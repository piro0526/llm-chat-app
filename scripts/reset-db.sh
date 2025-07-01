#!/bin/bash

# Database reset script for development
# This script stops containers, removes volumes, and creates fresh migrations

set -e

echo "🔄 Resetting database and migrations..."

# Stop and remove containers
echo "📦 Stopping Docker containers..."
docker compose -f docker-compose.backend.yml down -v

# Remove migration files (keeping the directory)
echo "🗑️  Removing old migration files..."
rm -f backend/alembic/versions/*.py
rm -rf backend/alembic/versions/__pycache__ 2>/dev/null || true

# Create fresh initial migration
echo "📝 Creating new initial migration..."
cd backend
python -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:password@localhost:5432/llm_chat_app'
os.system('alembic revision --autogenerate -m \"initial_migration\"')
"
cd ..

echo "🚀 Starting services..."
docker compose -f docker-compose.backend.yml up --build -d

echo "✅ Database reset complete!"
echo "🔍 Check logs with: docker compose -f docker-compose.backend.yml logs -f"