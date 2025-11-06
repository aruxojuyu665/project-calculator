from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from src.schemas import CalculateRequestSchema, CalculateResponseSchema
from src.database import get_db, engine
from src import models
from src.pricing_engine import PricingEngine
from src.sync_service import sync_google_sheets_to_db

# Эта строка создаст таблицы в БД при первом запуске, если их нет
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="imm0rtal | Калькулятор стоимости каркасного дома",
    version="1.1.0"
)

@app.post("/calculate", response_model=CalculateResponseSchema, summary="Рассчитать стоимость")
def calculate(request: CalculateRequestSchema, db: Session = Depends(get_db)):
    """
    Эндпоинт для расчета стоимости дома.
    
    Принимает параметры дома и возвращает детальный расчет.
    """
    engine = PricingEngine()
    response = engine.calculate_total(db, request)
    return response

@app.post("/admin/sync-prices", summary="Синхронизировать цены из Google Sheets")
def sync_prices(db: Session = Depends(get_db)):
    """
    Административный эндпоинт для синхронизации данных из Google Sheets в базу данных.
    
    Этот эндпоинт:
    1. Подключается к Google Sheets (KM_ADM_TABLE)
    2. Читает данные из следующих листов:
       - addons
       - window_base_prices
       - window_modifiers
       - doors
       - delivery_rules
    3. Очищает соответствующие таблицы в БД
    4. Загружает новые данные из Google Sheets
    
    Требуется файл gspread_credentials.json с учетными данными сервисного аккаунта Google.
    """
    try:
        sync_google_sheets_to_db(db)
        return {
            "status": "success",
            "message": "Синхронизация данных из Google Sheets завершена успешно"
        }
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка: файл учетных данных не найден. Убедитесь, что файл gspread_credentials.json существует. {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при синхронизации: {str(e)}"
        )
