# OLKI Backend - Лендинг для сайта краски

Backend-сервис для лендинга продажи красок с использованием Django, PostgreSQL, RabbitMQ и мониторингом через Prometheus/Grafana.

## Технологии

- **Django 5.0** - веб-фреймворк
- **PostgreSQL** - база данных
- **RabbitMQ** - брокер сообщений
- **Prometheus** - сбор метрик
- **Grafana** - визуализация метрик
- **uv** - менеджер пакетов Python
- **pytest** - тестирование

## Структура проекта

```
olki-backend/
├── olki_backend/          # Основной проект Django
│   ├── settings.py        # Настройки
│   ├── urls.py            # URL маршруты
│   └── ...
├── products/              # Приложение для продукции
│   ├── models.py          # Модель Product
│   ├── views.py           # API endpoints
│   ├── serializers.py     # Сериализаторы
│   └── tests.py           # Тесты
├── contacts/              # Приложение для контактов
│   ├── models.py          # Модель ContactRequest
│   ├── views.py           # API endpoints
│   ├── management/        # Management команды
│   │   └── commands/
│   │       └── runworker.py  # RabbitMQ консьюмер
│   └── tests.py           # Тесты
├── docker-compose.yml     # Docker Compose конфигурация
├── Dockerfile             # Dockerfile для веб-сервера
├── Dockerfile.worker      # Dockerfile для воркера
└── pytest.ini            # Конфигурация pytest
```

## Требования

- Docker и Docker Compose
- Python 3.11+ (для локальной разработки)

## Быстрый старт

### Запуск через Docker Compose

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd olki-backend
```

2. Запустите все сервисы одной командой:
```bash
docker compose up
```

Это запустит:
- **Django сервер** на http://localhost:8000
- **PostgreSQL** на порту 5432
- **RabbitMQ** на порту 5672 (Management UI: http://localhost:15672)
- **Redis** на порту 6379
- **Prometheus** на http://localhost:9090
- **Grafana** на http://localhost:3000 (admin/admin)
- **Worker** (RabbitMQ консьюмер)
- **MailHog Web UI**: http://localhost:8025 - просмотр всех отправленных писем

3. Создайте суперпользователя (в другом терминале):
```bash
docker compose exec web python manage.py createsuperuser
```

4. Доступ к админ-панели: http://localhost:8000/admin
5. **Отчет о проекте**: http://localhost:8000/ - подробный отчет с описанием всех компонентов

### Локальная разработка

1. Установите зависимости:
```bash
# Установите uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установите зависимости
uv pip install -e ".[dev]"
```

2. Настройте переменные окружения:
```bash
export DATABASE_URL=postgresql://olki_user:olki_password@localhost:5432/olki_db
export RABBITMQ_URL=amqp://olki_user:olki_password@localhost:5672/
export REDIS_URL=redis://localhost:6379/0
export DJANGO_SETTINGS_MODULE=olki_backend.settings
```

3. Запустите миграции:
```bash
python manage.py migrate
```

4. Запустите сервер:
```bash
python manage.py runserver
```

5. Запустите воркер (в отдельном терминале):
```bash
python manage.py runworker
```

## API Endpoints

### Продукция

- `GET /api/products/` - список всех продуктов
- `GET /api/products/{id}/` - детали продукта
- `POST /api/products/` - создать продукт
- `PUT /api/products/{id}/` - обновить продукт
- `PATCH /api/products/{id}/` - частично обновить продукт
- `DELETE /api/products/{id}/` - удалить продукт
- `GET /api/products/featured/` - избранные продукты (первые 3)
- `GET /api/products/?search=query` - поиск продуктов

### Контакты

- `GET /api/contacts/` - список всех запросов
- `GET /api/contacts/{id}/` - детали запроса
- `POST /api/contacts/` - создать запрос на контакт (отправляет событие в RabbitMQ)
- `PUT /api/contacts/{id}/` - обновить запрос
- `PATCH /api/contacts/{id}/` - частично обновить запрос
- `DELETE /api/contacts/{id}/` - удалить запрос

### Метрики

- `GET /metrics` - метрики Prometheus

## Работа с RabbitMQ

При создании запроса на контакт через API (`POST /api/contacts/`):
1. Запрос сохраняется в БД
2. Событие отправляется в RabbitMQ очередь `email_notifications`
3. Пользователю сразу возвращается успешный ответ
4. Воркер обрабатывает событие асинхронно:
   - Отправляет письмо с благодарностью пользователю
   - Отправляет уведомление сервисным учеткам о новом запросе
   - Помечает запрос как обработанный

## Makefile команды

Проект включает Makefile для удобного управления. Просмотр всех доступных команд:

```bash
make help
```

Основные команды:

```bash
make setup           # Установить зависимости
make test            # Запустить тесты с покрытием
make test-fast       # Запустить тесты без покрытия
make coverage        # Показать отчет о покрытии в браузере
make lint            # Проверить код с помощью ruff
make format          # Форматировать код
make check           # Проверить и исправить код (lint + format)
make pre-commit      # Запустить pre-commit на всех файлах
make up              # Запустить все сервисы через docker-compose
make down            # Остановить все сервисы
make migrate         # Применить миграции
make clean           # Очистить временные файлы
make all             # Выполнить все проверки (clean, install, check, test)
```

## Тестирование

Запуск тестов:
```bash
make test
# или
pytest
```

Запуск тестов с покрытием:
```bash
make test
# или
pytest --cov=. --cov-report=term-missing --cov-report=html
```

Покрытие кода должно быть не менее 90%.

## CI/CD

Проект настроен с GitHub Actions для автоматического запуска тестов при push и pull request. CI проверяет:
- Запуск всех тестов
- Покрытие кода
- Отчет о покрытии выводится в консоль

## Мониторинг

### Prometheus
- URL: http://localhost:9090
- Собирает метрики с Django сервера через `/metrics` endpoint

### Grafana
- URL: http://localhost:3000
- Логин: `admin`
- Пароль: `admin`
- Дашборд "Django Application Metrics" будет автоматически загружен при первом запуске
- Дашборд включает:
  - HTTP Requests Rate - скорость HTTP запросов
  - HTTP Request Duration - время ответа (50th и 95th percentile)
  - Total Requests - общее количество запросов
  - Error Rate (5xx) - частота ошибок сервера
  - HTTP Status Codes - распределение по статус-кодам
  - Database Queries Rate - скорость запросов к БД

## Структура данных

### Product (Продукция)
- `id` - ID продукта
- `name` - Название
- `description` - Описание (Markdown)
- `price` - Стоимость
- `image` - Изображение
- `created_at` - Дата создания
- `updated_at` - Дата обновления

### ContactRequest (Запрос на контакт)
- `id` - ID запроса
- `name` - Имя
- `email` - Email
- `phone` - Телефон (опционально)
- `message` - Сообщение (опционально)
- `created_at` - Дата создания
- `processed` - Флаг обработки

## Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Основные переменные:

- `DATABASE_URL` - URL базы данных PostgreSQL
- `RABBITMQ_URL` - URL RabbitMQ
- `REDIS_URL` - URL Redis
- `DJANGO_SETTINGS_MODULE` - Модуль настроек Django
- `SECRET_KEY` - Секретный ключ Django
- `DEBUG` - Режим отладки (True/False)

### Настройки Email

Для тестирования используется **MailHog** (включен в docker-compose):
- `EMAIL_HOST=mailhog` - хост MailHog
- `EMAIL_PORT=1025` - SMTP порт MailHog
- `EMAIL_USE_TLS=False` - TLS не требуется
- `DEFAULT_FROM_EMAIL` - Email отправителя
- `SERVICE_EMAIL` - Email для сервисных уведомлений

## Лицензия

MIT
