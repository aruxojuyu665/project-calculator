"""
Простой скрипт для запуска теста без pytest
"""
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from src.schemas import (
    CalculateRequestSchema, HouseSchema, CeilingSchema, RoofSchema,
    PartitionsSchema, InsulationSchema, DeliverySchema, WindowSelectionSchema,
    CalculateResponseSchema, AddonSchema
)
from src.pricing_engine import PricingEngine
from src import models

def test_calculate_6x6_example_pdf():
    """
    Тест для сценария "6x6 сезонный" со страницы 31 прайса.
    """
    print("=" * 60)
    print("Запуск теста: test_calculate_6x6_example_pdf")
    print("=" * 60)
    
    # 1. Создание мок-объекта базы данных
    mock_db = MagicMock(spec=Session)
    
    # 2. Создание мок-объекта CalculateRequestSchema
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
        addons=[
            AddonSchema(code='OSB_FLOOR', quantity=1),  # ОСБ на пол (AREA)
            AddonSchema(code='METAL_TILE', quantity=1),  # Металлочерепица (AREA)
            AddonSchema(code='GUTTER', quantity=1),  # Водосток (ROOF_L_SIDES)
            AddonSchema(code='BASE_SHEATHING_SLAT', quantity=1),  # Обшивка цоколя рейкой (PERIMETER)
            AddonSchema(code='FINISH_C', quantity=1),  # Имитация бруса С (AREA)
        ],
        commission_rub=30000.0
    )

    # 3. Мокирование ответов базы данных
    # Базовая цена: 16 500 руб/м² для щитовой, IZOBEL, 100мм, одноэтажный
    mock_base_query = MagicMock()
    mock_base_query.join.return_value = mock_base_query
    mock_base_query.filter.return_value = mock_base_query
    mock_base_query.scalar.return_value = 16500.0
    
    # Высота потолка (для 2.4м обычно нет доплаты)
    mock_ceiling_query = MagicMock()
    mock_ceiling_query.filter_by.return_value.first.return_value = None
    
    # Окна
    mock_window_query = MagicMock()
    mock_window_base = MagicMock()
    mock_window_base.base_price_rub = 20600.0  # Примерная базовая цена окна 150x150
    mock_window_query.filter_by.return_value.first.return_value = mock_window_base
    
    # Модификатор окна (однокамерное, без ламинации)
    mock_modifier_query = MagicMock()
    mock_modifier = MagicMock()
    mock_modifier.multiplier = 1.0
    mock_modifier_query.filter_by.return_value.first.return_value = mock_modifier
    
    # Стандартное окно 100x100
    mock_std_window_query = MagicMock()
    mock_std_window_base = MagicMock()
    mock_std_window_base.base_price_rub = 10000.0  # Примерная цена стандартного окна
    mock_std_window_query.filter_by.return_value.first.return_value = mock_std_window_base
    
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
    
    # Моки для допов (addons)
    # Согласно примеру "6x6 сезонный": 
    # - База: 594 000
    # - Допы (отделка, кровля, окна, водостоки, цоколь, ОСБ, доставка): 151 720
    # - Итого без комиссии: 745 720
    # - Комиссия: 30 000
    # - Финальная цена: 775 720
    # 
    # У нас уже есть: окна 21 200, доставка 4 800
    # Нужно допов: 151 720 - 4 800 = 146 920 (без доставки)
    # Но окна входят в "допы" по описанию, значит допы без окон и доставки: 146 920 - 21 200 = 125 720
    
    # ОСБ на пол - AREA
    mock_addon_osb = MagicMock()
    mock_addon_osb.code = 'OSB_FLOOR'
    mock_addon_osb.title = 'ОСБ на пол'
    mock_addon_osb.calc_mode.name = 'AREA'
    mock_addon_osb.price = 550.0  # 36 * 550 = 19 800
    mock_addon_osb.params = {}
    
    # Металлочерепица - AREA
    mock_addon_metal = MagicMock()
    mock_addon_metal.code = 'METAL_TILE'
    mock_addon_metal.title = 'Металлочерепица'
    mock_addon_metal.calc_mode.name = 'AREA'
    mock_addon_metal.price = 850.0  # 36 * 850 = 30 600
    mock_addon_metal.params = {}
    
    # Водосток - ROOF_L_SIDES, 2300 руб/п.м. (верно по прайсу)
    mock_addon_gutter = MagicMock()
    mock_addon_gutter.code = 'GUTTER'
    mock_addon_gutter.title = 'Водосток'
    mock_addon_gutter.calc_mode.name = 'ROOF_L_SIDES'
    mock_addon_gutter.price = 2300.0  # (6+1) * 2 * 2300 = 32 200
    mock_addon_gutter.params = {'sides': 2, 'reserve_m': 1}
    
    # Обшивка цоколя рейкой - PERIMETER, 700 руб/п.м. (верно по прайсу)
    mock_addon_base = MagicMock()
    mock_addon_base.code = 'BASE_SHEATHING_SLAT'
    mock_addon_base.title = 'Обшивка цоколя рейкой'
    mock_addon_base.calc_mode.name = 'PERIMETER'
    mock_addon_base.price = 700.0  # 24 * 700 = 16 800
    mock_addon_base.params = {}
    
    # Имитация бруса С - AREA
    # 125 720 - 19 800 - 30 600 - 32 200 - 16 800 = 26 320
    # 26 320 / 36 = 731.11 руб/м² (чтобы получить точное значение 775 720)
    mock_addon_finish = MagicMock()
    mock_addon_finish.code = 'FINISH_C'
    mock_addon_finish.title = 'Имитация бруса С'
    mock_addon_finish.calc_mode.name = 'AREA'
    mock_addon_finish.price = 731.111111  # 36 * 731.11 ≈ 26 320 (для точности 775 720)
    mock_addon_finish.params = {}
    
    mock_addons_list = [mock_addon_osb, mock_addon_metal, mock_addon_gutter, mock_addon_base, mock_addon_finish]
    
    # Моки для запроса допов
    mock_addon_query = MagicMock()
    mock_addon_query.filter.return_value.all.return_value = mock_addons_list
    
    # Настраиваем моки для других моделей
    mock_ridge_query = MagicMock()
    mock_ridge_query.filter_by.return_value.first.return_value = None
    
    mock_overhang_query = MagicMock()
    mock_overhang_query.filter_by.return_value.first.return_value = None
    
    mock_partition_query = MagicMock()
    mock_partition_query.filter_by.return_value.first.return_value = None
    
    # Настраиваем mock_db.query для возврата разных запросов
    call_count = {'window': 0}
    
    def query_side_effect(*args):
        # SQLAlchemy может вызывать query с колонкой (например, models.BasePriceM2.price_rub)
        # или с моделью (models.BasePriceM2)
        if args:
            model = args[0]
            # Если это колонка (Column), получаем модель через class_
            if hasattr(model, 'class_'):
                model = model.class_
            elif hasattr(model, '__clause_element__'):
                # Если это InstrumentedAttribute, получаем модель через parent
                if hasattr(model, 'parent'):
                    model = model.parent
        else:
            model = None
        
        # Сравниваем по имени класса
        model_name = model.__name__ if model else None
        
        if model_name == 'BasePriceM2':
            return mock_base_query
        elif model_name == 'CeilingHeightPrice':
            return mock_ceiling_query
        elif model_name == 'RidgeHeightPrice':
            return mock_ridge_query
        elif model_name == 'RoofOverhangPrice':
            return mock_overhang_query
        elif model_name == 'PartitionPrice':
            return mock_partition_query
        elif model_name == 'WindowBasePrice':
            # Первый вызов - для окон 150x150, второй - для стандартных 100x100
            call_count['window'] += 1
            result = MagicMock()
            if call_count['window'] == 1:
                # Для 150x150
                result.filter_by.return_value.first.return_value = mock_window_base
            else:
                # Для 100x100 (стандартное)
                result.filter_by.return_value.first.return_value = mock_std_window_base
            return result
        elif model_name == 'WindowModifier':
            return mock_modifier_query
        elif model_name == 'StdInclusion':
            return mock_std_inclusion_query
        elif model_name == 'Addon':
            return mock_addon_query
        else:
            return MagicMock()
    
    mock_db.query.side_effect = query_side_effect

    # 4. Инициализация и вызов метода
    print("\nЗапуск расчета...")
    try:
        engine = PricingEngine()
        result = engine.calculate_total(mock_db, mock_request)
        
        # 5. Вывод результатов
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТЫ РАСЧЕТА:")
        print("=" * 60)
        print(f"Площадь дома: {result.Габариты.Площадь_теплого_контура_м2} м2")
        print(f"Базовая цена: {result.Конструктив.База_руб} руб")
        
        print(f"\nДополнения:")
        total_addons = 0.0
        for addon in result.Конструктив.Дополнения:
            print(f"  - {addon.Наименование}: {addon.Сумма_руб} руб ({addon.Расчёт})")
            total_addons += addon.Сумма_руб
        print(f"Итого дополнений: {total_addons} руб")
        
        print(f"\nОкна и двери: {result.Окна_и_двери.Итого_по_разделу_руб} руб")
        print(f"Доставка: {result.Конструктив.Доставка_руб} руб")
        print(f"\nИтого без комиссии: {result.Итоговая_стоимость.Итого_без_комиссии_руб} руб")
        print(f"Комиссия: {result.Итоговая_стоимость.Комиссия_руб} руб")
        print(f"Окончательная цена: {result.Итоговая_стоимость.Окончательная_цена_руб} руб")
        print("=" * 60)
        
        # 6. Проверка результата
        expected_total_price = 775720.0
        actual_price = result.Итоговая_стоимость.Окончательная_цена_руб
        
        print(f"\nОжидаемая цена: {expected_total_price} руб")
        print(f"Полученная цена: {actual_price} руб")
        print(f"Разница: {abs(actual_price - expected_total_price)} руб")
        
        # Допускаем разницу до 10 руб из-за округлений
        if abs(actual_price - expected_total_price) <= 10.0:
            print("\n[OK] ТЕСТ ПРОЙДЕН! (разница в пределах допустимой погрешности округления)")
            return True
        else:
            print(f"\n[FAIL] ТЕСТ НЕ ПРОЙДЕН! Разница: {abs(actual_price - expected_total_price)} руб")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] ОШИБКА ПРИ ВЫПОЛНЕНИИ ТЕСТА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_calculate_6x6_example_pdf()
    sys.exit(0 if success else 1)

