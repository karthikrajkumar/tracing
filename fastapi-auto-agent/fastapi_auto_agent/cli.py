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
    
    logger.info(f"Running command: {' '.join(args.command)}")
    
    # Prepare the command
    cmd = args.command
    cmd_path = cmd[0]
    cmd_args = cmd[1:]
    
    # Update sys.argv for the command
    sys.argv = [cmd_path] + cmd_args
    
    # Execute the command
    try:
        with open(cmd_path, 'rb') as script:
            code = compile(script.read(), cmd_path, 'exec')
            exec(code, {'__name__': '__main__', '__file__': cmd_path})
    except FileNotFoundError:
        logger.error(f"Command not found: {cmd_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
