import multiprocessing
import os

bind = f"127.0.0.1:{os.getenv('PORT', '8000')}"

workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))

worker_class = "uvicorn.workers.UvicornWorker"

keepalive = 120

timeout = 120

graceful_timeout = 30

max_requests = 1000

max_requests_jitter = 50

accesslog = os.getenv('ACCESS_LOG', '/var/log/pdf-api/access.log')

errorlog = os.getenv('ERROR_LOG', '/var/log/pdf-api/error.log')

loglevel = os.getenv('LOG_LEVEL', 'info')

capture_output = True

enable_stdio_inheritance = True

preload_app = True

daemon = False
