from typing import List, Optional, Dict, Any
import hashlib
import random
import time
import requests
from .repositories import UserRepository, TodoRepository
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# Initialize requests instrumentation
RequestsInstrumentor().instrument()

# Get tracer
tracer = trace.get_tracer(__name__)

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        with tracer.start_as_current_span("service.create_user") as span:
            span.set_attribute("service.name", "user_service")
            span.set_attribute("operation.name", "create_user")
            
            # Hash the password (in a real app, use a proper password hashing library)
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            
            try:
                # Create user in database
                user = self.user_repository.create_user(
                    username=username,
                    email=email,
                    hashed_password=hashed_password
                )
                
                # Return user data
                span.set_attribute("result.success", True)
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                }
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        with tracer.start_as_current_span("service.get_user") as span:
            span.set_attribute("service.name", "user_service")
            span.set_attribute("operation.name", "get_user")
            span.set_attribute("user.id", user_id)
            
            try:
                # Get user from database
                user = self.user_repository.get_user_by_id(user_id)
                
                if not user:
                    span.set_attribute("result.found", False)
                    return None
                
                # Return user data
                span.set_attribute("result.found", True)
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                }
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def get_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        with tracer.start_as_current_span("service.get_users") as span:
            span.set_attribute("service.name", "user_service")
            span.set_attribute("operation.name", "get_users")
            span.set_attribute("query.skip", skip)
            span.set_attribute("query.limit", limit)
            
            try:
                # Get users from database
                users = self.user_repository.get_users(skip, limit)
                
                # Return user data
                span.set_attribute("result.count", len(users))
                return [
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "is_active": user.is_active,
                        "created_at": user.created_at.isoformat()
                    }
                    for user in users
                ]
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with tracer.start_as_current_span("service.update_user") as span:
            span.set_attribute("service.name", "user_service")
            span.set_attribute("operation.name", "update_user")
            span.set_attribute("user.id", user_id)
            
            try:
                # Update user in database
                user = self.user_repository.update_user(user_id, user_data)
                
                if not user:
                    span.set_attribute("result.success", False)
                    return None
                
                # Return updated user data
                span.set_attribute("result.success", True)
                return {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat()
                }
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def delete_user(self, user_id: int) -> bool:
        with tracer.start_as_current_span("service.delete_user") as span:
            span.set_attribute("service.name", "user_service")
            span.set_attribute("operation.name", "delete_user")
            span.set_attribute("user.id", user_id)
            
            try:
                # Delete user from database
                result = self.user_repository.delete_user(user_id)
                
                # Return result
                span.set_attribute("result.success", result)
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise


class TodoService:
    def __init__(self, todo_repository: TodoRepository, user_repository: UserRepository):
        self.todo_repository = todo_repository
        self.user_repository = user_repository

    def create_todo(self, user_id: int, title: str, description: str, priority: int = 1) -> Dict[str, Any]:
        with tracer.start_as_current_span("service.create_todo") as span:
            span.set_attribute("service.name", "todo_service")
            span.set_attribute("operation.name", "create_todo")
            span.set_attribute("user.id", user_id)
            
            try:
                # Check if user exists
                user = self.user_repository.get_user_by_id(user_id)
                if not user:
                    span.set_attribute("result.error", "user_not_found")
                    span.set_status(StatusCode.ERROR, "User not found")
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Create todo in database
                todo = self.todo_repository.create_todo(
                    user_id=user_id,
                    title=title,
                    description=description,
                    priority=priority
                )
                
                # Return todo data
                span.set_attribute("result.success", True)
                span.set_attribute("todo.id", todo.id)
                return {
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description,
                    "completed": todo.completed,
                    "priority": todo.priority,
                    "user_id": todo.user_id,
                    "created_at": todo.created_at.isoformat()
                }
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def get_todo(self, todo_id: int) -> Optional[Dict[str, Any]]:
        with tracer.start_as_current_span("service.get_todo") as span:
            span.set_attribute("service.name", "todo_service")
            span.set_attribute("operation.name", "get_todo")
            span.set_attribute("todo.id", todo_id)
            
            try:
                # Get todo from database
                todo = self.todo_repository.get_todo_by_id(todo_id)
                
                if not todo:
                    span.set_attribute("result.found", False)
                    return None
                
                # Return todo data
                span.set_attribute("result.found", True)
                return {
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description,
                    "completed": todo.completed,
                    "priority": todo.priority,
                    "user_id": todo.user_id,
                    "created_at": todo.created_at.isoformat()
                }
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def get_todos(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        with tracer.start_as_current_span("service.get_todos") as span:
            span.set_attribute("service.name", "todo_service")
            span.set_attribute("operation.name", "get_todos")
            span.set_attribute("query.skip", skip)
            span.set_attribute("query.limit", limit)
            
            try:
                # Get todos from database
                todos = self.todo_repository.get_todos(skip, limit)
                
                # Return todo data
                span.set_attribute("result.count", len(todos))
                return [
                    {
                        "id": todo.id,
                        "title": todo.title,
                        "description": todo.description,
                        "completed": todo.completed,
                        "priority": todo.priority,
                        "user_id": todo.user_id,
                        "created_at": todo.created_at.isoformat()
                    }
                    for todo in todos
                ]
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def get_user_todos(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        with tracer.start_as_current_span("service.get_user_todos") as span:
            span.set_attribute("service.name", "todo_service")
            span.set_attribute("operation.name", "get_user_todos")
            span.set_attribute("user.id", user_id)
            span.set_attribute("query.skip", skip)
            span.set_attribute("query.limit", limit)
            
            try:
                # Check if user exists
                user = self.user_repository.get_user_by_id(user_id)
                if not user:
                    span.set_attribute("result.error", "user_not_found")
                    span.set_status(StatusCode.ERROR, "User not found")
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Get todos from database
                todos = self.todo_repository.get_user_todos(user_id, skip, limit)
                
                # Return todo data
                span.set_attribute("result.count", len(todos))
                return [
                    {
                        "id": todo.id,
                        "title": todo.title,
                        "description": todo.description,
                        "completed": todo.completed,
                        "priority": todo.priority,
                        "user_id": todo.user_id,
                        "created_at": todo.created_at.isoformat()
                    }
                    for todo in todos
                ]
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def update_todo(self, todo_id: int, todo_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with tracer.start_as_current_span("service.update_todo") as span:
            span.set_attribute("service.name", "todo_service")
            span.set_attribute("operation.name", "update_todo")
            span.set_attribute("todo.id", todo_id)
            
            try:
                # Update todo in database
                todo = self.todo_repository.update_todo(todo_id, todo_data)
                
                if not todo:
                    span.set_attribute("result.success", False)
                    return None
                
                # Return updated todo data
                span.set_attribute("result.success", True)
                return {
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description,
                    "completed": todo.completed,
                    "priority": todo.priority,
                    "user_id": todo.user_id,
                    "created_at": todo.created_at.isoformat()
                }
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def delete_todo(self, todo_id: int) -> bool:
        with tracer.start_as_current_span("service.delete_todo") as span:
            span.set_attribute("service.name", "todo_service")
            span.set_attribute("operation.name", "delete_todo")
            span.set_attribute("todo.id", todo_id)
            
            try:
                # Delete todo from database
                result = self.todo_repository.delete_todo(todo_id)
                
                # Return result
                span.set_attribute("result.success", result)
                return result
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise

    def mark_todo_completed(self, todo_id: int, completed: bool = True) -> Optional[Dict[str, Any]]:
        with tracer.start_as_current_span("service.mark_todo_completed") as span:
            span.set_attribute("service.name", "todo_service")
            span.set_attribute("operation.name", "mark_todo_completed")
            span.set_attribute("todo.id", todo_id)
            span.set_attribute("todo.completed", completed)
            
            try:
                # Mark todo as completed in database
                todo = self.todo_repository.mark_todo_completed(todo_id, completed)
                
                if not todo:
                    span.set_attribute("result.success", False)
                    return None
                
                # Return updated todo data
                span.set_attribute("result.success", True)
                return {
                    "id": todo.id,
                    "title": todo.title,
                    "description": todo.description,
                    "completed": todo.completed,
                    "priority": todo.priority,
                    "user_id": todo.user_id,
                    "created_at": todo.created_at.isoformat()
                }
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise


class ExternalApiService:
    def __init__(self):
        pass

    def get_weather(self, city: str) -> Dict[str, Any]:
        with tracer.start_as_current_span("service.get_weather") as span:
            span.set_attribute("service.name", "external_api_service")
            span.set_attribute("operation.name", "get_weather")
            span.set_attribute("api.city", city)
            
            try:
                # Make API request to weather service
                # In a real app, you would use an actual API key and endpoint
                url = f"https://jsonplaceholder.typicode.com/todos/1"
                span.set_attribute("http.url", url)
                span.set_attribute("http.method", "GET")
                
                # Add a small delay to simulate network latency
                time.sleep(0.2)
                
                # Make the actual HTTP request
                response = requests.get(url)
                span.set_attribute("http.status_code", response.status_code)
                
                # Process response
                if response.status_code == 200:
                    # In a real app, you would parse the actual weather data
                    # Here we're just simulating with the placeholder API
                    data = response.json()
                    
                    # Simulate weather data
                    weather_data = {
                        "city": city,
                        "temperature": round(random.uniform(0, 35), 1),
                        "conditions": random.choice(["Sunny", "Cloudy", "Rainy", "Snowy"]),
                        "humidity": random.randint(30, 90),
                        "wind_speed": round(random.uniform(0, 30), 1),
                        "timestamp": time.time()
                    }
                    
                    span.set_attribute("result.success", True)
                    return weather_data
                else:
                    span.set_attribute("result.success", False)
                    span.set_attribute("result.error", f"API returned status code {response.status_code}")
                    span.set_status(StatusCode.ERROR, f"API returned status code {response.status_code}")
                    return {
                        "error": f"API returned status code {response.status_code}",
                        "timestamp": time.time()
                    }
            except Exception as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, str(e))
                raise
