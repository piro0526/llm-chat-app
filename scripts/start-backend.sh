#!/bin/bash

# Start backend services with Docker

echo "🐳 Starting backend services with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose plugin first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating .env file..."
    cp backend/.env.example backend/.env
    echo "✅ .env file created. Please edit backend/.env with your API keys."
fi

# Build and start backend services
echo "🔨 Building and starting backend services..."
docker compose -f docker-compose.backend.yml up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "📊 Running database migrations..."
echo "Creating initial migration if needed..."
docker compose -f docker-compose.backend.yml exec backend alembic revision --autogenerate -m "Initial migration" 2>/dev/null || echo "Migration already exists or error occurred"

echo "Applying migrations..."
docker compose -f docker-compose.backend.yml exec backend alembic upgrade head

echo "✅ Backend services started!"
echo ""
echo "🌐 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🗄️ PostgreSQL: localhost:5432"
echo ""
echo "💡 To start frontend locally:"
echo "   cd frontend"
echo "   npm install"
echo "   npm run dev"
echo ""
echo "🛑 To stop backend services:"
echo "   docker compose -f docker-compose.backend.yml down"