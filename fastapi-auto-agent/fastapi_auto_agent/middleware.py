"""HTTP middleware for request tracing."""

from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.trace.status import Status, StatusCode
import time
import logging

logger = logging.getLogger(__name__)

async def telemetry_middleware(request, call_next):
    """Middleware to trace HTTP requests."""
    tracer = trace.get_tracer("fastapi-auto-agent")
    
    # Start timing
    start_time = time.time()
    
    # Extract path for span name
    path = request.url.path
    method = request.method
    span_name = f"{method} {path}"
    
    logger.debug(f"Processing request: {span_name}")
    
    # Create a span for this request
    with tracer.start_as_current_span(
        span_name,
        kind=SpanKind.SERVER,
        attributes={
            "http.method": method,
            "http.url": str(request.url),
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "http.target": path,
            "http.user_agent": request.headers.get("user-agent", ""),
            "http.request_content_length": request.headers.get("content-length", 0),
        }
    ) as span:
        try:
            # Process the request
            response = await call_next(request)
            
            # Add response attributes
            status_code = response.status_code
            span.set_attribute("http.status_code", status_code)
            span.set_attribute("http.response_content_length", 
                              response.headers.get("content-length", 0))
            
            # Set span status based on response status code
            if 200 <= status_code < 400:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR, f"HTTP status code: {status_code}"))
            
            return response
        except Exception as e:
            # Record exception
            logger.exception(f"Error processing request: {span_name}")
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        finally:
            # Record duration
            duration = time.time() - start_time
            span.set_attribute("http.duration_ms", duration * 1000)
            logger.debug(f"Request completed: {span_name} in {duration:.3f}s")
