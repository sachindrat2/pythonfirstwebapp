#!/bin/sh
# Use $PORT if set, otherwise default to 8000
gunicorn -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:${PORT:-8000}
