# API Документация: Список неназначенных статей и детальная страница для редактора

## Эндпоинт: Список неназначенных статей
```
GET /articles/unassigned
```

## Описание
Возвращает список статей, которые еще не назначены редакторам, с поддержкой фильтрации и пагинации.

## Требования
- **Аутентификация**: Требуется Bearer токен
- **Роль**: `editor` (только редакторы имеют доступ)

## Параметры запроса (Query Parameters)

### Фильтрация

| Параметр | Тип | Обязательный | Описание | Пример |
|----------|-----|--------------|----------|---------|
| `status` | string | Нет | Статус статьи. Если не указан, показываются только `submitted` | `submitted`, `under_review`, `accepted`, `published`, `withdrawn`, `draft` |
| `author_name` | string | Нет | Поиск по имени автора (поддерживает частичное совпадение по имени, фамилии, отчеству) | `Иванов`, `John` |
| `year` | integer | Нет | Год создания статьи | `2024`, `2025` |
| `article_type` | string | Нет | Тип статьи | `original`, `review` |
| `keywords` | string | Нет | Ключевые слова через запятую (поиск по любому из указанных) | `медицина, биология` |
| `search` | string | Нет | Общий поиск по заголовку и аннотации на всех языках (kz, en, ru) | `COVID-19` |

### Пагинация

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `page` | integer | Нет | 1 | Номер страницы (начинается с 1) |
| `page_size` | integer | Нет | 10 | Количество элементов на странице (от 1 до 100) |

## Примеры запросов

### 1. Базовый запрос (все неназначенные статьи)
```bash
GET /articles/unassigned
Authorization: Bearer <token>
```

### 2. С пагинацией (вторая страница, по 20 элементов)
```bash
GET /articles/unassigned?page=2&page_size=20
Authorization: Bearer <token>
```

### 3. Фильтр по автору
```bash
GET /articles/unassigned?author_name=Иванов
Authorization: Bearer <token>
```

### 4. Фильтр по году и типу статьи
```bash
GET /articles/unassigned?year=2025&article_type=original
Authorization: Bearer <token>
```

### 5. Поиск по ключевым словам
```bash
GET /articles/unassigned?keywords=медицина,биология
Authorization: Bearer <token>
```

### 6. Общий поиск по тексту
```bash
GET /articles/unassigned?search=COVID-19
Authorization: Bearer <token>
```

### 7. Комплексный запрос с несколькими фильтрами
```bash
GET /articles/unassigned?status=submitted&year=2025&article_type=original&search=исследование&page=1&page_size=15
Authorization: Bearer <token>
```

## Структура ответа

```json
{
  "items": [
    {
      "id": 1,
      "title_kz": "Заголовок на казахском",
      "title_en": "Title in English",
      "title_ru": "Заголовок на русском",
      "abstract_kz": "Аннотация на казахском",
      "abstract_en": "Abstract in English",
      "abstract_ru": "Аннотация на русском",
      "doi": "10.1234/example.2025.001",
      "status": "submitted",
      "article_type": "original",
      "responsible_user_id": 123,
      "manuscript_file_url": "/files/abc123/download",
      "antiplagiarism_file_url": "/files/def456/download",
      "author_info_file_url": "/files/ghi789/download",
      "cover_letter_file_url": "/files/jkl012/download",
      "not_published_elsewhere": true,
      "plagiarism_free": true,
      "authors_agree": true,
      "generative_ai_info": "Not used",
      "created_at": "2025-11-15T10:30:00Z",
      "updated_at": "2025-11-16T14:20:00Z",
      "current_version_id": 5,
      "authors": [
        {
          "id": 1,
          "email": "author@example.com",
          "prefix": "Dr.",
          "first_name": "Иван",
          "patronymic": "Иванович",
          "last_name": "Иванов",
          "phone": "+7 777 123 4567",
          "address": "Алматы, ул. Примерная 1",
          "country": "Казахстан",
          "affiliation1": "КазНУ",
          "affiliation2": null,
          "affiliation3": null,
          "is_corresponding": true,
          "orcid": "0000-0001-2345-6789",
          "scopus_author_id": "12345678900",
          "researcher_id": "A-1234-2025"
        }
      ],
      "keywords": [
        {
          "id": 1,
          "title_kz": "медицина",
          "title_en": "medicine",
          "title_ru": "медицина"
        },
        {
          "id": 2,
          "title_kz": "зерттеу",
          "title_en": "research",
          "title_ru": "исследование"
        }
      ],
      "versions": []
    }
  ],
  "pagination": {
    "total_count": 45,
    "page": 1,
    "page_size": 10,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

## Поля ответа

### Объект `items` (массив статей)
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer | ID статьи |
| `title_kz` / `title_en` / `title_ru` | string | Заголовок на разных языках |
| `abstract_kz` / `abstract_en` / `abstract_ru` | string | Аннотация на разных языках |
| `doi` | string | DOI статьи |
| `status` | string | Статус статьи |
| `article_type` | string | Тип статьи (`original` или `review`) |
| `responsible_user_id` | integer | ID ответственного автора |
| `manuscript_file_url` | string | Ссылка на рукопись |
| `antiplagiarism_file_url` | string | Ссылка на файл проверки антиплагиата |
| `author_info_file_url` | string | Ссылка на информацию об авторах |
| `cover_letter_file_url` | string | Ссылка на сопроводительное письмо |
| `not_published_elsewhere` | boolean | Не опубликовано ранее |
| `plagiarism_free` | boolean | Отсутствие плагиата |
| `authors_agree` | boolean | Согласие всех авторов |
| `generative_ai_info` | string | Информация об использовании ИИ |
| `created_at` | datetime | Дата создания |
| `updated_at` | datetime | Дата обновления |
| `current_version_id` | integer | ID текущей версии |
| `authors` | array | Массив авторов статьи |
| `keywords` | array | Массив ключевых слов |
| `versions` | array | Массив версий статьи |

### Объект `pagination`
| Поле | Тип | Описание |
|------|-----|----------|
| `total_count` | integer | Общее количество статей (с учетом фильтров) |
| `page` | integer | Текущая страница |
| `page_size` | integer | Размер страницы |
| `total_pages` | integer | Общее количество страниц |
| `has_next` | boolean | Есть ли следующая страница |
| `has_prev` | boolean | Есть ли предыдущая страница |

## Коды ответов

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Некорректные параметры запроса |
| 401 | Не авторизован (неверный или отсутствующий токен) |
| 403 | Доступ запрещен (требуется роль editor) |

## Примеры ошибок

### 400 Bad Request
```json
{
  "detail": "Invalid status: invalid_status"
}
```

```json
{
  "detail": "Page must be >= 1"
}
```

```json
{
  "detail": "Page size must be between 1 and 100"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid token"
}
```

### 403 Forbidden
```json
{
  "detail": "Editor role required"
}
```

---

## Эндпоинт: Детальная страница рукописи для редактора
```
GET /articles/editor/{article_id}
```

## Описание
Возвращает детальную информацию о рукописи для редактора. Включает полные данные статьи, информацию об авторах, ключевые слова и все версии рукописи.

## Требования
- **Аутентификация**: Требуется Bearer токен
- **Роль**: `editor` (только редакторы имеют доступ)

## Параметры пути (Path Parameters)

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `article_id` | integer | Да | ID статьи/рукописи |

## Примеры запросов

### Получить детальную информацию о рукописи
```bash
GET /articles/editor/123
Authorization: Bearer <token>
```

## Ответ

### Успешный ответ (200 OK)
```json
{
  "id": 123,
  "title_kz": "Заголовок на казахском",
  "title_en": "Title in English",
  "title_ru": "Заголовок на русском",
  "abstract_kz": "Аннотация на казахском...",
  "abstract_en": "Abstract in English...",
  "abstract_ru": "Аннотация на русском...",
  "doi": "10.1234/example.2024.001",
  "status": "submitted",
  "article_type": "original",
  "responsible_user_id": 456,
  "antiplagiarism_file_url": "/files/abc123/download",
  "not_published_elsewhere": true,
  "plagiarism_free": true,
  "authors_agree": true,
  "generative_ai_info": "Использован ChatGPT для редактирования текста",
  "manuscript_file_url": "/files/xyz789/download",
  "author_info_file_url": "/files/def456/download",
  "cover_letter_file_url": "/files/ghi789/download",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:20:00Z",
  "authors": [
    {
      "id": 1,
      "email": "author@example.com",
      "prefix": "Dr.",
      "first_name": "Иван",
      "patronymic": "Иванович",
      "last_name": "Иванов",
      "phone": "+7-777-123-4567",
      "address": "ул. Примерная, 123",
      "country": "Kazakhstan",
      "affiliation1": "Казахский Национальный Университет",
      "affiliation2": "Институт Биологии",
      "affiliation3": null,
      "is_corresponding": true,
      "orcid": "0000-0001-2345-6789",
      "scopus_author_id": "12345678900",
      "researcher_id": "A-1234-2024"
    }
  ],
  "keywords": [
    {
      "id": 1,
      "title_kz": "Медицина",
      "title_en": "Medicine",
      "title_ru": "Медицина"
    },
    {
      "id": 2,
      "title_kz": "Биология",
      "title_en": "Biology",
      "title_ru": "Биология"
    }
  ],
  "versions": [
    {
      "id": 1,
      "article_id": 123,
      "version_number": 1,
      "version_code": "v1.0",
      "title_kz": "Заголовок на казахском",
      "title_en": "Title in English",
      "title_ru": "Заголовок на русском",
      "abstract_kz": "Аннотация на казахском...",
      "abstract_en": "Abstract in English...",
      "abstract_ru": "Аннотация на русском...",
      "doi": null,
      "article_type": "original",
      "manuscript_file_url": "/files/xyz789/download",
      "antiplagiarism_file_url": "/files/abc123/download",
      "author_info_file_url": "/files/def456/download",
      "cover_letter_file_url": "/files/ghi789/download",
      "not_published_elsewhere": true,
      "plagiarism_free": true,
      "authors_agree": true,
      "generative_ai_info": null,
      "file_url": "/files/xyz789/download",
      "created_at": "2024-01-15T10:30:00Z",
      "is_published": false,
      "authors": [
        {
          "id": 1,
          "email": "author@example.com",
          "prefix": "Dr.",
          "first_name": "Иван",
          "patronymic": "Иванович",
          "last_name": "Иванов",
          "phone": "+7-777-123-4567",
          "address": "ул. Примерная, 123",
          "country": "Kazakhstan",
          "affiliation1": "Казахский Национальный Университет",
          "affiliation2": "Институт Биологии",
          "affiliation3": null,
          "is_corresponding": true,
          "orcid": "0000-0001-2345-6789",
          "scopus_author_id": "12345678900",
          "researcher_id": "A-1234-2024"
        }
      ],
      "keywords": [
        {
          "id": 1,
          "title_kz": "Медицина",
          "title_en": "Medicine",
          "title_ru": "Медицина"
        }
      ]
    }
  ]
}
```

### Ошибки

#### Статья не найдена (404 Not Found)
```json
{
  "detail": "Article not found"
}
```

#### Отсутствует токен (401 Unauthorized)
```json
{
  "detail": "Invalid token"
}
```

#### Недостаточно прав (403 Forbidden)
```json
{
  "detail": "Editor role required"
}
```

## Отличия от эндпоинта автора

| Аспект | Эндпоинт автора (`/articles/my/{article_id}`) | Эндпоинт редактора (`/articles/editor/{article_id}`) |
|--------|-----------------------------------------------|-----------------------------------------------------|
| **Роль** | Автор (author) | Редактор (editor) |
| **Проверка доступа** | Только ответственный пользователь (responsible_user_id) | Любой редактор |
| **Назначение** | Личный кабинет автора | Административная панель редактора |
| **Данные** | Идентичные | Идентичные |

---

## Рекомендации по использованию

1. **Пагинация**: Всегда используйте пагинацию для больших списков. Оптимальный размер страницы - 10-20 элементов.

2. **Фильтры**: Комбинируйте фильтры для более точного поиска. Все фильтры работают с логическим AND (И).

3. **Поиск**: Параметр `search` ищет по всем языковым версиям заголовка и аннотации одновременно.

4. **Ключевые слова**: При фильтрации по ключевым словам используйте запятую без пробелов или с пробелами - оба варианта работают.

5. **Кэширование**: Рекомендуется кэшировать результаты на короткое время (30-60 секунд) для уменьшения нагрузки на сервер.

6. **Обработка ошибок**: Всегда обрабатывайте ошибки 400, 401, 403 и показывайте пользователю понятные сообщения.

7. **Статус по умолчанию**: Если не указан параметр `status`, API возвращает только статьи со статусом `submitted`.

8. **Детальная страница**: Используйте эндпоинт `/articles/editor/{article_id}` для получения полной информации о рукописи, включая все версии и файлы.

