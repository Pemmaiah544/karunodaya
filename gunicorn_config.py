"""
Gunicorn configuration file for Karunodaya Platform
"""

import multiprocessing

# Server Socket
bind = '127.0.0.1:8000'
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '/var/log/karunodaya/gunicorn_access.log'
errorlog = '/var/log/karunodaya/gunicorn_error.log'
loglevel = 'info'

# Process Naming
proc_name = 'karunodaya'

# Server Mechanics
daemon = False
pidfile = '/var/run/karunodaya/gunicorn.pid'
user = 'www-data'
group = 'www-data'
umask = 0o007

# SSL (if terminating SSL at Gunicorn level)
# keyfile = '/path/to/ssl/key.pem'
# certfile = '/path/to/ssl/cert.pem'
