# Project Calculator

Калькулятор стоимости каркасного дома на основе FastAPI и PostgreSQL.

## Требования

- Docker и Docker Compose

## Быстрый старт

### 1. Создайте файл `.env`

Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

Файл `.env` уже содержит правильную строку подключения к БД для Docker Compose.

### 2. Запустите проект

```bash
docker-compose up -d --build
```

Эта команда:
- Создаст и запустит контейнер PostgreSQL 15 (сервис `db`)
- Соберет и запустит контейнер API (сервис `api`)
- API будет доступен по адресу: http://localhost:8000

### 3. Проверка работы

- API доступен: http://localhost:8000
- Документация Swagger: http://localhost:8000/docs
- Альтернативная документация: http://localhost:8000/redoc

## Структура проекта

```
project-calculator/
├── src/
│   ├── main.py              # Главный файл приложения FastAPI
│   ├── models.py            # SQLAlchemy модели
│   ├── schemas.py           # Pydantic схемы
│   ├── database.py          # Настройка подключения к БД
│   └── pricing_engine.py    # Движок расчетов стоимости
├── tests/                   # Тесты
├── Dockerfile               # Docker образ для API
├── docker-compose.yml       # Конфигурация Docker Compose
└── requirements.txt         # Зависимости Python
```

## Переменные окружения

- `DATABASE_URL` - строка подключения к PostgreSQL (по умолчанию: `postgresql://user:password@db:5432/mydatabase`)

## Остановка проекта

```bash
docker-compose down
```

Для удаления всех данных (включая volume с БД):

```bash
docker-compose down -v
```
