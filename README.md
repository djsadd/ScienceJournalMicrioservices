# ScienceJournalMicrioservices

## Automatic Migrations (User Profile Service)

The `User Profile Service` now runs raw SQL migrations automatically on container start.

### How it works
1. `User Profile Service/Dockerfile` installs the PostgreSQL client.
2. On startup `run_migrations.sh` executes all `migrations/*.sql` files (sorted alphabetically) against `DATABASE_URL`.
3. After successful migration, `uvicorn` starts the API.

### Adding a new migration
Create a new file in `User Profile Service/migrations/` with a sortable name, e.g.:
```
20251201_add_new_column.sql
```
Include idempotent SQL (use `IF NOT EXISTS` where possible).

### Example migration file
```
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(8);
UPDATE user_profiles SET preferred_language='en' WHERE preferred_language IS NULL;
ALTER TABLE user_profiles ALTER COLUMN preferred_language SET NOT NULL;
```

### Rebuilding
```
docker compose build users
docker compose up users
```

If a migration fails the container exits; fix the SQL and rebuild.
