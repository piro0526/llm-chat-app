#!/bin/bash

# Stop backend services

echo "🛑 Stopping backend services..."

docker compose -f docker-compose.backend.yml down

echo "✅ Backend services stopped!"
echo ""
echo "💡 To start backend services again:"
echo "   ./scripts/start-backend.sh"