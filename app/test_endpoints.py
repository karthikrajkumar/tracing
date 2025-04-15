#!/usr/bin/env python3
"""
Test script to generate trace data for all endpoints.
This script will make requests to all the endpoints we've created,
generating a mix of successful and error cases.
"""

import requests
import time
import random
import concurrent.futures
import argparse
import json
import uuid

# Default settings
DEFAULT_HOST = "http://localhost:8000"
DEFAULT_RUNS = 10
DEFAULT_CONCURRENCY = 3
DEFAULT_DELAY = 0.5

def make_request(endpoint, host=DEFAULT_HOST, method="GET", data=None):
    """Make a request to the specified endpoint and return the response."""
    url = f"{host}{endpoint}"
    try:
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method.upper() == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        duration = time.time() - start_time
        
        print(f"{method} request to {endpoint} completed in {duration:.3f}s with status {response.status_code}")
        
        if response.status_code >= 200 and response.status_code < 300:
            if response.status_code != 204:  # No content
                return response.json()
            return {"status": "success"}
        else:
            print(f"Error response: {response.text}")
            return None
    except Exception as e:
        print(f"Error making {method} request to {endpoint}: {str(e)}")
        return None

def create_user(host=DEFAULT_HOST):
    """Create a test user and return the user data."""
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    password = "testpassword123"
    
    user_data = {
        "username": username,
        "email": email,
        "password": password
    }
    
    response = make_request("/users", host, method="POST", data=user_data)
    return response

def create_todo(user_id, host=DEFAULT_HOST):
    """Create a test todo for the specified user and return the todo data."""
    todo_data = {
        "title": f"Test Todo {random.randint(1000, 9999)}",
        "description": f"This is a test todo created at {time.time()}",
        "priority": random.randint(1, 5)
    }
    
    response = make_request(f"/users/{user_id}/todos", host, method="POST", data=todo_data)
    return response

def test_user_flow(host=DEFAULT_HOST):
    """Test the user-related endpoints."""
    print("\nTesting user flow...")
    
    # Create a user
    user = create_user(host)
    if not user:
        print("Failed to create user")
        return
    
    user_id = user["id"]
    print(f"Created user with ID {user_id}")
    
    # Get the user
    get_user = make_request(f"/users/{user_id}", host)
    if not get_user:
        print(f"Failed to get user with ID {user_id}")
    
    # Update the user
    update_data = {"username": f"updated_{user['username']}"}
    updated_user = make_request(f"/users/{user_id}", host, method="PUT", data=update_data)
    if not updated_user:
        print(f"Failed to update user with ID {user_id}")
    
    # Get all users
    users = make_request("/users", host)
    if not users:
        print("Failed to get users")
    
    # Create todos for the user
    todos = []
    for _ in range(3):
        todo = create_todo(user_id, host)
        if todo:
            todos.append(todo)
    
    print(f"Created {len(todos)} todos for user {user_id}")
    
    # Get user's todos
    user_todos = make_request(f"/users/{user_id}/todos", host)
    if not user_todos:
        print(f"Failed to get todos for user {user_id}")
    
    # Mark a todo as completed
    if todos:
        todo_id = todos[0]["id"]
        completed_todo = make_request(f"/todos/{todo_id}/complete", host, method="PUT")
        if not completed_todo:
            print(f"Failed to mark todo {todo_id} as completed")
    
    # Get all todos
    all_todos = make_request("/todos", host)
    if not all_todos:
        print("Failed to get all todos")
    
    # Delete a todo
    if len(todos) > 1:
        todo_id = todos[1]["id"]
        delete_result = make_request(f"/todos/{todo_id}", host, method="DELETE")
        if not delete_result:
            print(f"Failed to delete todo {todo_id}")
    
    # Delete the user (optional - comment out if you want to keep the test data)
    # delete_result = make_request(f"/users/{user_id}", host, method="DELETE")
    # if not delete_result:
    #     print(f"Failed to delete user {user_id}")
    
    return user_id

def test_weather_api(host=DEFAULT_HOST):
    """Test the weather API endpoint."""
    print("\nTesting weather API...")
    
    cities = ["London", "New York", "Tokyo", "Paris", "Sydney"]
    city = random.choice(cities)
    
    weather = make_request(f"/weather/{city}", host)
    if weather:
        print(f"Weather for {city}: {weather['temperature']}°C, {weather['conditions']}")
    else:
        print(f"Failed to get weather for {city}")

def run_test(host=DEFAULT_HOST, runs=DEFAULT_RUNS, concurrency=DEFAULT_CONCURRENCY, delay=DEFAULT_DELAY):
    """Run the test with the specified parameters."""
    print(f"\n{'='*80}\nStarting test with {runs} runs, {concurrency} concurrent requests, and {delay}s delay\n{'='*80}\n")
    
    # First, test the user flow to create some data
    user_id = test_user_flow(host)
    
    # Test the weather API
    test_weather_api(host)
    
    # List of all endpoints
    endpoints = [
        "/hello",
        "/db-operation",
        "/complex-operation",
        "/health",
        f"/users/{user_id}" if user_id else "/users",
        "/todos",
        f"/weather/{random.choice(['London', 'New York', 'Tokyo', 'Paris', 'Sydney'])}"
    ]
    
    # Run the specified number of test iterations
    for i in range(runs):
        print(f"\nRun {i+1}/{runs}")
        
        # Randomly select endpoints for this run
        selected_endpoints = random.sample(endpoints, min(concurrency, len(endpoints)))
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(make_request, endpoint, host) for endpoint in selected_endpoints]
            concurrent.futures.wait(futures)
        
        # Add some error simulation requests with different probabilities
        error_probs = [0.0, 0.25, 0.5, 0.75, 1.0]
        for prob in random.sample(error_probs, min(2, len(error_probs))):
            make_request(f"/error-simulation?error_probability={prob}", host)
        
        # Wait before the next run
        if i < runs - 1:
            time.sleep(delay)
    
    print(f"\n{'='*80}\nTest completed. {runs} runs with {concurrency} concurrent requests\n{'='*80}")
    
    # Check metrics endpoint
    print("\nChecking metrics endpoint...")
    metrics_response = requests.get(f"{host}/metrics")
    if metrics_response.status_code == 200:
        print("Metrics endpoint is working. Sample metrics:")
        
        # Print a few sample metrics
        metrics_text = metrics_response.text
        metrics_lines = metrics_text.split("\n")
        
        # Filter for interesting metrics and print a sample
        interesting_metrics = [
            "request_processing_seconds",
            "db_operation_processing_seconds",
            "api_operation_processing_seconds",
            "application_errors_total",
            "http_requests_total",
            "request_latency_seconds",
            "concurrent_requests"
        ]
        
        for metric in interesting_metrics:
            matching_lines = [line for line in metrics_lines if metric in line and not line.startswith("#")]
            if matching_lines:
                print(f"\n{metric} samples:")
                for line in matching_lines[:3]:  # Print up to 3 samples
                    print(f"  {line}")
    else:
        print(f"Failed to access metrics endpoint: {metrics_response.status_code}")
    
    print("\nTest complete!")
    print(f"You can view traces in Jaeger UI at: http://localhost:16686")
    print(f"You can view metrics in Prometheus at: http://localhost:9090")
    if host != DEFAULT_HOST:
        print(f"Note: Tests were run against {host}, make sure this matches your Prometheus scrape config")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test script for generating trace data")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host URL (default: {DEFAULT_HOST})")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help=f"Number of test runs (default: {DEFAULT_RUNS})")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, 
                        help=f"Number of concurrent requests (default: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, 
                        help=f"Delay between runs in seconds (default: {DEFAULT_DELAY})")
    
    args = parser.parse_args()
    run_test(args.host, args.runs, args.concurrency, args.delay)
