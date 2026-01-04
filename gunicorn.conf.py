import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', '2'))
worker_class = 'sync'
worker_connections = 1000
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '7200'))  # 환경변수 사용 (기본 2시간)
keepalive = 5
graceful_timeout = 300  # graceful shutdown 5분

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'drama_server'

# Server mechanics
daemon = False
preload_app = True
