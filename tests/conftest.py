import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import sys

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import models

# Используем in-memory SQLite для тестов
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def engine():
    """Создает engine для подключения к тестовой БД на всю сессию."""
    # connect_args={"check_same_thread": False} необходим для SQLite
    return create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture(scope="function")
def tables(engine):
    """
    Для каждого теста создает все таблицы в тестовой БД.
    scope="function" гарантирует, что база данных будет чистой для каждого теста.
    """
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine, tables):
    """
    Фикстура для создания сессии БД для каждого теста.
    """
    connection = engine.connect()
    # Начинаем транзакцию
    transaction = connection.begin()
    # Создаем сессию
    session = Session(bind=connection)

    yield session

    # Откатываем транзакцию и закрываем соединение
    session.close()
    transaction.rollback()
    connection.close()

