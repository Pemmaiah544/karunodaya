"""
Gunicorn configuration file for Karunodaya Platform
Optimized for Docker / Local / Cloud deployment
"""

import multiprocessing
import os

# -----------------------------------
# Server Socket
# -----------------------------------

# IMPORTANT: Bind to 0.0.0.0 inside Docker
# Cloud Run injects PORT env var; default 8000 for local / Hetzner
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

backlog = 2048

# -----------------------------------
# Worker Processes
# -----------------------------------

# Recommended production formula
workers = multiprocessing.cpu_count() * 2 + 1

worker_class = "sync"
worker_connections = 1000

# Increased for ASR / ML inference calls that may take longer
timeout = 120
keepalive = 5

# -----------------------------------
# Logging
# -----------------------------------

# Log to stdout (Docker best practice)
accesslog = "-"
errorlog = "-"
loglevel = "info"

# -----------------------------------
# Process Naming
# -----------------------------------

proc_name = "karunodaya"

# -----------------------------------
# Server Mechanics
# -----------------------------------

daemon = False

# Do NOT use pidfile in Docker
pidfile = None

# Do NOT force user/group inside container
# user = "www-data"
# group = "www-data"

umask = 0

# -----------------------------------
# Optional: Graceful Restart
# -----------------------------------

graceful_timeout = 30
