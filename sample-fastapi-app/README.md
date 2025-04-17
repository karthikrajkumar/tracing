# Sample FastAPI Application

This is a sample FastAPI application with no explicit OpenTelemetry instrumentation. It's designed to be used with the FastAPI Auto-Instrumentation Agent to demonstrate automatic tracing capabilities.

## Features

- RESTful API with FastAPI
- SQLite database with SQLAlchemy ORM
- User and Item resources with CRUD operations
- External API calls using the requests library
- Various endpoints to demonstrate different tracing scenarios:
  - Basic endpoints
  - Database operations
  - External API calls
  - Error simulation
  - Complex operations with nested spans
  - Background tasks

## Project Structure

```
sample-fastapi-app/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database models and connection
│   ├── schemas.py           # Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── users.py         # User endpoints
│   │   └── items.py         # Item endpoints
│   └── services/
│       ├── __init__.py
│       ├── user_service.py  # User business logic
│       ├── item_service.py  # Item business logic
│       └── external_service.py  # External API calls
└── requirements.txt
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd sample-fastapi-app
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

### Without Auto-Instrumentation

To run the application normally without auto-instrumentation:

```bash
cd app
uvicorn main:app --reload
```

The API will be available at http://localhost:8000.

### With Auto-Instrumentation (Dynatrace-like Approach)

This application can be run with the FastAPI Auto-Instrumentation Agent, which works similarly to Dynatrace's OneAgent by automatically instrumenting the application without requiring any code changes:

```bash
# Make sure Jaeger is running
# For example, using Docker:
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# Run the application with auto-instrumentation
fastapi-auto-agent --service-name sample-fastapi-app python3 -m uvicorn app.main:app

# For more detailed logging, add the --debug flag:
# fastapi-auto-agent --debug --service-name sample-fastapi-app python3 -m uvicorn app.main:app
```

The agent works by:

1. Preloading instrumentation code before your application starts
2. Monkey patching key libraries (FastAPI, SQLAlchemy, requests) to add tracing
3. Automatically instrumenting your FastAPI application when it's created
4. Sending traces to Jaeger without any code changes to your application

This is similar to how Dynatrace's OneAgent works, where you install the agent on your server and it automatically instruments your applications without requiring any code changes.

The API will be available at http://localhost:8000, and traces will be sent to Jaeger.

## API Endpoints

### Basic Endpoints

- `GET /`: Welcome message
- `GET /hello`: Simple hello endpoint
- `GET /health`: Health check endpoint
- `GET /slow-operation`: Endpoint that simulates a slow operation
- `GET /error-simulation`: Endpoint that simulates errors with a configurable probability
- `GET /complex-operation`: Endpoint that performs multiple operations (database, external API, CPU-intensive)
- `GET /nested-operations`: Endpoint that performs nested operations to generate a complex trace
- `GET /background-task`: Endpoint that triggers a background task

### User Endpoints

- `POST /users/`: Create a new user
- `GET /users/{user_id}`: Get a specific user
- `GET /users/`: Get all users
- `PUT /users/{user_id}`: Update a user
- `DELETE /users/{user_id}`: Delete a user
- `GET /users/{user_id}/external-data`: Get external data for a user

### Item Endpoints

- `POST /users/{user_id}/items`: Create a new item for a user
- `GET /items/{item_id}`: Get a specific item
- `GET /items/`: Get all items
- `GET /users/{user_id}/items`: Get all items for a user
- `PUT /items/{item_id}`: Update an item
- `DELETE /items/{item_id}`: Delete an item
- `PUT /items/{item_id}/complete`: Mark an item as completed

### Weather Endpoint

- `GET /weather/{city}`: Get weather data for a city

## Viewing Traces

After running the application with auto-instrumentation, you can view the traces in Jaeger UI:

1. Open your browser and navigate to http://localhost:16686
2. Select "sample-fastapi-app" from the Service dropdown
3. Click "Find Traces" to see the traces
4. Click on a trace to see the detailed span information

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
