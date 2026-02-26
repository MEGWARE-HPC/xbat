"""
Production Gunicorn configuration.
No SSL used as this is provided by nginx and backend is only accessible through nginx from the outside.
"""

wsgi_app = "restapi:create_app()"
bind = "0.0.0.0:8001"
workers = 8
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 240 # temporarily increased timeout due to slow export call
keepalive = 30

preload_app = False
reload = False

errorlog = "-"
# debug, info, warning, error, critical
loglevel = "warning"
accesslog = "-"
capture_output = True


def worker_abort(worker):
    worker.log.info("WORKERABORT worker received SIGABRT signal")
    raise Exception(f"Gunicorn worker aborted: {worker}")
