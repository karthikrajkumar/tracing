# Auto-generated preload script for FastAPI Auto-Instrumentation Agent
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("fastapi-auto-agent-preload")

logger.info("Preload script executed")

# Import OpenTelemetry
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.resource import ResourceAttributes
    
    # Import instrumentation
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    
    # Set up telemetry
    service_name = os.environ.get('OTEL_SERVICE_NAME', 'fastapi-application')
    jaeger_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4317')
    
    logger.info(f"Setting up telemetry for service: {service_name}")
    logger.info(f"Exporting traces to: {jaeger_endpoint}")
    
    # Create a resource with service information
    import socket
    hostname = socket.gethostname()
    pid = os.getpid()
    
    resource = Resource.create({
        ResourceAttributes.SERVICE_NAME: service_name,
        ResourceAttributes.SERVICE_VERSION: "1.0.0",
        ResourceAttributes.HOST_NAME: hostname,
        ResourceAttributes.PROCESS_PID: pid,
        ResourceAttributes.PROCESS_RUNTIME_NAME: "python",
        ResourceAttributes.PROCESS_RUNTIME_VERSION: ".".join(map(str, sys.version_info[:3])),
    })
    
    # Create a tracer provider
    tracer_provider = TracerProvider(resource=resource)
    
    # Create exporters
    try:
        # Check if Jaeger is accessible
        import socket
        import urllib.parse
        
        parsed_url = urllib.parse.urlparse(jaeger_endpoint)
        host = parsed_url.hostname
        port = parsed_url.port or 4317
        
        logger.info(f"Checking if Jaeger is accessible at {host}:{port}")
        
        # Try to connect to Jaeger
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, port))
        s.close()
        logger.info(f"Successfully connected to Jaeger at {host}:{port}")
        
        # Create the OTLP exporter
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)
            logger.info("OTLP gRPC exporter created successfully")
        except Exception as e:
            logger.error(f"Error creating OTLP gRPC exporter: {e}")
            # Fallback to console exporter
            logger.info("Falling back to console exporter")
            otlp_exporter = ConsoleSpanExporter()
        
        # Also add a console exporter for debugging
        console_exporter = ConsoleSpanExporter()
        
        # Add the exporters to the tracer provider
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        
    except Exception as e:
        logger.error(f"Error setting up exporters: {e}")
        # Fallback to console exporter for debugging
        console_exporter = ConsoleSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    # Auto-instrument libraries
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    
    # Monkey patch FastAPI to auto-instrument
    import fastapi.applications
    original_init = fastapi.applications.FastAPI.__init__
    
    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        FastAPIInstrumentor.instrument_app(self)
        logger.info(f"FastAPI application auto-instrumented: {self}")
    
    fastapi.applications.FastAPI.__init__ = patched_init
    
    logger.info("Telemetry setup complete")
    
except Exception as e:
    logger.error(f"Error in preload script: {e}")
