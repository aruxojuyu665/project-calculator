import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from src.schemas import (
    CalculateRequestSchema, HouseSchema, CeilingSchema, RoofSchema,
    PartitionsSchema, InsulationSchema, DeliverySchema, WindowSelectionSchema,
    CalculateResponseSchema
)
from src.pricing_engine import PricingEngine
from src import models

# Mock the database session for the test
@pytest.fixture
def mock_db():
    """Fixture for a mocked SQLAlchemy Session."""
    return MagicMock(spec=Session)


def test_calculate_6x6_example_pdf(mock_db: Session):
    """
    Тест для сценария "6x6 сезонный" со страницы 31 прайса.
    Проверяет, что финальная цена до округления соответствует эталонному значению.
    
    Пример из прайса:
    - Дом 6x6 (36м2)
    - Утепление 100мм, Щитовая (panel), Izobel
    - Потолок ровный (flat), высота 2.4м
    - 2 больших окна 150х150
    - ОСБ на пол, Металлочерепица, Водосток, Обшивка цоколя рейкой
    - Доставка 140км
    - Комиссия 30000
    - Ожидаемая итоговая цена: 775 720 руб.
    """
    # 1. Создание мок-объекта CalculateRequestSchema
    mock_request = CalculateRequestSchema(
        house=HouseSchema(length_m=6.0, width_m=6.0),
        terrace=None,
        porch=None,
        ceiling=CeilingSchema(type='flat', height_m=2.4, ridge_delta_cm=0),
        roof=RoofSchema(overhang_cm='std'),
        partitions=PartitionsSchema(enabled=True, type='plain', run_m=0.0),
        insulation=InsulationSchema(brand='izobel', mm=100, build_tech='panel'),
        delivery=DeliverySchema(distance_km=140.0),
        windows=[
            WindowSelectionSchema(
                width_cm=150,
                height_cm=150,
                type='povorot_otkid',
                quantity=2,
                dual_chamber=False,
                laminated=False
            )
        ],
        addons=[],  # Допы будут мокироваться через БД
        commission_rub=30000.0
    )

    # 2. Мокирование ответов базы данных
    # Мокируем базовую цену: 16 500 руб/м² для щитовой, IZOBEL, 100мм, одноэтажный
    mock_base_price = MagicMock()
    mock_base_price.price_rub = 16500.0
    
    # Мокируем запросы к БД
    mock_query = MagicMock()
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.scalar.return_value = 16500.0
    
    mock_db.query.return_value = mock_query
    
    # Мокируем другие запросы (для допов, окон и т.д.)
    with patch.object(mock_db, 'query') as mock_query_func:
        # Базовая цена
        mock_base_query = MagicMock()
        mock_base_query.join.return_value = mock_base_query
        mock_base_query.filter.return_value = mock_base_query
        mock_base_query.scalar.return_value = 16500.0
        
        # Высота потолка (для 2.4м обычно нет доплаты, но проверим)
        mock_ceiling_query = MagicMock()
        mock_ceiling_query.filter_by.return_value.first.return_value = None
        
        # Окна
        mock_window_query = MagicMock()
        mock_window_base = MagicMock()
        mock_window_base.base_price_rub = 10000.0  # Примерная базовая цена окна
        mock_window_query.filter_by.return_value.first.return_value = mock_window_base
        
        # Модификатор окна (однокамерное, без ламинации)
        mock_modifier_query = MagicMock()
        mock_modifier = MagicMock()
        mock_modifier.multiplier = 1.0
        mock_modifier_query.filter_by.return_value.first.return_value = mock_modifier
        
        # Стандартное включение
        mock_std_inclusion_query = MagicMock()
        mock_std_inclusion = MagicMock()
        mock_std_inclusion.area_to_qty = [{"max_m2": 36, "qty": 2}, {"max_m2": 9999, "qty": 4}]
        mock_std_inclusion.included_window_width_cm = 100
        mock_std_inclusion.included_window_height_cm = 100
        mock_std_inclusion.included_window_type = 'povorot_otkid'
        mock_std_inclusion_query.join.return_value = mock_std_inclusion_query
        mock_std_inclusion_query.filter.return_value = mock_std_inclusion_query
        mock_std_inclusion_query.first.return_value = mock_std_inclusion
        
        # Настраиваем mock_query_func для возврата разных запросов
        def query_side_effect(model):
            if model == models.BasePriceM2:
                return mock_base_query
            elif model == models.CeilingHeightPrice:
                return mock_ceiling_query
            elif model == models.WindowBasePrice:
                return mock_window_query
            elif model == models.WindowModifier:
                return mock_modifier_query
            elif model == models.StdInclusion:
                return mock_std_inclusion_query
            else:
                return MagicMock()
        
        mock_query_func.side_effect = query_side_effect

        # 3. Инициализация и вызов метода
        engine = PricingEngine()
        result = engine.calculate_total(mock_db, mock_request)

        # 4. Проверка результата
        # Ожидаемая итоговая цена до округления: 775 720 руб.
        expected_total_price = 775720.0
        
        print(f"\nРассчитанная цена: {result.Итоговая_стоимость.Окончательная_цена_руб}")
        print(f"Ожидаемая цена: {expected_total_price}")
        print(f"Базовая цена: {result.Конструктив.База_руб}")
        print(f"Окна и двери: {result.Окна_и_двери.Итого_по_разделу_руб}")
        print(f"Доставка: {result.Конструктив.Доставка_руб}")
        print(f"Комиссия: {result.Итоговая_стоимость.Комиссия_руб}")
        
        # Используем Окончательная_цена_руб
        assert result.Итоговая_стоимость.Окончательная_цена_руб == expected_total_price, \
            f"Цена не совпадает: получено {result.Итоговая_стоимость.Окончательная_цена_руб}, ожидалось {expected_total_price}"

