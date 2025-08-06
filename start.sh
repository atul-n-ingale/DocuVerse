#!/bin/bash

echo "🚀 Starting DocuVerse - Document Universe"
echo "=========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy env.example to .env and configure your API keys:"
    echo "cp env.example .env"
    echo ""
    echo "Required environment variables:"
    echo "- OPENAI_API_KEY"
    echo "- PINECONE_API_KEY"
    echo "- PINECONE_ENVIRONMENT"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

# Create uploads directory if it doesn't exist
mkdir -p uploads

echo "📦 Building and starting services..."
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."

if docker-compose ps | grep -q "Up"; then
    echo "✅ All services are running!"
    echo ""
    echo "🌐 Access your application:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Flower (Celery Monitor): http://localhost:5555"
    echo ""
    echo "📊 Monitor services:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 To stop services:"
    echo "   docker-compose down"
else
    echo "❌ Some services failed to start!"
    echo "Check logs with: docker-compose logs"
    exit 1
fi 