# Инструкция по обновлению БД

## Шаги для применения миграции

### 1. Остановите сервисы (если они запущены)
```powershell
docker-compose down
```

### 2. Примените миграцию базы данных

#### Вариант A: Если используете Docker
```powershell
docker-compose up -d postgres
docker-compose run article_management alembic upgrade head
```

#### Вариант B: Локальная разработка
```powershell
cd "Article Management Service"
alembic upgrade head
```

### 3. Проверьте применение миграции
```powershell
alembic current
```

Должна быть версия: `f02b17fc7620 (head)`

### 4. Запустите сервисы
```powershell
docker-compose up -d
```

## Проверка работы

### Проверка структуры БД
Подключитесь к PostgreSQL и проверьте:
```sql
-- Проверка новых колонок в article_versions
\d article_versions

-- Проверка таблиц связей
\d article_version_authors
\d article_version_keywords

-- Проверка данных
SELECT id, version_number, title_en, article_type FROM article_versions LIMIT 5;
```

### Тестирование API
```bash
# Создание статьи
POST /articles/
{
  "title_kz": "Тест",
  "title_en": "Test",
  "title_ru": "Тест",
  ...
}

# Обновление статьи (автоматически создаст версию)
PUT /articles/1
{
  "title_en": "Updated Test"
}

# Получение статьи с версиями
GET /articles/my/1
```

## Откат (если нужен)

Если что-то пошло не так:
```powershell
alembic downgrade -1
```

⚠️ **Внимание:** Откат удалит данные из новых полей версий!

## Возможные проблемы

### Ошибка: "column already exists"
Решение: Проверьте, не применена ли миграция уже
```powershell
alembic current
alembic history
```

### Ошибка: "NOT NULL constraint failed"
Решение: Убедитесь, что в БД есть статьи с заполненными обязательными полями
