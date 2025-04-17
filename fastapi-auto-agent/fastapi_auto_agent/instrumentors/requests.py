"""Requests library instrumentation."""

import wrapt
from opentelemetry import trace
from opentelemetry.trace import SpanKind
import logging
import time

logger = logging.getLogger(__name__)

def instrument_requests(module):
    """Instrument Requests library."""
    logger.debug("Instrumenting Requests library")
    
    # Patch the Session.request method
    if hasattr(module, 'Session'):
        original_request = module.Session.request
        
        @wrapt.wrap_function_wrapper(module.Session, 'request')
        def wrapped_request(wrapped, instance, args, kwargs):
            # Extract request information
            method = kwargs.get('method', args[0] if args else 'GET')
            url = kwargs.get('url', args[1] if len(args) > 1 else None)
            
            if not url:
                return wrapped(*args, **kwargs)
            
            # Create a span for this HTTP request
            tracer = trace.get_tracer("fastapi-auto-agent")
            
            with tracer.start_as_current_span(
                f"HTTP {method}",
                kind=SpanKind.CLIENT,
                attributes={
                    "http.method": method,
                    "http.url": url,
                    "http.target": url.split('://')[-1].split('/', 1)[-1] if '://' in url else url,
                    "http.host": url.split('://')[-1].split('/', 1)[0] if '://' in url else url.split('/', 1)[0],
                }
            ) as span:
                try:
                    # Record start time
                    start_time = time.time()
                    
                    # Make the request
                    response = wrapped(*args, **kwargs)
                    
                    # Record duration
                    duration = time.time() - start_time
                    span.set_attribute("http.duration_ms", duration * 1000)
                    
                    # Record response information
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute("http.response_content_length", 
                                      len(response.content) if hasattr(response, 'content') else 0)
                    
                    # Set span status based on response status code
                    if 200 <= response.status_code < 400:
                        span.set_status(trace.status.Status(trace.status.StatusCode.OK))
                    else:
                        span.set_status(trace.status.Status(
                            trace.status.StatusCode.ERROR, 
                            f"HTTP status code: {response.status_code}"
                        ))
                    
                    return response
                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    raise
        
        logger.debug("Patched Requests Session.request")
    
    return module
