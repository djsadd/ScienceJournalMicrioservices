#!/bin/bash
set -euo pipefail

echo "[UserProfile] Running migrations..."
if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL not set" >&2
  exit 1
fi

# Apply *.sql files in migrations folder alphabetically
if [ -d migrations ]; then
  for file in $(ls migrations/*.sql 2>/dev/null | sort); do
    echo "Applying $file"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$file"
  done
else
  echo "No migrations directory found, skipping"
fi

echo "[UserProfile] Migrations complete"
