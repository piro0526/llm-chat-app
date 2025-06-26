#!/bin/bash

echo "🗄️ Initializing database..."

# Create initial migration if it doesn't exist
echo "📝 Creating initial migration..."
docker compose -f docker-compose.backend.yml exec backend alembic revision --autogenerate -m "Initial migration"

# Apply migrations
echo "📊 Applying migrations..."
docker compose -f docker-compose.backend.yml exec backend alembic upgrade head

echo "✅ Database initialization complete!"

# Check if tables were created
echo ""
echo "🔍 Verifying tables:"
docker compose -f docker-compose.backend.yml exec backend python -c "
from database import engine
from sqlalchemy import text
try:
    with engine.connect() as conn:
        result = conn.execute(text(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'\"))
        tables = result.fetchall()
        if tables:
            print('✅ Tables created successfully:')
            for table in tables:
                print(f'  - {table[0]}')
        else:
            print('❌ No tables found.')
except Exception as e:
    print(f'❌ Error: {e}')
"