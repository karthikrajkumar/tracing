"""FastAPI instrumentation."""

import wrapt
from opentelemetry import trace
import logging

logger = logging.getLogger(__name__)

def instrument_fastapi(module):
    """Instrument FastAPI application class."""
    logger.debug("Instrumenting FastAPI")
    
    original_init = module.FastAPI.__init__
    
    @wrapt.wrap_function_wrapper(module.FastAPI, '__init__')
    def wrapped_init(wrapped, instance, args, kwargs):
        # Call original __init__
        result = wrapped(*args, **kwargs)
        
        logger.debug("FastAPI application initialized, adding instrumentation")
        
        # Add middleware for request tracking
        from fastapi_auto_agent.middleware import telemetry_middleware
        instance.middleware("http")(telemetry_middleware)
        
        # Patch the routing mechanism
        _patch_routing(instance)
        
        return result
    
    return module

def _patch_routing(app):
    """Patch the FastAPI routing to trace all endpoint calls."""
    # Get original add_route method
    original_add_route = app.router.add_route
    
    # Create a tracer
    tracer = trace.get_tracer("fastapi-auto-agent")
    
    def wrapped_add_route(route, endpoint, **kwargs):
        # Get the original endpoint
        original_endpoint = endpoint
        
        # Create a wrapped endpoint with tracing
        @wrapt.wraps(original_endpoint)
        async def traced_endpoint(*args, **kwargs):
            request = kwargs.get('request')
            route_name = f"{request.method} {route}" if request else route
            
            with tracer.start_as_current_span(route_name) as span:
                if request:
                    # Add attributes to the span
                    span.set_attribute("http.route", route)
                    span.set_attribute("http.method", request.method)
                
                # Call the original endpoint
                return await original_endpoint(*args, **kwargs)
        
        # Call the original add_route with our traced endpoint
        return original_add_route(route, traced_endpoint, **kwargs)
    
    # Replace the add_route method
    app.router.add_route = wrapped_add_route
    logger.debug("Patched FastAPI routing")
