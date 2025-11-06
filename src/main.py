from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from src.schemas import CalculateRequestSchema, CalculateResponseSchema
from src.database import get_db, engine
from src import models

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
    # Временный моковый ответ для демонстрации
    mock_response = {
        "Габариты": {
            "Площадь_теплого_контура_м2": request.house.length_m * request.house.width_m,
            "Площадь_террас_м2": 0.0,
            "Площадь_крылец_м2": 0.0,
            "Высота_потолка_м": request.ceiling.height_m,
            "Тип_потолка": request.ceiling.type,
            "Повышение_конька_см": request.ceiling.ridge_delta_cm or 0,
            "Вынос_крыши": request.roof.overhang_cm
        },
        "Окна_и_двери": {
            "Стандартные_окна": [
                {
                    "Размер": "100x100", "Тип": "povorot_otkid", "Колво": 4,
                    "Цена_шт_руб": 15000.0, "Сумма_руб": 60000.0
                }
            ],
            "Двери": [
                {
                    "Наименование": "Входная дверь", "Колво": 1,
                    "Цена_шт_руб": 25000.0, "Сумма_руб": 25000.0
                }
            ],
            "Итого_по_разделу_руб": 85000.0
        },
        "Конструктив": {
            "База_руб": 1500000.0,
            "Дополнения": [
                {
                    "Код": "ROOF-01", "Наименование": "Утепление крыши",
                    "Расчёт": "100.5 м2 * 500 руб/м2", "Сумма_руб": 50250.0
                }
            ],
            "Доставка_руб": 10000.0
        },
        "Итоговая_стоимость": {
            "Итого_без_комиссии_руб": 1645250.0,
            "Комиссия_руб": request.commission_rub,
            "Окончательная_цена_руб": 1645250.0 + request.commission_rub
        }
    }
    return CalculateResponseSchema.parse_obj(mock_response)
