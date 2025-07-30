#!/bin/bash
set -e

# Start virtual display in background
Xvfb :99 -screen 0 1024x768x16 -ac +extension GLX +render -noreset &
sleep 2

# Start gunicorn
exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 300 --preload "app:create_app()"