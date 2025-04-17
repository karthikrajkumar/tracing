"""OpenTelemetry setup for the auto-instrumentation agent."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import logging
import os
import sys
import socket
import urllib.parse

logger = logging.getLogger(__name__)

def setup_telemetry(service_name="fastapi-application", jaeger_endpoint="http://localhost:4317"):
    """Set up the OpenTelemetry pipeline to export to Jaeger."""
    logger.info(f"Setting up telemetry for service: {service_name}")
    logger.info(f"Exporting traces to: {jaeger_endpoint}")
    
    # Create a resource with service information
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
    
    # Create an OTLP exporter pointing to Jaeger
    logger.info(f"Creating OTLP exporter with endpoint: {jaeger_endpoint}")
    
    # Check if Jaeger is accessible
    
    parsed_url = urllib.parse.urlparse(jaeger_endpoint)
    host = parsed_url.hostname
    port = parsed_url.port or 4317
    
    logger.info(f"Checking if Jaeger is accessible at {host}:{port}")
    
    try:
        # Try to connect to Jaeger
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((host, port))
        s.close()
        logger.info(f"Successfully connected to Jaeger at {host}:{port}")
        
        # Create the OTLP exporter
        # Try OTLP gRPC exporter
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)
            logger.info("OTLP gRPC exporter created successfully")
        except Exception as e:
            logger.error(f"Error creating OTLP gRPC exporter: {e}")
            # Fallback to console exporter
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            logger.info("Falling back to console exporter")
            otlp_exporter = ConsoleSpanExporter()
        
        # Also add a console exporter for debugging
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        console_exporter = ConsoleSpanExporter()
        
    except Exception as e:
        logger.error(f"Error connecting to Jaeger at {host}:{port}: {e}")
        logger.error("Make sure Jaeger is running and accessible")
        
        # Fallback to console exporter for debugging
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        logger.info("Falling back to console exporter")
        otlp_exporter = ConsoleSpanExporter()
        console_exporter = None
    
    # Add the exporters to the tracer provider
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Add console exporter if available
    if 'console_exporter' in locals() and console_exporter is not None:
        logger.info("Adding console exporter for debugging")
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    logger.info("Telemetry setup complete")
    
    return tracer_provider
