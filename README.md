# Auto-Instrumentation for FastAPI Applications (Dynatrace-like Approach)

This project demonstrates how to automatically add OpenTelemetry instrumentation to FastAPI applications without requiring any code changes, similar to how Dynatrace works. It consists of two main components:

1. **FastAPI Auto-Instrumentation Agent**: A Python agent that automatically instruments FastAPI applications at runtime using monkey patching and preloading techniques, similar to how Dynatrace's OneAgent works.
2. **Sample FastAPI Application**: A clean FastAPI application with no explicit OpenTelemetry instrumentation, used to demonstrate the agent's capabilities.

## Project Structure

```
.
├── fastapi-auto-agent/         # Auto-instrumentation agent
│   ├── fastapi_auto_agent/     # Agent source code
│   ├── README.md               # Agent documentation
│   └── setup.py                # Agent package setup
├── sample-fastapi-app/         # Sample FastAPI application
│   ├── app/                    # Application source code
│   ├── README.md               # Application documentation
│   └── requirements.txt        # Application dependencies
└── setup_and_run.sh            # Script to set up and run both components
```

## Quick Start

The easiest way to get started is to use the provided setup script:

```bash
# Make the script executable
chmod +x setup_and_run.sh

# Run the setup script
./setup_and_run.sh
```

This script will:
1. Create a virtual environment
2. Install the auto-instrumentation agent
3. Install the sample application dependencies
4. Start Jaeger (if Docker is available)
5. Run the sample application with auto-instrumentation

Once running:
- The sample application will be available at http://localhost:8000
- The Jaeger UI will be available at http://localhost:16686

## Manual Setup

If you prefer to set up the components manually:

### 1. Install the Auto-Instrumentation Agent

```bash
# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the agent
cd fastapi-auto-agent
pip install -e .
cd ..
```

### 2. Install the Sample Application Dependencies

```bash
cd sample-fastapi-app
pip install -r requirements.txt
cd ..
```

### 3. Start Jaeger

```bash
# Using Docker
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

### 4. Run the Sample Application with Auto-Instrumentation

```bash
cd sample-fastapi-app
fastapi-auto-agent --service-name sample-fastapi-app python3 -m uvicorn app.main:app --reload
```

## How It Works

The auto-instrumentation agent uses Python's import hooks to intercept module imports and inject OpenTelemetry instrumentation code at runtime. When a FastAPI application is started with the agent:

1. The agent sets up the OpenTelemetry SDK and configures exporters
2. It installs import hooks to intercept module loading
3. When FastAPI, SQLAlchemy, or requests modules are imported, it injects instrumentation code
4. It adds middleware to the FastAPI application to trace HTTP requests
5. It patches database and HTTP client operations to add spans

All of this happens without requiring any code changes to the application itself.

## Testing the Application

You can use the Swagger UI to test the API endpoints:

1. Open your browser and navigate to http://localhost:8000/docs
2. Use the Swagger UI to send requests to the API endpoints

Or you can use curl to send requests:

```bash
# Create a user
curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{"username":"testuser","email":"test@example.com","password":"password123"}'

# Get all users
curl -X GET "http://localhost:8000/users/"

# Create an item for a user
curl -X POST "http://localhost:8000/users/1/items" -H "Content-Type: application/json" -d '{"title":"Test Item","description":"This is a test item","priority":3}'

# Get all items for a user
curl -X GET "http://localhost:8000/users/1/items"

# Get weather data
curl -X GET "http://localhost:8000/weather/London"

# Trigger a complex operation
curl -X GET "http://localhost:8000/complex-operation"
```

## Viewing Traces

After running the application with auto-instrumentation, you can view the traces in Jaeger UI:

1. Open your browser and navigate to http://localhost:16686
2. Select "sample-fastapi-app" from the Service dropdown
3. Click "Find Traces" to see the traces
4. Click on a trace to see the detailed span information

## Troubleshooting

### No Traces in Jaeger

If you don't see any traces in Jaeger, try the following:

1. **Check if Jaeger is running**: Open http://localhost:16686 in your browser to see if Jaeger UI is accessible.

2. **Verify the Jaeger endpoint**: Make sure the Jaeger endpoint is correct. The default is http://localhost:4317.

3. **Run with debug logging**: Add the `--debug` flag to see more detailed logs:
   ```bash
   fastapi-auto-agent --debug --service-name sample-fastapi-app python3 -m uvicorn app.main:app --reload
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
   
   fastapi-auto-agent --jaeger-endpoint http://localhost:14317 --service-name sample-fastapi-app python3 -m uvicorn app.main:app --reload
   ```

6. **Check Docker logs**: If using Docker for Jaeger, check the logs for any errors:
   ```bash
   docker logs jaeger
   ```

7. **Check console output**: The agent now includes a console exporter that will print traces to the console when running with the `--debug` flag. Look for trace output in the console to verify that traces are being generated.

8. **Check the OTLP exporter**: The agent uses the OTLP gRPC exporter to send traces to Jaeger. Make sure the appropriate port is open in your Jaeger container:
   ```bash
   docker run -d --name jaeger \
     -e COLLECTOR_OTLP_ENABLED=true \
     -p 16686:16686 \
     -p 4317:4317 \
     jaegertracing/all-in-one:latest
   ```

9. **Try a different collector**: If you're still having issues with Jaeger, you can try using Zipkin instead:
   ```bash
   docker run -d -p 9411:9411 openzipkin/zipkin
   
   # Then install the Zipkin exporter
   pip install opentelemetry-exporter-zipkin
   ```
   
   Then modify the `telemetry.py` file to use the Zipkin exporter instead of the OTLP exporter.

10. **Check if traces are being generated**: The console output should show spans being created. If you see spans in the console but not in Jaeger, the issue is likely with the connection to Jaeger, not with the instrumentation itself.

## Next Steps

This project demonstrates the basic capabilities of auto-instrumentation. Here are some ideas for extending it:

1. Add support for more libraries and frameworks
2. Add support for metrics and logs in addition to traces
3. Add support for other exporters (e.g., Zipkin, Prometheus)
4. Add support for sampling and filtering
5. Add a web UI for configuring the agent
6. Add support for Azure Functions or other serverless environments

## License

This project is licensed under the MIT License.
