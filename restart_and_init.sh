#!/bin/bash

# Скрипт полного перезапуска и инициализации

echo "========================================="
echo "ПОЛНЫЙ ПЕРЕЗАПУСК КАЛЬКУЛЯТОРА"
echo "========================================="

# 1. Остановка контейнеров
echo ""
echo "1. Остановка контейнеров..."
docker compose down

# 2. Пересборка образов
echo ""
echo "2. Пересборка образов (применение новых изменений)..."
docker compose build --no-cache

# 3. Запуск контейнеров
echo ""
echo "3. Запуск контейнеров..."
docker compose up -d

# 4. Ожидание запуска БД
echo ""
echo "4. Ожидание запуска базы данных..."
sleep 10

# 5. Инициализация БД
echo ""
echo "5. Инициализация базы данных..."
docker compose exec calculator_api python init_database.py

# 6. Проверка статуса
echo ""
echo "6. Проверка статуса контейнеров..."
docker compose ps

echo ""
echo "========================================="
echo "✓ ПЕРЕЗАПУСК ЗАВЕРШЕН!"
echo "========================================="
echo ""
echo "Следующие шаги:"
echo "1. Проверьте логи: docker compose logs -f calculator_api"
echo "2. Запустите синхронизацию: curl -X POST http://localhost:8000/admin/sync-prices"
echo "3. Проверьте API: curl http://localhost:8000/docs"
echo ""
