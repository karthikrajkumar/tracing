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

# Default settings
DEFAULT_HOST = "http://localhost:8000"
DEFAULT_RUNS = 10
DEFAULT_CONCURRENCY = 3
DEFAULT_DELAY = 0.5

def make_request(endpoint, host=DEFAULT_HOST):
    """Make a request to the specified endpoint and return the response."""
    url = f"{host}{endpoint}"
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        duration = time.time() - start_time
        
        print(f"Request to {endpoint} completed in {duration:.3f}s with status {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"Error making request to {endpoint}: {str(e)}")
        return None

def run_test(host=DEFAULT_HOST, runs=DEFAULT_RUNS, concurrency=DEFAULT_CONCURRENCY, delay=DEFAULT_DELAY):
    """Run the test with the specified parameters."""
    print(f"\n{'='*80}\nStarting test with {runs} runs, {concurrency} concurrent requests, and {delay}s delay\n{'='*80}\n")
    
    # List of all endpoints
    endpoints = [
        "/hello",
        "/db-operation",
        "/external-api",
        "/error-simulation",
        "/complex-operation",
        "/health"
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
