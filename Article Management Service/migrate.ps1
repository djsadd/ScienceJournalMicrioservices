# Apply database migrations
Write-Host "🔄 Applying database migrations..." -ForegroundColor Cyan
alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Migrations applied successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Migration failed!" -ForegroundColor Red
    exit 1
}
