#!/bin/bash

echo "🔍 Checking backend status..."

# Check if containers are running
echo "📦 Docker containers status:"
docker compose -f docker-compose.backend.yml ps

echo ""
echo "🗄️ Database connection test:"
docker compose -f docker-compose.backend.yml exec backend python -c "
from database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
"

echo ""
echo "📊 Database tables:"
docker compose -f docker-compose.backend.yml exec backend python -c "
from database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'\"))
        tables = result.fetchall()
        if tables:
            print('Tables found:')
            for table in tables:
                print(f'  - {table[0]}')
        else:
            print('❌ No tables found. Run migrations first.')
except Exception as e:
    print(f'❌ Error checking tables: {e}')
"

echo ""
echo "🌐 API health check:"
curl -s http://localhost:8000/health || echo "❌ API not responding"

echo ""
echo "📋 Backend logs (last 10 lines):"
docker compose -f docker-compose.backend.yml logs backend --tail 10