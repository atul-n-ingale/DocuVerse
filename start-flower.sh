#!/bin/bash

echo "🌸 Starting Flower - Celery Task Monitor"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "backend/app/workers/celery_app.py" ]; then
    echo "❌ Please run this script from the DocuVerse root directory"
    exit 1
fi

# Check if backend environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected"
    echo "Please activate your Python virtual environment first:"
    echo "cd backend && source venv/bin/activate"
    echo ""
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo "Please start Redis first:"
    echo "docker run -d -p 6379:6379 --name redis redis:7-alpine"
    echo "or install Redis locally"
    exit 1
fi

echo "🚀 Starting Flower..."
echo "📊 Monitor will be available at: http://localhost:5555"
echo ""

cd workers
celery -A app.workers.celery_app flower --config=flower_config --port=5555 