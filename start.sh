#!/bin/sh
# Use $PORT if set, otherwise default to 8000
echo "🚀 Starting Notes App with 3D Dashboard - Version 1.0.3"
echo "📅 Build Date: $(date)"
echo "🐍 Python version: $(python --version)"
echo "🌐 Port: ${PORT:-8000}"
echo "📁 Working directory: $(pwd)"
echo "📄 Files in directory: $(ls -la)"

# Initialize database
echo "🗄️ Initializing database..."
python -c "from database import init_db; init_db()" 2>/dev/null || echo "Database already exists"

# Create admin user  
echo "👤 Creating admin user..."
python create_simple_admin.py 2>/dev/null || echo "Admin user already exists"

echo "🎊 Starting 3D Admin Dashboard server..."

# Start with gunicorn for production
exec gunicorn -k uvicorn.workers.UvicornWorker main:app \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 1 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 200 \
    --max-requests-jitter 50 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
