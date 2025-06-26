#!/bin/bash

# LLM Chat App Setup Script

echo "🚀 Setting up LLM Chat App..."

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
    echo "✅ .env file created. Please edit backend/.env with your settings."
fi

# Build and start services
echo "🔨 Building and starting services..."
docker compose up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run database migrations
echo "📊 Running database migrations..."
docker compose exec backend alembic upgrade head

echo "✅ Setup complete!"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "💡 Next steps:"
echo "   1. Edit backend/.env with your API keys"
echo "   2. Restart the backend: docker compose restart backend"
echo "   3. Access the application at http://localhost:3000"