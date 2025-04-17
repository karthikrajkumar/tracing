#!/usr/bin/env python3
"""Command-line interface for the FastAPI auto-instrumentation agent."""

import sys
import os
import argparse
import logging
from fastapi_auto_agent.import_hook import install_import_hook
from fastapi_auto_agent.telemetry import setup_telemetry
from fastapi_auto_agent import __version__

def main():
    """CLI entry point for the agent"""
    parser = argparse.ArgumentParser(description="FastAPI Auto-Instrumentation Agent")
    parser.add_argument("--service-name", default="fastapi-application",
                        help="Name of the service (default: fastapi-application)")
    parser.add_argument("--jaeger-endpoint", default="http://localhost:4317",
                        help="Jaeger OTLP endpoint (default: http://localhost:4317)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    parser.add_argument("--version", action="store_true",
                        help="Show version information and exit")
    parser.add_argument("command", nargs=argparse.REMAINDER,
                        help="The command to run with instrumentation")
    
    args = parser.parse_args()
    
    # Show version and exit if requested
    if args.version:
        print(f"FastAPI Auto-Instrumentation Agent v{__version__}")
        sys.exit(0)
    
    if not args.command:
        parser.error("No command specified to run")
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("fastapi-auto-agent")
    
    logger.info(f"Starting FastAPI Auto-Instrumentation Agent v{__version__}")
    logger.info(f"Service name: {args.service_name}")
    logger.info(f"Jaeger endpoint: {args.jaeger_endpoint}")
    
    # Set up telemetry
    setup_telemetry(args.service_name, args.jaeger_endpoint)
    
    # Install import hooks
    install_import_hook()
    
    # Give some time for the import hooks to be fully set up
    import time
    time.sleep(1)
    
    logger.info(f"Running command: {' '.join(args.command)}")
    
    # Prepare the command
    cmd = args.command
    cmd_path = cmd[0]
    cmd_args = cmd[1:]
    
    # Update sys.argv for the command
    sys.argv = [cmd_path] + cmd_args
    
    # Execute the command
    try:
        # Check if the command exists
        if not os.path.exists(cmd_path) and cmd_path in ['python', 'python3']:
            # Try to find the Python executable
            python_path = None
            for path in ['python3', 'python']:
                try:
                    python_path = os.popen(f'which {path}').read().strip()
                    if python_path:
                        logger.info(f"Found Python executable: {python_path}")
                        break
                except:
                    pass
            
            if python_path:
                # Use the found Python executable
                import subprocess
                
                # Modify the environment to enable auto-instrumentation
                env = os.environ.copy()
                env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + ":" + env.get('PYTHONPATH', '')
                env['OTEL_SERVICE_NAME'] = args.service_name
                env['OTEL_EXPORTER_OTLP_ENDPOINT'] = args.jaeger_endpoint
                env['OTEL_PYTHON_AGENT_ENABLED'] = 'true'
                
                # Add a preload module that will instrument the application
                preload_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preload.py")
                
                # Create the preload script if it doesn't exist
                if not os.path.exists(preload_script):
                    with open(preload_script, 'w') as f:
                        f.write("""
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
        otlp_exporter = OTLPSpanExporter(endpoint=jaeger_endpoint, insecure=True)
        logger.info("OTLP exporter created successfully")
        
        # Also add a console exporter for debugging
        console_exporter = ConsoleSpanExporter()
        
        # Add the exporters to the tracer provider
        tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
        
    except Exception as e:
        logger.error(f"Error creating OTLP exporter: {e}")
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
""")
                
                # Execute the command with the preload script
                cmd = [python_path, "-c", f"import sys; sys.path.insert(0, '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}'); import fastapi_auto_agent.preload; import sys; sys.argv = ['{cmd_path}'] + {cmd_args}; import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000)"]
                logger.info(f"Executing: {' '.join(cmd)}")
                subprocess.run(cmd, env=env)
            else:
                logger.error("Could not find Python executable. Please make sure Python is installed and in your PATH.")
                sys.exit(1)
        else:
            # Execute the command as a script with preloading
            # Create a modified environment
            env = os.environ.copy()
            env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + ":" + env.get('PYTHONPATH', '')
            env['OTEL_SERVICE_NAME'] = args.service_name
            env['OTEL_EXPORTER_OTLP_ENDPOINT'] = args.jaeger_endpoint
            env['OTEL_PYTHON_AGENT_ENABLED'] = 'true'
            
            # Execute with the preload module
            import subprocess
            cmd = [sys.executable, "-c", f"import sys; sys.path.insert(0, '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}'); import fastapi_auto_agent.preload; import sys; sys.argv = ['{cmd_path}'] + {cmd_args}; import uvicorn; uvicorn.run('app.main:app', host='127.0.0.1', port=8000)"]
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.run(cmd, env=env)
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
