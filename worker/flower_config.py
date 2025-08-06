# Flower configuration for DocuVerse
import os

# Basic configuration
broker_api = os.getenv("REDIS_URL", "redis://localhost:6379/0")
broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Flower settings
port = 5555
address = "0.0.0.0"
url_prefix = ""
max_tasks = 10000
persistent = True
db = "/tmp/flower.db"
state_save_interval = 60000  # 1 minute
enable_events = True
auto_refresh = True
auto_refresh_interval = 5000  # 5 seconds

# Authentication (optional - uncomment to enable)
# basic_auth = ['admin:password']

# Task monitoring
task_annotations = {
    "app.workers.document_processor.process_document_task": {
        "rate_limit": "10/m",
        "time_limit": 1800,  # 30 minutes
        "soft_time_limit": 1500,  # 25 minutes
    }
}

# Worker monitoring
worker_annotations = {
    "*": {
        "max_concurrency": 4,
        "max_tasks_per_child": 1000,
    }
}

# Logging
logging = "INFO"
log_file = "/tmp/flower.log"

# Security (optional)
# auth = 'flower.auth.GoogleAuth'
# auth_provider = 'flower.auth.GoogleAuth'
# oauth2_key = 'your_oauth2_key'
# oauth2_secret = 'your_oauth2_secret'
# oauth2_redirect_uri = 'http://localhost:5555/login'

# CORS settings
cors_origins = ["*"]
cors_credentials = True

# Task routing
task_routes = {
    "app.workers.document_processor.*": {"queue": "docuverse"},
}

# Queue monitoring
queues = ["docuverse", "celery"]

# Metrics
enable_metrics = True
metrics_interval = 5000  # 5 seconds

# WebSocket support
enable_websocket = True
