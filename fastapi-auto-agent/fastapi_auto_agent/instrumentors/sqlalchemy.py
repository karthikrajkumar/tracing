"""SQLAlchemy instrumentation."""

import wrapt
from opentelemetry import trace
from opentelemetry.trace import SpanKind
import logging
import time

logger = logging.getLogger(__name__)

def instrument_sqlalchemy(module):
    """Instrument SQLAlchemy engine."""
    logger.debug("Instrumenting SQLAlchemy")
    
    # Patch the execute method of Connection
    if hasattr(module, 'Connection'):
        original_execute = module.Connection.execute
        
        @wrapt.wrap_function_wrapper(module.Connection, 'execute')
        def wrapped_execute(wrapped, instance, args, kwargs):
            # Get the SQL statement
            statement = args[0] if args else kwargs.get('statement')
            if statement is None:
                return wrapped(*args, **kwargs)
            
            # Get statement text
            statement_text = str(statement)
            
            # Create a span for this database operation
            tracer = trace.get_tracer("fastapi-auto-agent")
            
            with tracer.start_as_current_span(
                "sqlalchemy.execute",
                kind=SpanKind.CLIENT,
                attributes={
                    "db.system": "sqlite" if "sqlite" in str(instance.engine.url) else "unknown",
                    "db.statement": statement_text[:1000],  # Truncate long statements
                    "db.operation": statement_text.split()[0].upper() if statement_text else "UNKNOWN",
                }
            ) as span:
                try:
                    # Record start time
                    start_time = time.time()
                    
                    # Execute the query
                    result = wrapped(*args, **kwargs)
                    
                    # Record duration
                    duration = time.time() - start_time
                    span.set_attribute("db.execution_time_ms", duration * 1000)
                    
                    # Record row count if available
                    if hasattr(result, 'rowcount'):
                        span.set_attribute("db.result.rows", result.rowcount)
                    
                    return result
                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    raise
        
        logger.debug("Patched SQLAlchemy Connection.execute")
    
    return module
