"""Starlette instrumentation."""

import wrapt
from opentelemetry import trace
import logging

logger = logging.getLogger(__name__)

def instrument_starlette(module):
    """Instrument Starlette application class."""
    logger.debug("Instrumenting Starlette")
    
    original_init = module.Starlette.__init__
    
    @wrapt.wrap_function_wrapper(module.Starlette, '__init__')
    def wrapped_init(wrapped, instance, args, kwargs):
        # Call original __init__
        result = wrapped(*args, **kwargs)
        
        logger.debug("Starlette application initialized, adding instrumentation")
        
        # Add middleware for request tracking
        from fastapi_auto_agent.middleware import telemetry_middleware
        
        # Check if middleware is already in the list
        middleware_already_added = False
        for middleware in instance.user_middleware:
            if getattr(middleware, "dispatch", None) == telemetry_middleware:
                middleware_already_added = True
                break
        
        if not middleware_already_added:
            instance.add_middleware(telemetry_middleware)
        
        return result
    
    return module
