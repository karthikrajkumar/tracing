from fastapi import FastAPI, Request, Response, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import time
import random
import requests
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.routers import users, items
from app.services.external_service import ExternalApiService
from app.schemas import WeatherResponse, ErrorResponse

app = FastAPI(
    title="Sample FastAPI App",
    description="A sample FastAPI application with no explicit OpenTelemetry instrumentation",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(items.router)

# Startup event to initialize the database
@app.on_event("startup")
def startup_event():
    init_db()

# Basic endpoints
@app.get("/")
def read_root():
    return {"message": "Welcome to the Sample FastAPI App"}

@app.get("/hello")
def hello():
    # Simulate some processing time
    time.sleep(0.5)
    return {"message": "Hello from FastAPI!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

# Weather endpoint
@app.get("/weather/{city}", response_model=WeatherResponse)
def get_weather(city: str):
    # Get weather data
    external_service = ExternalApiService()
    try:
        return external_service.get_weather(city)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting weather data: {str(e)}"
        )

# Slow operation endpoint
@app.get("/slow-operation")
def slow_operation():
    # Simulate a slow operation
    time.sleep(random.uniform(0.5, 2.0))
    return {"message": "Slow operation completed"}

# Error simulation endpoint
@app.get("/error-simulation", response_model=None, responses={500: {"model": ErrorResponse}})
def error_simulation(error_probability: float = 0.5):
    # Simulate an error based on probability
    if random.random() < error_probability:
        raise HTTPException(
            status_code=500,
            detail="Simulated error occurred"
        )
    return {"message": "Operation completed successfully"}

# Complex operation endpoint
@app.get("/complex-operation")
def complex_operation(
    db: Session = Depends(get_db)
):
    results = {}
    
    # Step 1: Database operation
    try:
        # Simulate complex database query
        time.sleep(random.uniform(0.2, 0.5))
        users_count = len(db.execute("SELECT id FROM users").fetchall())
        items_count = len(db.execute("SELECT id FROM items").fetchall())
        results["database"] = {
            "users_count": users_count,
            "items_count": items_count
        }
    except Exception as e:
        results["database"] = {"error": str(e)}
    
    # Step 2: External API call
    try:
        # Make external API call
        external_service = ExternalApiService()
        todos = external_service.get_todos()
        results["external_api"] = {
            "todos_count": len(todos),
            "sample_todo": todos[0] if todos else None
        }
    except Exception as e:
        results["external_api"] = {"error": str(e)}
    
    # Step 3: CPU-intensive operation
    try:
        # Simulate CPU-intensive operation
        start_time = time.time()
        result = 0
        for i in range(1000000):
            result += i
        duration = time.time() - start_time
        results["cpu_operation"] = {
            "result": result,
            "duration_ms": duration * 1000
        }
    except Exception as e:
        results["cpu_operation"] = {"error": str(e)}
    
    return {
        "message": "Complex operation completed",
        "results": results
    }

# Nested operations endpoint
@app.get("/nested-operations")
def nested_operations(
    depth: int = 3,
    width: int = 2,
    db: Session = Depends(get_db)
):
    """Perform nested operations to generate a complex trace."""
    
    def perform_operation(current_depth, operation_id):
        # Base case
        if current_depth <= 0:
            return {
                "operation_id": operation_id,
                "depth": current_depth,
                "result": "Leaf node reached"
            }
        
        # Simulate some work
        time.sleep(random.uniform(0.05, 0.2))
        
        # Perform different operations based on depth
        results = {}
        
        if current_depth % 3 == 0:
            # Database operation
            try:
                query_result = db.execute(f"SELECT COUNT(*) FROM users").fetchone()
                results["db_operation"] = {
                    "query": "SELECT COUNT(*) FROM users",
                    "result": query_result[0] if query_result else 0
                }
            except Exception as e:
                results["db_operation"] = {"error": str(e)}
        
        elif current_depth % 3 == 1:
            # External API call
            try:
                response = requests.get("https://jsonplaceholder.typicode.com/todos/1")
                results["api_call"] = {
                    "status_code": response.status_code,
                    "data": response.json() if response.status_code == 200 else None
                }
            except Exception as e:
                results["api_call"] = {"error": str(e)}
        
        else:
            # CPU operation
            start = time.time()
            result = 0
            for i in range(100000):
                result += i
            duration = time.time() - start
            results["cpu_operation"] = {
                "result": result,
                "duration_ms": duration * 1000
            }
        
        # Recursive calls
        children = []
        for i in range(width):
            child_id = f"{operation_id}-{i}"
            child_result = perform_operation(current_depth - 1, child_id)
            children.append(child_result)
        
        return {
            "operation_id": operation_id,
            "depth": current_depth,
            "results": results,
            "children": children
        }
    
    # Start the recursive operation
    return perform_operation(depth, "root")

# Background task endpoint
@app.get("/background-task")
def background_task_endpoint(background_tasks: BackgroundTasks):
    """Endpoint that triggers a background task."""
    
    def process_background_task():
        # Simulate background processing
        time.sleep(random.uniform(1.0, 3.0))
        
        # Perform some database operations
        try:
            db = next(get_db())
            db.execute("SELECT COUNT(*) FROM users")
            db.execute("SELECT COUNT(*) FROM items")
        except Exception as e:
            print(f"Background task error: {str(e)}")
        finally:
            db.close()
        
        # Make an external API call
        try:
            requests.get("https://jsonplaceholder.typicode.com/todos/1")
        except Exception as e:
            print(f"Background task API error: {str(e)}")
    
    # Add the task to background tasks
    background_tasks.add_task(process_background_task)
    
    return {"message": "Background task started"}
