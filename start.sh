#!/bin/sh
# Use $PORT if set, otherwise default to 8000
echo "Starting application on port ${PORT:-8000}"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "Files in directory: $(ls -la)"

# Start with gunicorn for production
exec gunicorn -k uvicorn.workers.UvicornWorker main:app \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 1 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 200 \
    --max-requests-jitter 50 \
    --log-level info
