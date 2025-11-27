# Article Management Service - Database Migrations

## Автоматические миграции

Миграции применяются **автоматически** при запуске приложения. Вам не нужно ничего делать вручную!

## Ручное управление миграциями (если нужно)

### Применить миграции
```bash
alembic upgrade head
```

### Откатить последнюю миграцию
```bash
alembic downgrade -1
```

### Создать новую миграцию
```bash
alembic revision -m "description of migration"
```

### Автогенерация миграции на основе изменений в моделях
```bash
alembic revision --autogenerate -m "description"
```

### Просмотреть историю миграций
```bash
alembic history
```

### Просмотреть текущую версию БД
```bash
alembic current
```

## Существующие миграции

1. **20251126_01_add_withdrawn_status.py** - Добавляет статус 'withdrawn' в enum ArticleStatus
2. **20251126_02_add_version_code.py** - Добавляет поле version_code в таблицу article_versions

## Как это работает

При запуске приложения (в `app/main.py`) автоматически вызывается функция `run_migrations()`, которая:
1. Проверяет, какие миграции уже применены
2. Применяет новые миграции, если они есть
3. В случае ошибки откатывается к `create_all()`

Это означает, что вам **больше не нужно удалять и пересоздавать базу данных** при добавлении новых полей или enum значений!

## Добавление новых enum значений

Для PostgreSQL используйте:
```sql
ALTER TYPE enum_name ADD VALUE IF NOT EXISTS 'new_value'
```

Это безопасная операция, которая не падает, если значение уже существует.
