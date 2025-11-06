from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Schemas for Request Body of /calculate

class HouseSchema(BaseModel):
    length_m: float = Field(..., gt=0)
    width_m: float = Field(..., gt=0)

class TerracePorchComponent(BaseModel):
    enabled: bool = False
    length_m: Optional[float] = None
    width_m: Optional[float] = None

class TerracePorchSchema(BaseModel):
    primary: Optional[TerracePorchComponent] = None
    extra: Optional[TerracePorchComponent] = None

class CeilingSchema(BaseModel):
    type: Literal['flat', 'rafters']
    height_m: Literal[2.4, 2.5, 2.6, 2.7, 2.8, 3.0]
    ridge_delta_cm: Optional[Literal[0, 10, 20, 30, 40, 50, 60]] = None

class RoofSchema(BaseModel):
    overhang_cm: Literal['std', '30', '40', '50'] = 'std'

class PartitionsSchema(BaseModel):
    enabled: bool
    type: Optional[Literal['none', 'plain', 'insul50', 'insul100']] = None
    run_m: Optional[float] = Field(None, ge=0)

class InsulationSchema(BaseModel):
    brand: Literal['izobel', 'neman_plus', 'technonicol'] = 'izobel'
    mm: Literal[100, 150, 200]
    build_tech: Literal['panel', 'frame'] = 'panel'

class DeliverySchema(BaseModel):
    distance_km: float = 100

class CalculateRequestSchema(BaseModel):
    house: HouseSchema
    terrace: Optional[TerracePorchSchema] = None
    porch: Optional[TerracePorchSchema] = None
    ceiling: CeilingSchema
    roof: RoofSchema
    partitions: PartitionsSchema
    insulation: InsulationSchema
    delivery: DeliverySchema
    commission_rub: float = Field(0, description="Комиссия агента (КП). Добавляется в финале, как в примере на стр. 31 прайса.")

# Schemas for Response Body of /calculate (200 OK)

class GabaritySchema(BaseModel):
    Площадь_теплого_контура_м2: float
    Площадь_террас_м2: float
    Площадь_крылец_м2: float
    Высота_потолка_м: float
    Тип_потолка: str
    Повышение_конька_см: int
    Вынос_крыши: str

class StandardWindowItem(BaseModel):
    Размер: str
    Тип: str
    Колво: int
    Цена_шт_руб: float
    Сумма_руб: float

class DoorItem(BaseModel):
    Наименование: str
    Колво: int
    Цена_шт_руб: float
    Сумма_руб: float

class OknaIDveriSchema(BaseModel):
    Стандартные_окна: List[StandardWindowItem]
    Двери: List[DoorItem]
    Итого_по_разделу_руб: float

class DopolneniyaItem(BaseModel):
    Код: str
    Наименование: str
    Расчёт: str
    Сумма_руб: float

class KonstruktivSchema(BaseModel):
    База_руб: float
    Дополнения: List[DopolneniyaItem]
    Доставка_руб: float

class ItogovayaStoimostSchema(BaseModel):
    Итого_без_комиссии_руб: float
    Комиссия_руб: float
    Окончательная_цена_руб: float

class CalculateResponseSchema(BaseModel):
    Габариты: GabaritySchema
    Окна_и_двери: OknaIDveriSchema
    Конструктив: KonstruktivSchema
    Итоговая_стоимость: ItogovayaStoimostSchema
