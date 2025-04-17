# FastAPI Auto-Instrumentation Agent (Dynatrace-like Approach)

A Python agent that automatically adds OpenTelemetry instrumentation to FastAPI applications without requiring any code changes, similar to how Dynatrace's OneAgent works.

## Features

- **Zero-Code Instrumentation**: Add tracing to FastAPI applications without modifying their code
- **Automatic Middleware**: Adds HTTP request tracing middleware automatically
- **Database Tracing**: Traces SQLAlchemy database operations
- **External API Tracing**: Traces HTTP requests made with the requests library
- **Jaeger Integration**: Sends traces to Jaeger for visualization
- **Low Overhead**: Minimal performance impact on the instrumented application

## How It Works

The agent uses Python's import hooks to intercept module imports and inject instrumentation code at runtime. When a FastAPI application is started with the agent, it:

1. Sets up the OpenTelemetry SDK and configures exporters
2. Installs import hooks to intercept module loading
3. When FastAPI, SQLAlchemy, or requests modules are imported, it injects instrumentation code
4. Adds middleware to the FastAPI application to trace HTTP requests
5. Patches database and HTTP client operations to add spans

## Installation

### From Source

1. Clone the repository:

```bash
git clone <repository-url>
cd fastapi-auto-agent
```

2. Install the package in development mode:

```bash
pip install -e .
```

## Usage

### Running a FastAPI Application with Auto-Instrumentation

```bash
# Make sure Jaeger is running
# For example, using Docker:
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# Run your FastAPI application with the agent
fastapi-auto-agent --service-name your-service-name python3 -m uvicorn your_app:app --reload
```

### Command-Line Options

- `--service-name`: Name of the service (default: fastapi-application)
- `--jaeger-endpoint`: Jaeger OTLP endpoint (default: http://localhost:4317)
- `--debug`: Enable debug logging
- `--version`: Show version information and exit

## Viewing Traces

After running your application with the agent, you can view the traces in Jaeger UI:

1. Open your browser and navigate to http://localhost:16686
2. Select your service from the Service dropdown
3. Click "Find Traces" to see the traces
4. Click on a trace to see the detailed span information

## Supported Libraries

The agent currently supports instrumenting:

- **FastAPI**: HTTP request handling
- **Starlette**: ASGI middleware (used by FastAPI)
- **SQLAlchemy**: Database operations
- **Requests**: HTTP client operations

## Example

See the [sample-fastapi-app](../sample-fastapi-app) directory for an example FastAPI application that can be used with this agent.

## Extending the Agent

### Adding Support for New Libraries

To add support for a new library, create a new instrumentor in the `fastapi_auto_agent/instrumentors` directory and update the `import_hook.py` file to use it.

For example, to add support for a new database driver:

1. Create `fastapi_auto_agent/instrumentors/new_driver.py`
2. Implement the instrumentation logic
3. Update `import_hook.py` to intercept the new module and apply the instrumentation

### Customizing Span Attributes

You can customize the attributes added to spans by modifying the instrumentor files. For example, to add more attributes to HTTP request spans, modify the `middleware.py` file.

## Limitations

- The agent only works with Python applications
- It may not work with all FastAPI configurations or extensions
- It doesn't support all database drivers or HTTP client libraries
- It may not capture all spans that manual instrumentation would

## Troubleshooting

### No Traces in Jaeger

If you don't see any traces in Jaeger, try the following:

1. **Check if Jaeger is running**: Open http://localhost:16686 in your browser to see if Jaeger UI is accessible.

2. **Verify the Jaeger endpoint**: Make sure the Jaeger endpoint is correct. The default is http://localhost:4317.

3. **Run with debug logging**: Add the `--debug` flag to see more detailed logs:
   ```bash
   fastapi-auto-agent --debug --service-name your-service-name python3 -m uvicorn your_app:app --reload
   ```

4. **Check module loading**: Look for log messages about intercepting and instrumenting modules. If you don't see these messages, the instrumentation might not be applied.

5. **Try a different port**: If port 4317 is already in use, try a different port:
   ```bash
   docker run -d --name jaeger \
     -e COLLECTOR_OTLP_ENABLED=true \
     -p 16686:16686 \
     -p 14317:4317 \
     -p 14318:4318 \
     jaegertracing/all-in-one:latest
   
   fastapi-auto-agent --jaeger-endpoint http://localhost:14317 --service-name your-service-name python3 -m uvicorn your_app:app --reload
   ```

6. **Check Docker logs**: If using Docker for Jaeger, check the logs for any errors:
   ```bash
   docker logs jaeger
   ```

7. **Check if the application is importing the right modules**: The agent only instruments specific modules. Make sure your application is importing FastAPI, SQLAlchemy, and/or requests.

### Application Errors

- If the application crashes or behaves unexpectedly, try running it without the agent to see if the issue persists
- Check the logs for any errors related to the agent
- Try updating the agent to the latest version

## License

This project is licensed under the MIT License - see the LICENSE file for details.
