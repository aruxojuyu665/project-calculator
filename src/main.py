from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from src.schemas import CalculateRequestSchema, CalculateResponseSchema
from src.database import get_db, engine
from src import models
from src.pricing_engine import PricingEngine

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
