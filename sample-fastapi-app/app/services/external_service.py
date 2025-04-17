import requests
import time
import random
import json

class ExternalApiService:
    """Service for making external API calls."""
    
    def get_weather(self, city: str):
        """Get weather data for a city."""
        # Simulate API call delay
        time.sleep(random.uniform(0.3, 1.0))
        
        # In a real application, this would call an actual weather API
        # For this example, we'll simulate a response
        
        # Simulate occasional errors
        if random.random() < 0.1:  # 10% chance of error
            raise Exception("External API error: Weather service unavailable")
        
        # Generate random weather data
        temperature = round(random.uniform(-10, 40), 1)
        conditions = random.choice([
            "Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Stormy", "Snowy", "Foggy"
        ])
        humidity = round(random.uniform(30, 100), 1)
        wind_speed = round(random.uniform(0, 30), 1)
        
        return {
            "city": city,
            "temperature": temperature,
            "conditions": conditions,
            "humidity": humidity,
            "wind_speed": wind_speed
        }
    
    def get_user_data(self, user_id: int):
        """Get user data from an external API."""
        # Simulate API call delay
        time.sleep(random.uniform(0.2, 0.8))
        
        # Make a real API call to JSONPlaceholder
        try:
            response = requests.get(f"https://jsonplaceholder.typicode.com/users/{user_id}")
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            return response.json()
        except requests.RequestException as e:
            # Handle request errors
            raise Exception(f"External API error: {str(e)}")
    
    def get_todos(self, user_id: int = None):
        """Get todos from an external API."""
        # Simulate API call delay
        time.sleep(random.uniform(0.2, 0.8))
        
        # Make a real API call to JSONPlaceholder
        try:
            url = "https://jsonplaceholder.typicode.com/todos"
            if user_id:
                url += f"?userId={user_id}"
            
            response = requests.get(url)
            response.raise_for_status()  # Raise exception for 4XX/5XX responses
            
            # Limit the number of todos returned
            todos = response.json()
            return todos[:5]  # Return only the first 5 todos
        except requests.RequestException as e:
            # Handle request errors
            raise Exception(f"External API error: {str(e)}")
