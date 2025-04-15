from fastapi import FastAPI, Request, Response, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import make_asgi_app
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from app.metrics import (
    REQUEST_TIME, DB_OPERATION_TIME, API_OPERATION_TIME, 
    ERROR_COUNTER, REQUEST_COUNTER, REQUEST_LATENCY, CONCURRENT_REQUESTS
)
import time
import random
import requests
import asyncio
from typing import Dict, List, Optional

app = FastAPI()

# Middleware to track concurrent requests and record request metrics
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Increment the concurrent requests gauge
        CONCURRENT_REQUESTS.inc()
        
        # Record request method and endpoint
        method = request.method
        endpoint = request.url.path
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Record metrics on success
            status = response.status_code
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint, status=status).inc()
            
            # Record latency
            duration = time.time() - start_time
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)
            
            return response
        except Exception as e:
            # Record metrics on error
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint, status=500).inc()
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise
        finally:
            # Decrement the concurrent requests gauge
            CONCURRENT_REQUESTS.dec()

# Add the metrics middleware
app.add_middleware(MetricsMiddleware)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Set up OpenTelemetry tracing
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="localhost:4317", insecure=True)
    )
)
FastAPIInstrumentor().instrument_app(app)

# Get a tracer instance
tracer = trace.get_tracer(__name__)

# Original endpoint
@app.get("/hello")
@REQUEST_TIME.time()
def hello():
    time.sleep(0.5)
    return {"message": "Hello from APM-monitored FastAPI!"}

# Database simulation endpoint with custom spans
@app.get("/db-operation")
@DB_OPERATION_TIME.time()
def db_operation():
    # Create parent span for the entire operation
    with tracer.start_as_current_span("database-operation") as parent_span:
        # Add custom attributes
        parent_span.set_attribute("operation.type", "database")
        parent_span.set_attribute("database.name", "example_db")
        parent_span.set_attribute("database.system", "postgresql")
        
        # Simulate connection
        with tracer.start_as_current_span("db-connection") as conn_span:
            conn_span.set_attribute("connection.id", f"conn-{random.randint(1000, 9999)}")
            time.sleep(0.05)
        
        # Simulate query planning
        with tracer.start_as_current_span("query-planning") as planning_span:
            planning_span.set_attribute("query.complexity", "medium")
            planning_span.set_attribute("query.type", "SELECT")
            time.sleep(0.1)
        
        # Simulate query execution
        with tracer.start_as_current_span("query-execution") as execution_span:
            execution_span.set_attribute("query.rows", 100)
            execution_span.set_attribute("query.table", "users")
            time.sleep(0.3)
            
            # Nested operation - data processing
            with tracer.start_as_current_span("data-processing") as processing_span:
                processing_span.set_attribute("processing.records", 100)
                time.sleep(0.15)
            
    return {"result": "Database operation completed", "rows": 100}

# External API call simulation
@app.get("/external-api")
@API_OPERATION_TIME.time()
def external_api():
    with tracer.start_as_current_span("external-api-call") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.url", "https://jsonplaceholder.typicode.com/todos/1")
        
        try:
            # Simulate API call
            span.add_event("Starting API request")
            time.sleep(0.2)  # Simulate network latency
            
            # Make actual HTTP request (or simulate it)
            with tracer.start_as_current_span("http-request") as request_span:
                request_span.set_attribute("http.request_content_length", 0)
                
                # Uncomment to make a real HTTP request
                # response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
                # status_code = response.status_code
                # response_data = response.json()
                
                # For simulation, we'll just create mock data
                time.sleep(0.3)
                status_code = 200
                response_data = {"userId": 1, "id": 1, "title": "Sample todo", "completed": False}
                
                request_span.set_attribute("http.status_code", status_code)
                request_span.set_attribute("http.response_content_length", len(str(response_data)))
            
            span.add_event("API request completed", {"status_code": status_code})
            return {"status": "success", "data": response_data}
            
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            return {"status": "error", "message": str(e)}

# Error simulation endpoint
@app.get("/error-simulation")
def error_simulation(error_probability: float = 0.5):
    with tracer.start_as_current_span("error-prone-operation") as span:
        span.set_attribute("error.probability", error_probability)
        
        try:
            # Simulate an error based on probability
            if random.random() < error_probability:
                span.add_event("Triggering simulated error")
                raise ValueError("Simulated error occurred")
                
            span.add_event("Operation completed successfully")
            return {"result": "Operation completed successfully"}
            
        except Exception as e:
            # Record exception in the span
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            
            # Increment error counter
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            
            # Return error response
            return {"error": str(e), "type": type(e).__name__}

# Complex operation with multiple nested spans
@app.get("/complex-operation")
def complex_operation():
    with tracer.start_as_current_span("complex-operation") as parent_span:
        parent_span.set_attribute("operation.complexity", "high")
        parent_span.set_attribute("operation.id", f"op-{random.randint(10000, 99999)}")
        
        # Step 1: Data preparation
        with tracer.start_as_current_span("data-preparation") as prep_span:
            prep_span.set_attribute("data.size", "medium")
            time.sleep(0.15)
            
            # Sub-step: Data validation
            with tracer.start_as_current_span("data-validation") as validation_span:
                validation_span.set_attribute("validation.rules", 5)
                time.sleep(0.1)
        
        # Step 2: Processing
        with tracer.start_as_current_span("data-processing") as processing_span:
            processing_span.set_attribute("processing.batch_size", 50)
            
            # Sub-step 1: First processing phase
            with tracer.start_as_current_span("processing-phase-1") as phase1_span:
                phase1_span.set_attribute("phase", 1)
                time.sleep(0.2)
            
            # Sub-step 2: Second processing phase
            with tracer.start_as_current_span("processing-phase-2") as phase2_span:
                phase2_span.set_attribute("phase", 2)
                time.sleep(0.25)
                
                # Nested operation in phase 2
                with tracer.start_as_current_span("specialized-calculation") as calc_span:
                    calc_span.set_attribute("calculation.type", "matrix")
                    time.sleep(0.15)
        
        # Step 3: Result compilation
        with tracer.start_as_current_span("result-compilation") as result_span:
            result_span.set_attribute("results.count", 3)
            time.sleep(0.1)
        
        return {
            "status": "completed",
            "steps_executed": 3,
            "processing_time": "~1 second",
            "result": "Complex operation finished successfully"
        }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}
