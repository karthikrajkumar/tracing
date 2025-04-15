from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from .database import User, Todo
from opentelemetry import trace

# Get tracer
tracer = trace.get_tracer(__name__)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, username: str, email: str, hashed_password: str) -> User:
        with tracer.start_as_current_span("db.create_user") as span:
            span.set_attribute("db.operation", "create")
            span.set_attribute("db.table", "users")
            span.set_attribute("user.username", username)
            span.set_attribute("user.email", email)
            
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            span.set_attribute("user.id", user.id)
            return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        with tracer.start_as_current_span("db.get_user_by_id") as span:
            span.set_attribute("db.operation", "read")
            span.set_attribute("db.table", "users")
            span.set_attribute("user.id", user_id)
            
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if user:
                span.set_attribute("result.found", True)
            else:
                span.set_attribute("result.found", False)
                
            return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        with tracer.start_as_current_span("db.get_user_by_username") as span:
            span.set_attribute("db.operation", "read")
            span.set_attribute("db.table", "users")
            span.set_attribute("user.username", username)
            
            user = self.db.query(User).filter(User.username == username).first()
            
            if user:
                span.set_attribute("result.found", True)
            else:
                span.set_attribute("result.found", False)
                
            return user

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        with tracer.start_as_current_span("db.get_users") as span:
            span.set_attribute("db.operation", "read_many")
            span.set_attribute("db.table", "users")
            span.set_attribute("query.skip", skip)
            span.set_attribute("query.limit", limit)
            
            users = self.db.query(User).offset(skip).limit(limit).all()
            
            span.set_attribute("result.count", len(users))
            return users

    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        with tracer.start_as_current_span("db.update_user") as span:
            span.set_attribute("db.operation", "update")
            span.set_attribute("db.table", "users")
            span.set_attribute("user.id", user_id)
            
            # First check if user exists
            user = self.get_user_by_id(user_id)
            if not user:
                span.set_attribute("result.success", False)
                return None
                
            # Update user
            for key, value in user_data.items():
                setattr(user, key, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            span.set_attribute("result.success", True)
            return user

    def delete_user(self, user_id: int) -> bool:
        with tracer.start_as_current_span("db.delete_user") as span:
            span.set_attribute("db.operation", "delete")
            span.set_attribute("db.table", "users")
            span.set_attribute("user.id", user_id)
            
            # First check if user exists
            user = self.get_user_by_id(user_id)
            if not user:
                span.set_attribute("result.success", False)
                return False
                
            # Delete user
            self.db.delete(user)
            self.db.commit()
            
            span.set_attribute("result.success", True)
            return True


class TodoRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_todo(self, user_id: int, title: str, description: str, priority: int = 1) -> Todo:
        with tracer.start_as_current_span("db.create_todo") as span:
            span.set_attribute("db.operation", "create")
            span.set_attribute("db.table", "todos")
            span.set_attribute("todo.title", title)
            span.set_attribute("todo.user_id", user_id)
            
            todo = Todo(
                title=title,
                description=description,
                priority=priority,
                user_id=user_id
            )
            self.db.add(todo)
            self.db.commit()
            self.db.refresh(todo)
            
            span.set_attribute("todo.id", todo.id)
            return todo

    def get_todo_by_id(self, todo_id: int) -> Optional[Todo]:
        with tracer.start_as_current_span("db.get_todo_by_id") as span:
            span.set_attribute("db.operation", "read")
            span.set_attribute("db.table", "todos")
            span.set_attribute("todo.id", todo_id)
            
            todo = self.db.query(Todo).filter(Todo.id == todo_id).first()
            
            if todo:
                span.set_attribute("result.found", True)
            else:
                span.set_attribute("result.found", False)
                
            return todo

    def get_todos(self, skip: int = 0, limit: int = 100) -> List[Todo]:
        with tracer.start_as_current_span("db.get_todos") as span:
            span.set_attribute("db.operation", "read_many")
            span.set_attribute("db.table", "todos")
            span.set_attribute("query.skip", skip)
            span.set_attribute("query.limit", limit)
            
            todos = self.db.query(Todo).offset(skip).limit(limit).all()
            
            span.set_attribute("result.count", len(todos))
            return todos

    def get_user_todos(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Todo]:
        with tracer.start_as_current_span("db.get_user_todos") as span:
            span.set_attribute("db.operation", "read_many")
            span.set_attribute("db.table", "todos")
            span.set_attribute("user.id", user_id)
            span.set_attribute("query.skip", skip)
            span.set_attribute("query.limit", limit)
            
            todos = self.db.query(Todo).filter(Todo.user_id == user_id).offset(skip).limit(limit).all()
            
            span.set_attribute("result.count", len(todos))
            return todos

    def update_todo(self, todo_id: int, todo_data: Dict[str, Any]) -> Optional[Todo]:
        with tracer.start_as_current_span("db.update_todo") as span:
            span.set_attribute("db.operation", "update")
            span.set_attribute("db.table", "todos")
            span.set_attribute("todo.id", todo_id)
            
            # First check if todo exists
            todo = self.get_todo_by_id(todo_id)
            if not todo:
                span.set_attribute("result.success", False)
                return None
                
            # Update todo
            for key, value in todo_data.items():
                setattr(todo, key, value)
            
            self.db.commit()
            self.db.refresh(todo)
            
            span.set_attribute("result.success", True)
            return todo

    def delete_todo(self, todo_id: int) -> bool:
        with tracer.start_as_current_span("db.delete_todo") as span:
            span.set_attribute("db.operation", "delete")
            span.set_attribute("db.table", "todos")
            span.set_attribute("todo.id", todo_id)
            
            # First check if todo exists
            todo = self.get_todo_by_id(todo_id)
            if not todo:
                span.set_attribute("result.success", False)
                return False
                
            # Delete todo
            self.db.delete(todo)
            self.db.commit()
            
            span.set_attribute("result.success", True)
            return True

    def mark_todo_completed(self, todo_id: int, completed: bool = True) -> Optional[Todo]:
        with tracer.start_as_current_span("db.mark_todo_completed") as span:
            span.set_attribute("db.operation", "update")
            span.set_attribute("db.table", "todos")
            span.set_attribute("todo.id", todo_id)
            span.set_attribute("todo.completed", completed)
            
            return self.update_todo(todo_id, {"completed": completed})
