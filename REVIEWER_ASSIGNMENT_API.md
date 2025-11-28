# Reviewer Assignment API Documentation

## Обзор
Этот документ описывает API для назначения рецензентов на статьи и управления рецензиями.

## Article Management Service

### 1. Назначить рецензентов на статью
**Endpoint:** `POST /articles/{article_id}/assign_reviewers`

**Описание:** Назначает одного или нескольких рецензентов на статью. Доступно только редакторам.

**Требования:**
- Роль: `editor`
- Авторизация: Bearer Token

**Request Body:**
```json
{
  "reviewer_ids": [1, 2, 3],
  "deadline": "2025-12-31T23:59:59Z" // optional, общий дедлайн для всех назначаемых
}
```

**Response:**
```json
{
  "message": "Reviewers assigned successfully",
  "article_id": 123,
  "reviewer_ids": [1, 2, 3]
}
```

**Процесс:**
1. Проверяет, что пользователь имеет роль `editor`
2. Проверяет существование статьи
3. Создает записи в таблице `article_reviewers` (связь многие-ко-многим)
4. Отправляет HTTP запрос в Review Service для создания записей `Review`
5. Возвращает результат

---

### 2. Получить список рецензентов статьи
**Endpoint:** `GET /articles/{article_id}/reviewers`

**Описание:** Возвращает список назначений (по рецензии): рецензент и дедлайн. Может также возвращать полную информацию по каждому рецензенту (агрегация профиля и данных аутентификации).

**Требования:**
- Роль: `editor` или автор статьи (responsible_user_id)
- Авторизация: Bearer Token

**Response:**
```json
{
  "article_id": 123,
  "reviews": [
    {
      "reviewer_id": 1,
      "deadline": "2025-12-31T23:59:59Z",
      "reviewer": {
        "id": 10,
        "user_id": 1,
        "full_name": "Ivan Petrov",
        "phone": "+7123456789",
        "organization": "Kazakh National University",
        "roles": ["reviewer"],
        "preferred_language": "ru",
        "is_active": true,
        "username": "ipetrov",
        "email": "ipetrov@knu.kz",
        "first_name": "Ivan",
        "last_name": "Petrov",
        "institution": "Kazakh National University"
      }
    },
    { "reviewer_id": 2, "deadline": null, "reviewer": { /* ... */ } },
    { "reviewer_id": 3, "deadline": "2026-01-10T12:00:00Z", "reviewer": { /* ... */ } }
  ]
}
```

Примечания:
- Данные о дедлайне берутся из Review Service (`GET /reviews/article/{article_id}`).
- Полная информация рецензента агрегируется из User Profile Service (`GET /users/{user_id}`) и Auth Service (`GET /auth/users/{user_id}`).
- При недоступности сервисов профилей/аутентификации поле `reviewer` может быть частично заполнено или `null`. При недоступности Review Service список возвращается с `deadline: null` либо пустым массивом.

---

## Review Service

### 3. Создать назначение рецензента (внутренний эндпоинт)
**Endpoint:** `POST /reviews/assign`

**Описание:** Создает запись Review при назначении рецензента. Вызывается из Article Management Service.

**Request Body:**
```json
{
  "article_id": 123,
  "reviewer_id": 1,
  "deadline": "2025-12-31T23:59:59Z" // optional
}
```

**Response:**
```json
{
  "id": 1,
  "article_id": 123,
  "reviewer_id": 1,
  "deadline": "2025-12-31T23:59:59Z",
  "status": "pending",
  "comments": null,
  "recommendation": null,
  "created_at": "2025-11-28T12:00:00Z",
  "updated_at": null
}
```

**Логика:**
- Проверяет, не существует ли уже Review для данной пары article_id/reviewer_id
- Если существует - возвращает существующую запись
- Если нет - создает новую со статусом `pending`

---

### 4. Получить мои рецензии
**Endpoint:** `GET /reviews/my-reviews`

**Описание:** Возвращает все рецензии, назначенные текущему пользователю-рецензенту.

**Требования:**
- Роль: `reviewer`
- Авторизация: Bearer Token

**Response:**
```json
[
  {
    "id": 1,
    "article_id": 123,
    "reviewer_id": 1,
    "status": "pending",
    "comments": null,
    "recommendation": null,
    "created_at": "2025-11-28T12:00:00Z",
    "updated_at": null
  },
  {
    "id": 2,
    "article_id": 456,
    "reviewer_id": 1,
    "status": "in_progress",
    "comments": "Reviewing...",
    "recommendation": null,
    "created_at": "2025-11-27T10:00:00Z",
    "updated_at": "2025-11-28T09:00:00Z"
  }
]
```

---

### 5. Получить рецензии статьи
**Endpoint:** `GET /reviews/article/{article_id}`

**Описание:** Возвращает все рецензии для конкретной статьи.

**Response:**
```json
[
  {
    "id": 1,
    "article_id": 123,
    "reviewer_id": 1,
    "status": "completed",
    "comments": "Good article",
    "recommendation": "accept",
    "created_at": "2025-11-28T12:00:00Z",
    "updated_at": "2025-11-29T15:00:00Z"
  }
]
```

---

### 6. Обновить рецензию
**Endpoint:** `PATCH /reviews/{review_id}`

**Описание:** Обновляет рецензию. Доступно только автору рецензии.

**Требования:**
- Авторизация: Bearer Token
- Пользователь должен быть автором рецензии (reviewer_id == current_user_id)

**Request Body:**
```json
{
  "article_id": 123,
  "comments": "The article needs revision",
  "recommendation": "major_revision",
  "status": "completed"
}
```

**Response:**
```json
{
  "id": 1,
  "article_id": 123,
  "reviewer_id": 1,
  "status": "completed",
  "comments": "The article needs revision",
  "recommendation": "major_revision",
  "created_at": "2025-11-28T12:00:00Z",
  "updated_at": "2025-11-29T15:00:00Z"
}
```

---

## User Profile Service

### 7. Получить список рецензентов
**Endpoint:** `GET /users/reviewers`

**Описание:** Возвращает список всех пользователей с ролью `reviewer`. Опционально фильтрует по предпочитаемому языку.

**Требования:**
- Роль: `editor`
- Авторизация: Bearer Token

**Query Parameters:**
- `language` (optional): `kz`, `ru`, или `en` — фильтрация рецензентов по предпочитаемому языку

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 5,
    "full_name": "Ivan Petrov",
    "phone": "+7123456789",
    "organization": "Kazakh National University",
    "roles": ["reviewer"],
    "preferred_language": "ru",
    "username": "ipetrov",
    "email": "ipetrov@knu.kz",
    "first_name": "Ivan",
    "last_name": "Petrov",
    "institution": "Kazakh National University",
    "is_active": true
  },
  {
    "id": 2,
    "user_id": 8,
    "full_name": "John Smith",
    "phone": null,
    "organization": "MIT",
    "roles": ["reviewer", "author"],
    "preferred_language": "en",
    "username": "jsmith",
    "email": "jsmith@mit.edu",
    "first_name": "John",
    "last_name": "Smith",
    "institution": "Massachusetts Institute of Technology",
    "is_active": true
  }
]
```

**Примеры:**
```bash
# Получить всех рецензентов
curl -X GET http://localhost:8000/users/reviewers \
  -H "Authorization: Bearer {editor_token}"

# Получить рецензентов, предпочитающих русский язык
curl -X GET "http://localhost:8000/users/reviewers?language=ru" \
  -H "Authorization: Bearer {editor_token}"
```

---

## Схемы данных

### ReviewStatus (Enum)
- `pending` - Ожидает начала рецензирования
- `in_progress` - В процессе рецензирования
- `completed` - Рецензирование завершено

### Recommendation (Enum)
- `accept` - Принять без изменений
- `minor_revision` - Принять с незначительными изменениями
- `major_revision` - Требуются существенные изменения
- `reject` - Отклонить

### Preferred Language (UserProfile)
Используется для выбора подходящих рецензентов и локализации взаимодействия.
Допустимые значения:
- `kz` – Казахский
- `ru` – Русский
- `en` – Английский

Поле хранится в сервисе профилей пользователей (`User Profile Service`) как `preferred_language`.

Пример профиля пользователя:
```json
{
  "id": 42,
  "user_id": 42,
  "full_name": "Reviewer Example",
  "roles": ["reviewer"],
  "preferred_language": "ru"
}
```

Эндпоинт обновления языка:
`PATCH /users/me/language?preferred_language=ru`

Возвращает обновлённый профиль.

---

## Примеры использования

### Пример 1: Редактор назначает рецензентов
```bash
# 1. Редактор назначает двух рецензентов на статью с ID 123
curl -X POST http://localhost:8000/articles/123/assign_reviewers \
  -H "Authorization: Bearer {editor_token}" \
  -H "Content-Type: application/json" \
  -d '{"reviewer_ids": [5, 8], "deadline": "2025-12-31T23:59:59Z"}'

# Response:
# {
#   "message": "Reviewers assigned successfully",
#   "article_id": 123,
#   "reviewer_ids": [5, 8]
# }
```

### Пример 2: Рецензент смотрит свои задания
```bash
# 2. Рецензент получает список своих назначений
curl -X GET http://localhost:8000/reviews/my-reviews \
  -H "Authorization: Bearer {reviewer_token}"

# Response:
# [
#   {
#     "id": 1,
#     "article_id": 123,
#     "reviewer_id": 5,
#     "status": "pending",
#     ...
#   }
# ]
```

### Пример 3: Рецензент обновляет свою рецензию
```bash
# 3. Рецензент добавляет комментарии и рекомендацию
curl -X PATCH http://localhost:8000/reviews/1 \
  -H "Authorization: Bearer {reviewer_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 123,
    "comments": "Well-written article with minor issues",
    "recommendation": "minor_revision",
    "status": "completed"
  }'
```

---

## Конфигурация

### Article Management Service
Добавьте в `.env`:
```
REVIEW_SERVICE_URL=http://reviews:8000
```

### Таблицы базы данных

**article_reviewers** (Article Management Service):
- `article_id` (FK -> articles.id)
- `user_id` (ID пользователя из Auth Service)

**reviews** (Review Service):
- `id` (PK)
- `article_id` (ID статьи из Article Service)
- `reviewer_id` (ID пользователя из Auth Service)
- `comments` (текст рецензии)
- `recommendation` (enum)
- `status` (enum)
- `created_at`
- `updated_at`
