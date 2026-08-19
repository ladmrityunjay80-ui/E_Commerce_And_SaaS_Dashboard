import os
import multiprocessing

bind = os.getenv("BIND", "0.0.0.0:8000")
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
keepalive = 5
errorlog = "-"
accesslog = "-"
preload_app = True
