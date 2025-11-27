#!/bin/bash

# Apply database migrations
echo "🔄 Applying database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi
