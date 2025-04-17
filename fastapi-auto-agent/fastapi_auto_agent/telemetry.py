"""OpenTelemetry setup for the auto-instrumentation agent."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
import logging
import socket
import os
import sys

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
    otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)
    
    # Add the exporter to the tracer provider
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)
    
    logger.info("Telemetry setup complete")
    
    return tracer_provider
