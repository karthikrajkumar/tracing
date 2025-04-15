from prometheus_client import Summary, Counter, Histogram, Gauge

# Existing metrics
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

# New metrics for specific operations
DB_OPERATION_TIME = Summary('db_operation_processing_seconds', 'Time spent processing database operations')
API_OPERATION_TIME = Summary('api_operation_processing_seconds', 'Time spent processing API operations')

# Counter for tracking errors
ERROR_COUNTER = Counter('application_errors_total', 'Total count of application errors', ['error_type'])

# Counter for tracking HTTP requests
REQUEST_COUNTER = Counter('http_requests_total', 'Total count of HTTP requests', ['method', 'endpoint', 'status'])

# Histogram for more detailed latency measurements
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency in seconds', 
                           ['endpoint'], buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0))

# Gauge for tracking concurrent requests
CONCURRENT_REQUESTS = Gauge('concurrent_requests', 'Number of concurrent requests')
