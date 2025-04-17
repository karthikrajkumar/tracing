"""Module import hooks for auto-instrumentation."""

import sys
from importlib.abc import MetaPathFinder
from importlib.machinery import PathFinder, SourceFileLoader
import logging

logger = logging.getLogger(__name__)

class InstrumentationLoader(SourceFileLoader):
    """Custom loader that applies instrumentation after module loading."""
    
    def exec_module(self, module):
        # Call the original loader
        super().exec_module(module)
        
        # Apply instrumentation after module is loaded
        module_name = module.__name__
        logger.info(f"Loaded module: {module_name}")
        
        try:
            if module_name == "fastapi.applications":
                from fastapi_auto_agent.instrumentors.fastapi import instrument_fastapi
                instrument_fastapi(module)
                logger.info(f"Instrumented FastAPI module")
            elif module_name == "starlette.applications":
                from fastapi_auto_agent.instrumentors.starlette import instrument_starlette
                instrument_starlette(module)
                logger.info(f"Instrumented Starlette module")
            elif module_name == "sqlalchemy.engine.base":
                from fastapi_auto_agent.instrumentors.sqlalchemy import instrument_sqlalchemy
                instrument_sqlalchemy(module)
                logger.info(f"Instrumented SQLAlchemy module")
            elif module_name == "requests.sessions":
                from fastapi_auto_agent.instrumentors.requests import instrument_requests
                instrument_requests(module)
                logger.info(f"Instrumented Requests module")
        except Exception as e:
            logger.error(f"Error instrumenting {module_name}: {e}")
        
        return module

class InstrumentationFinder(MetaPathFinder):
    """Custom meta path finder that intercepts module imports."""
    
    def find_spec(self, fullname, path, target=None):
        # Use the standard PathFinder to find the module
        spec = PathFinder.find_spec(fullname, path, target)
        if spec is None or spec.loader is None:
            return spec
            
        # Replace the loader with our custom loader for specific modules
        modules_to_instrument = [
            "fastapi.applications",
            "starlette.applications",
            "sqlalchemy.engine.base",
            "requests.sessions"
        ]
        
        if fullname in modules_to_instrument:
            logger.info(f"Intercepting module: {fullname}")
            spec.loader = InstrumentationLoader(spec.loader.name, spec.loader.path)
            
        return spec

def install_import_hook():
    """Install the import hook into sys.meta_path."""
    logger.info("Installing import hooks")
    sys.meta_path.insert(0, InstrumentationFinder())
    
    # Also try to instrument already imported modules
    logger.info("Checking for already imported modules to instrument")
    modules_to_instrument = {
        "fastapi.applications": "fastapi_auto_agent.instrumentors.fastapi",
        "starlette.applications": "fastapi_auto_agent.instrumentors.starlette",
        "sqlalchemy.engine.base": "fastapi_auto_agent.instrumentors.sqlalchemy",
        "requests.sessions": "fastapi_auto_agent.instrumentors.requests"
    }
    
    for module_name, instrumentor_path in modules_to_instrument.items():
        if module_name in sys.modules:
            logger.info(f"Found already imported module: {module_name}")
            try:
                module = sys.modules[module_name]
                instrumentor = __import__(instrumentor_path, fromlist=['instrument_' + module_name.split('.')[-1]])
                instrument_func = getattr(instrumentor, 'instrument_' + module_name.split('.')[-1])
                instrument_func(module)
                logger.info(f"Instrumented already imported module: {module_name}")
            except Exception as e:
                logger.error(f"Error instrumenting already imported module {module_name}: {e}")
