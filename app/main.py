from fastapi import FastAPI, Request, Response, HTTPException, Depends, BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import make_asgi_app
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from app.metrics import (
    REQUEST_TIME, DB_OPERATION_TIME, API_OPERATION_TIME, 
    ERROR_COUNTER, REQUEST_COUNTER, REQUEST_LATENCY, CONCURRENT_REQUESTS
)
from app.database import get_db, init_db
from app.repositories import UserRepository, TodoRepository
from app.services import UserService, TodoService, ExternalApiService
from app.schemas import (
    UserCreate, UserUpdate, User, 
    TodoCreate, TodoUpdate, Todo, 
    WeatherResponse, ErrorResponse
)
import time
import random
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

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

# Instrument FastAPI
FastAPIInstrumentor().instrument_app(app)

# Instrument requests library
RequestsInstrumentor().instrument()

# Get a tracer instance
tracer = trace.get_tracer(__name__)

# Startup event to initialize the database
@app.on_event("startup")
def startup_event():
    init_db()

# Dependency to get user service
def get_user_service(db: Session = Depends(get_db)):
    return UserService(UserRepository(db))

# Dependency to get todo service
def get_todo_service(db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    todo_repo = TodoRepository(db)
    return TodoService(todo_repo, user_repo)

# Dependency to get external API service
def get_external_api_service():
    return ExternalApiService()

# Original hello endpoint
@app.get("/hello")
@REQUEST_TIME.time()
def hello():
    time.sleep(0.5)
    return {"message": "Hello from APM-monitored FastAPI!"}

# User endpoints
@app.post("/users", response_model=User, status_code=201)
def create_user(
    user: UserCreate, 
    user_service: UserService = Depends(get_user_service)
):
    with tracer.start_as_current_span("api.create_user") as span:
        span.set_attribute("api.operation", "create_user")
        
        try:
            result = user_service.create_user(
                username=user.username,
                email=user.email,
                password=user.password
            )
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/users/{user_id}", response_model=User)
def get_user(
    user_id: int, 
    user_service: UserService = Depends(get_user_service)
):
    with tracer.start_as_current_span("api.get_user") as span:
        span.set_attribute("api.operation", "get_user")
        span.set_attribute("user.id", user_id)
        
        try:
            user = user_service.get_user(user_id)
            if not user:
                span.set_attribute("result.found", False)
                raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
            span.set_attribute("result.found", True)
            return user
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/users", response_model=List[User])
def get_users(
    skip: int = 0, 
    limit: int = 100, 
    user_service: UserService = Depends(get_user_service)
):
    with tracer.start_as_current_span("api.get_users") as span:
        span.set_attribute("api.operation", "get_users")
        span.set_attribute("query.skip", skip)
        span.set_attribute("query.limit", limit)
        
        try:
            users = user_service.get_users(skip, limit)
            span.set_attribute("result.count", len(users))
            return users
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}", response_model=User)
def update_user(
    user_id: int, 
    user: UserUpdate, 
    user_service: UserService = Depends(get_user_service)
):
    with tracer.start_as_current_span("api.update_user") as span:
        span.set_attribute("api.operation", "update_user")
        span.set_attribute("user.id", user_id)
        
        try:
            user_data = user.dict(exclude_unset=True)
            updated_user = user_service.update_user(user_id, user_data)
            
            if not updated_user:
                span.set_attribute("result.found", False)
                raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
            span.set_attribute("result.found", True)
            return updated_user
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int, 
    user_service: UserService = Depends(get_user_service)
):
    with tracer.start_as_current_span("api.delete_user") as span:
        span.set_attribute("api.operation", "delete_user")
        span.set_attribute("user.id", user_id)
        
        try:
            result = user_service.delete_user(user_id)
            
            if not result:
                span.set_attribute("result.found", False)
                raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")
            
            span.set_attribute("result.found", True)
            return None
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

# Todo endpoints
@app.post("/users/{user_id}/todos", response_model=Todo, status_code=201)
def create_todo(
    user_id: int, 
    todo: TodoCreate, 
    todo_service: TodoService = Depends(get_todo_service)
):
    with tracer.start_as_current_span("api.create_todo") as span:
        span.set_attribute("api.operation", "create_todo")
        span.set_attribute("user.id", user_id)
        
        try:
            result = todo_service.create_todo(
                user_id=user_id,
                title=todo.title,
                description=todo.description,
                priority=todo.priority
            )
            return result
        except ValueError as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(
    todo_id: int, 
    todo_service: TodoService = Depends(get_todo_service)
):
    with tracer.start_as_current_span("api.get_todo") as span:
        span.set_attribute("api.operation", "get_todo")
        span.set_attribute("todo.id", todo_id)
        
        try:
            todo = todo_service.get_todo(todo_id)
            if not todo:
                span.set_attribute("result.found", False)
                raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
            
            span.set_attribute("result.found", True)
            return todo
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/todos", response_model=List[Todo])
def get_todos(
    skip: int = 0, 
    limit: int = 100, 
    todo_service: TodoService = Depends(get_todo_service)
):
    with tracer.start_as_current_span("api.get_todos") as span:
        span.set_attribute("api.operation", "get_todos")
        span.set_attribute("query.skip", skip)
        span.set_attribute("query.limit", limit)
        
        try:
            todos = todo_service.get_todos(skip, limit)
            span.set_attribute("result.count", len(todos))
            return todos
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/todos", response_model=List[Todo])
def get_user_todos(
    user_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    todo_service: TodoService = Depends(get_todo_service)
):
    with tracer.start_as_current_span("api.get_user_todos") as span:
        span.set_attribute("api.operation", "get_user_todos")
        span.set_attribute("user.id", user_id)
        span.set_attribute("query.skip", skip)
        span.set_attribute("query.limit", limit)
        
        try:
            todos = todo_service.get_user_todos(user_id, skip, limit)
            span.set_attribute("result.count", len(todos))
            return todos
        except ValueError as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(
    todo_id: int, 
    todo: TodoUpdate, 
    todo_service: TodoService = Depends(get_todo_service)
):
    with tracer.start_as_current_span("api.update_todo") as span:
        span.set_attribute("api.operation", "update_todo")
        span.set_attribute("todo.id", todo_id)
        
        try:
            todo_data = todo.dict(exclude_unset=True)
            updated_todo = todo_service.update_todo(todo_id, todo_data)
            
            if not updated_todo:
                span.set_attribute("result.found", False)
                raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
            
            span.set_attribute("result.found", True)
            return updated_todo
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(
    todo_id: int, 
    todo_service: TodoService = Depends(get_todo_service)
):
    with tracer.start_as_current_span("api.delete_todo") as span:
        span.set_attribute("api.operation", "delete_todo")
        span.set_attribute("todo.id", todo_id)
        
        try:
            result = todo_service.delete_todo(todo_id)
            
            if not result:
                span.set_attribute("result.found", False)
                raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
            
            span.set_attribute("result.found", True)
            return None
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.put("/todos/{todo_id}/complete", response_model=Todo)
def mark_todo_completed(
    todo_id: int, 
    completed: bool = True, 
    todo_service: TodoService = Depends(get_todo_service)
):
    with tracer.start_as_current_span("api.mark_todo_completed") as span:
        span.set_attribute("api.operation", "mark_todo_completed")
        span.set_attribute("todo.id", todo_id)
        span.set_attribute("todo.completed", completed)
        
        try:
            updated_todo = todo_service.mark_todo_completed(todo_id, completed)
            
            if not updated_todo:
                span.set_attribute("result.found", False)
                raise HTTPException(status_code=404, detail=f"Todo with ID {todo_id} not found")
            
            span.set_attribute("result.found", True)
            return updated_todo
        except HTTPException:
            raise
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

# Real external API call
@app.get("/weather/{city}", response_model=WeatherResponse)
@API_OPERATION_TIME.time()
def get_weather(
    city: str, 
    external_api_service: ExternalApiService = Depends(get_external_api_service)
):
    with tracer.start_as_current_span("api.get_weather") as span:
        span.set_attribute("api.operation", "get_weather")
        span.set_attribute("api.city", city)
        
        try:
            result = external_api_service.get_weather(city)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

# Database operation endpoint (now using real database)
@app.get("/db-operation")
@DB_OPERATION_TIME.time()
def db_operation(
    user_service: UserService = Depends(get_user_service),
    todo_service: TodoService = Depends(get_todo_service)
):
    with tracer.start_as_current_span("database-operation") as parent_span:
        parent_span.set_attribute("operation.type", "database")
        parent_span.set_attribute("database.name", "sqlite")
        parent_span.set_attribute("database.system", "sqlite")
        
        try:
            # Create a test user
            with tracer.start_as_current_span("create-test-user") as user_span:
                user_span.set_attribute("operation", "create_user")
                
                username = f"testuser_{random.randint(1000, 9999)}"
                email = f"{username}@example.com"
                
                user = user_service.create_user(
                    username=username,
                    email=email,
                    password="testpassword"
                )
                
                user_span.set_attribute("user.id", user["id"])
                user_span.set_attribute("user.username", user["username"])
            
            # Create some todos for the user
            todos = []
            with tracer.start_as_current_span("create-test-todos") as todos_span:
                todos_span.set_attribute("operation", "create_todos")
                
                # Create 3 todos
                for i in range(3):
                    todo = todo_service.create_todo(
                        user_id=user["id"],
                        title=f"Test Todo {i+1}",
                        description=f"Description for test todo {i+1}",
                        priority=random.randint(1, 5)
                    )
                    todos.append(todo)
                
                todos_span.set_attribute("todos.count", len(todos))
            
            # Get all todos for the user
            with tracer.start_as_current_span("get-user-todos") as get_span:
                get_span.set_attribute("operation", "get_user_todos")
                get_span.set_attribute("user.id", user["id"])
                
                user_todos = todo_service.get_user_todos(user["id"])
                get_span.set_attribute("todos.count", len(user_todos))
            
            # Mark one todo as completed
            with tracer.start_as_current_span("complete-todo") as complete_span:
                complete_span.set_attribute("operation", "mark_todo_completed")
                
                if todos:
                    todo_id = todos[0]["id"]
                    complete_span.set_attribute("todo.id", todo_id)
                    
                    updated_todo = todo_service.mark_todo_completed(todo_id)
                    complete_span.set_attribute("todo.completed", updated_todo["completed"])
            
            return {
                "result": "Database operation completed",
                "user": user,
                "todos_created": len(todos),
                "todos_retrieved": len(user_todos)
            }
        except Exception as e:
            parent_span.record_exception(e)
            parent_span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

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

# Complex operation with multiple nested spans (now using real operations)
@app.get("/complex-operation")
def complex_operation(
    user_service: UserService = Depends(get_user_service),
    todo_service: TodoService = Depends(get_todo_service),
    external_api_service: ExternalApiService = Depends(get_external_api_service)
):
    with tracer.start_as_current_span("complex-operation") as parent_span:
        parent_span.set_attribute("operation.complexity", "high")
        parent_span.set_attribute("operation.id", f"op-{random.randint(10000, 99999)}")
        
        try:
            results = {}
            
            # Step 1: Data preparation - Create a user
            with tracer.start_as_current_span("data-preparation") as prep_span:
                prep_span.set_attribute("data.size", "medium")
                
                # Create a test user
                username = f"complex_user_{random.randint(1000, 9999)}"
                email = f"{username}@example.com"
                
                user = user_service.create_user(
                    username=username,
                    email=email,
                    password="complexpassword"
                )
                
                prep_span.set_attribute("user.id", user["id"])
                results["user"] = user
                
                # Sub-step: Data validation
                with tracer.start_as_current_span("data-validation") as validation_span:
                    validation_span.set_attribute("validation.rules", 5)
                    
                    # Validate user was created correctly
                    retrieved_user = user_service.get_user(user["id"])
                    validation_span.set_attribute("validation.success", retrieved_user is not None)
                    
                    if not retrieved_user:
                        raise ValueError("User validation failed")
            
            # Step 2: Processing - Create todos and get weather
            with tracer.start_as_current_span("data-processing") as processing_span:
                processing_span.set_attribute("processing.batch_size", 50)
                
                todos = []
                
                # Sub-step 1: First processing phase - Create todos
                with tracer.start_as_current_span("processing-phase-1") as phase1_span:
                    phase1_span.set_attribute("phase", 1)
                    
                    # Create 3 todos
                    for i in range(3):
                        todo = todo_service.create_todo(
                            user_id=user["id"],
                            title=f"Complex Todo {i+1}",
                            description=f"Description for complex todo {i+1}",
                            priority=random.randint(1, 5)
                        )
                        todos.append(todo)
                    
                    phase1_span.set_attribute("todos.count", len(todos))
                    results["todos"] = todos
                
                # Sub-step 2: Second processing phase - Get weather
                with tracer.start_as_current_span("processing-phase-2") as phase2_span:
                    phase2_span.set_attribute("phase", 2)
                    
                    # Get weather for a random city
                    cities = ["London", "New York", "Tokyo", "Paris", "Sydney"]
                    city = random.choice(cities)
                    
                    weather = external_api_service.get_weather(city)
                    phase2_span.set_attribute("weather.city", city)
                    phase2_span.set_attribute("weather.temperature", weather["temperature"])
                    results["weather"] = weather
                    
                    # Nested operation in phase 2 - Mark a todo as completed
                    with tracer.start_as_current_span("specialized-calculation") as calc_span:
                        calc_span.set_attribute("calculation.type", "todo_completion")
                        
                        if todos:
                            todo_id = todos[0]["id"]
                            updated_todo = todo_service.mark_todo_completed(todo_id)
                            calc_span.set_attribute("todo.id", todo_id)
                            calc_span.set_attribute("todo.completed", updated_todo["completed"])
                            results["completed_todo"] = updated_todo
            
            # Step 3: Result compilation
            with tracer.start_as_current_span("result-compilation") as result_span:
                result_span.set_attribute("results.count", len(results))
                
                # Get all todos for the user
                user_todos = todo_service.get_user_todos(user["id"])
                result_span.set_attribute("todos.total", len(user_todos))
                result_span.set_attribute("todos.completed", sum(1 for t in user_todos if t["completed"]))
                
                results["user_todos"] = user_todos
            
            return {
                "status": "completed",
                "steps_executed": 3,
                "user_id": user["id"],
                "todos_created": len(todos),
                "weather_city": results["weather"]["city"],
                "todos_completed": sum(1 for t in user_todos if t["completed"]),
                "result": "Complex operation finished successfully"
            }
        except Exception as e:
            parent_span.record_exception(e)
            parent_span.set_status(StatusCode.ERROR, str(e))
            ERROR_COUNTER.labels(error_type=type(e).__name__).inc()
            raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}
