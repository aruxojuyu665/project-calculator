"""
Скрипт инициализации базы данных для калькулятора

Этот скрипт:
1. Создает все справочные таблицы
2. Заполняет их тестовыми данными
3. Создает базовые цены для всех комбинаций параметров
4. Проверяет корректность данных

Запуск: python init_database.py
"""

import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

# Импортируем модели
from src import models
from src.database import engine, SessionLocal

def clear_all_tables(db):
    """Очищает все таблицы в правильном порядке (учитывая FK)"""
    print("Очистка всех таблиц...")

    # Сначала зависимые таблицы
    db.query(models.BasePriceM2).delete()
    db.query(models.StdInclusion).delete()
    db.query(models.GlobalDefault).delete()

    # Потом таблицы с ценами
    db.query(models.CeilingHeightPrice).delete()
    db.query(models.RidgeHeightPrice).delete()
    db.query(models.RoofOverhangPrice).delete()
    db.query(models.PartitionPrice).delete()
    db.query(models.Addon).delete()
    db.query(models.WindowBasePrice).delete()
    db.query(models.WindowModifier).delete()
    db.query(models.Door).delete()
    db.query(models.DoorAccessory).delete()
    db.query(models.DeliveryRule).delete()

    # Потом справочные таблицы
    db.query(models.BuildTechnology).delete()
    db.query(models.Contour).delete()
    db.query(models.InsulationBrand).delete()
    db.query(models.InsulationThickness).delete()
    db.query(models.StoreyType).delete()

    db.commit()
    print("✓ Все таблицы очищены")

def init_reference_tables(db):
    """Инициализирует справочные таблицы"""
    print("\nИнициализация справочных таблиц...")

    # Технологии строительства
    tech_panel = models.BuildTechnology(code='panel', title='Панельная технология')
    tech_frame = models.BuildTechnology(code='frame', title='Каркасная технология')
    db.add_all([tech_panel, tech_frame])
    db.commit()
    print("✓ Технологии строительства: 2 записи")

    # Контуры
    contour_warm = models.Contour(code='warm', title='Тёплый контур')
    contour_cold = models.Contour(code='cold', title='Холодный контур')
    db.add_all([contour_warm, contour_cold])
    db.commit()
    print("✓ Контуры: 2 записи")

    # Типы этажности
    storey_one = models.StoreyType(code='one', title='Одноэтажный')
    storey_mansard = models.StoreyType(code='mansard', title='Мансардный')
    storey_two = models.StoreyType(code='two', title='Двухэтажный')
    db.add_all([storey_one, storey_mansard, storey_two])
    db.commit()
    print("✓ Типы этажности: 3 записи")

    # Марки утеплителя
    brand_izobel = models.InsulationBrand(code='izobel', title='Изобел')
    brand_neman = models.InsulationBrand(code='neman_plus', title='Неман+')
    brand_techno = models.InsulationBrand(code='technonicol', title='Технониколь')
    db.add_all([brand_izobel, brand_neman, brand_techno])
    db.commit()
    print("✓ Марки утеплителя: 3 записи")

    # Толщины утеплителя
    thick_100 = models.InsulationThickness(mm=100)
    thick_150 = models.InsulationThickness(mm=150)
    thick_200 = models.InsulationThickness(mm=200)
    db.add_all([thick_100, thick_150, thick_200])
    db.commit()
    print("✓ Толщины утеплителя: 3 записи")

    return {
        'techs': [tech_panel, tech_frame],
        'contours': [contour_warm, contour_cold],
        'storey_types': [storey_one, storey_mansard, storey_two],
        'brands': [brand_izobel, brand_neman, brand_techno],
        'thicknesses': [thick_100, thick_150, thick_200]
    }

def init_base_prices(db, refs):
    """Инициализирует базовые цены для всех комбинаций"""
    print("\nИнициализация базовых цен...")

    # Базовые цены для разных комбинаций
    base_prices = [
        # panel + warm + izobel
        {'tech': 'panel', 'contour': 'warm', 'brand': 'izobel', 'thick': 100, 'storey': 'one', 'price': 10000},
        {'tech': 'panel', 'contour': 'warm', 'brand': 'izobel', 'thick': 150, 'storey': 'one', 'price': 12000},
        {'tech': 'panel', 'contour': 'warm', 'brand': 'izobel', 'thick': 200, 'storey': 'mansard', 'price': 15000},

        # panel + warm + neman_plus
        {'tech': 'panel', 'contour': 'warm', 'brand': 'neman_plus', 'thick': 100, 'storey': 'one', 'price': 10500},
        {'tech': 'panel', 'contour': 'warm', 'brand': 'neman_plus', 'thick': 150, 'storey': 'one', 'price': 12500},

        # frame + warm + technonicol
        {'tech': 'frame', 'contour': 'warm', 'brand': 'technonicol', 'thick': 100, 'storey': 'one', 'price': 9500},
        {'tech': 'frame', 'contour': 'warm', 'brand': 'technonicol', 'thick': 150, 'storey': 'one', 'price': 11000},
        {'tech': 'frame', 'contour': 'warm', 'brand': 'technonicol', 'thick': 200, 'storey': 'mansard', 'price': 14000},
    ]

    for bp in base_prices:
        tech = next(t for t in refs['techs'] if t.code == bp['tech'])
        contour = next(c for c in refs['contours'] if c.code == bp['contour'])
        brand = next(b for b in refs['brands'] if b.code == bp['brand'])
        thick = next(t for t in refs['thicknesses'] if t.mm == bp['thick'])
        storey = next(s for s in refs['storey_types'] if s.code == bp['storey'])

        db.add(models.BasePriceM2(
            tech_id=tech.id,
            contour_id=contour.id,
            brand_id=brand.id,
            thickness_id=thick.id,
            storey_type_id=storey.id,
            price_rub=Decimal(str(bp['price']))
        ))

    db.commit()
    print(f"✓ Базовые цены: {len(base_prices)} записей")

def init_std_inclusions(db, refs):
    """Инициализирует стандартные включения"""
    print("\nИнициализация стандартных включений...")

    # Находим нужные ID
    tech_frame = next(t for t in refs['techs'] if t.code == 'frame')
    contour_warm = next(c for c in refs['contours'] if c.code == 'warm')
    storey_one = next(s for s in refs['storey_types'] if s.code == 'one')
    storey_mansard = next(s for s in refs['storey_types'] if s.code == 'mansard')

    std_inclusions = [
        models.StdInclusion(
            tech_id=tech_frame.id,
            contour_id=contour_warm.id,
            storey_type_id=storey_one.id,
            included_window_width_cm=100,
            included_window_height_cm=100,
            included_window_type='povorot_otkid',
            area_to_qty=[
                {"max_m2": 36, "qty": 2},
                {"max_m2": 60, "qty": 3},
                {"max_m2": 9999, "qty": 4}
            ],
            included_entry_door_code='entry_door_01',
            included_interior_doors_qty=3,
            note='Стандарт для одноэтажного дома'
        ),
        models.StdInclusion(
            tech_id=tech_frame.id,
            contour_id=contour_warm.id,
            storey_type_id=storey_mansard.id,
            included_window_width_cm=100,
            included_window_height_cm=100,
            included_window_type='povorot_otkid',
            area_to_qty=[
                {"max_m2": 40, "qty": 2},
                {"max_m2": 70, "qty": 4},
                {"max_m2": 9999, "qty": 5}
            ],
            included_entry_door_code='entry_door_01',
            included_interior_doors_qty=5,
            note='Стандарт для мансардного дома'
        ),
    ]

    db.add_all(std_inclusions)
    db.commit()
    print(f"✓ Стандартные включения: {len(std_inclusions)} записей")

def init_doors(db):
    """Инициализирует двери"""
    print("\nИнициализация дверей...")

    doors = [
        models.Door(code='entry_door_01', title='Входная дверь металлическая стандарт', price_rub=Decimal('25000')),
        models.Door(code='entry_door_02', title='Входная дверь металлическая утепленная', price_rub=Decimal('35000')),
        models.Door(code='entry_door_03', title='Входная дверь премиум', price_rub=Decimal('45000')),
        models.Door(code='interior_door_01', title='Межкомнатная дверь стандарт', price_rub=Decimal('8000')),
        models.Door(code='interior_door_02', title='Межкомнатная дверь улучшенная', price_rub=Decimal('12000')),
        models.Door(code='interior_door_03', title='Межкомнатная дверь премиум', price_rub=Decimal('18000')),
    ]

    db.add_all(doors)
    db.commit()
    print(f"✓ Двери: {len(doors)} записей")

def init_additional_tables(db):
    """Инициализирует дополнительные таблицы, которые НЕ синхронизируются из Google Sheets"""
    print("\nИнициализация дополнительных таблиц...")

    # Правила доставки
    db.add(models.DeliveryRule(
        free_km=100,
        rate_per_km=Decimal('120.00'),
        note='Стандартные условия доставки'
    ))

    # Цены на высоту потолка
    ceiling_heights = [
        models.CeilingHeightPrice(height_m=Decimal('2.4'), price_per_m2=Decimal('0')),
        models.CeilingHeightPrice(height_m=Decimal('2.5'), price_per_m2=Decimal('100')),
        models.CeilingHeightPrice(height_m=Decimal('2.6'), price_per_m2=Decimal('200')),
        models.CeilingHeightPrice(height_m=Decimal('2.7'), price_per_m2=Decimal('300')),
        models.CeilingHeightPrice(height_m=Decimal('2.8'), price_per_m2=Decimal('400')),
        models.CeilingHeightPrice(height_m=Decimal('3.0'), price_per_m2=Decimal('600')),
    ]
    db.add_all(ceiling_heights)

    # Цены на высоту конька
    ridge_heights = [
        models.RidgeHeightPrice(ridge_height_m=Decimal('0'), price_per_m2=Decimal('0')),
        models.RidgeHeightPrice(ridge_height_m=Decimal('0.3'), price_per_m2=Decimal('300')),
        models.RidgeHeightPrice(ridge_height_m=Decimal('0.6'), price_per_m2=Decimal('600')),
    ]
    db.add_all(ridge_heights)

    # Цены на вынос крыши
    roof_overhangs = [
        models.RoofOverhangPrice(overhang_cm=30, price_per_m2=Decimal('200')),
        models.RoofOverhangPrice(overhang_cm=40, price_per_m2=Decimal('300')),
        models.RoofOverhangPrice(overhang_cm=50, price_per_m2=Decimal('400')),
    ]
    db.add_all(roof_overhangs)

    # Цены на перегородки
    partitions = [
        models.PartitionPrice(type='plain', price_per_pm=Decimal('1000')),
        models.PartitionPrice(type='insul50', price_per_pm=Decimal('1500')),
        models.PartitionPrice(type='insul100', price_per_pm=Decimal('2000')),
    ]
    db.add_all(partitions)

    db.commit()
    print("✓ Дополнительные таблицы заполнены")

def verify_data(db):
    """Проверяет корректность данных"""
    print("\n" + "="*50)
    print("ПРОВЕРКА ДАННЫХ")
    print("="*50)

    counts = {
        'Технологии строительства': db.query(models.BuildTechnology).count(),
        'Контуры': db.query(models.Contour).count(),
        'Типы этажности': db.query(models.StoreyType).count(),
        'Марки утеплителя': db.query(models.InsulationBrand).count(),
        'Толщины утеплителя': db.query(models.InsulationThickness).count(),
        'Базовые цены': db.query(models.BasePriceM2).count(),
        'Стандартные включения': db.query(models.StdInclusion).count(),
        'Двери': db.query(models.Door).count(),
        'Правила доставки': db.query(models.DeliveryRule).count(),
        'Цены на высоту потолка': db.query(models.CeilingHeightPrice).count(),
        'Цены на высоту конька': db.query(models.RidgeHeightPrice).count(),
        'Цены на вынос крыши': db.query(models.RoofOverhangPrice).count(),
        'Цены на перегородки': db.query(models.PartitionPrice).count(),
    }

    print("\nКоличество записей:")
    for table, count in counts.items():
        status = "✓" if count > 0 else "✗"
        print(f"{status} {table}: {count}")

    # Проверка критичных данных
    print("\nПроверка критичных данных:")

    # Проверка std_inclusions
    std_incl = db.query(models.StdInclusion).first()
    if std_incl:
        print(f"✓ std_inclusions заполнены корректно")
        print(f"  - tech_id: {std_incl.tech_id}")
        print(f"  - contour_id: {std_incl.contour_id}")
        print(f"  - storey_type_id: {std_incl.storey_type_id}")
        print(f"  - included_entry_door_code: {std_incl.included_entry_door_code}")
        print(f"  - included_interior_doors_qty: {std_incl.included_interior_doors_qty}")
    else:
        print("✗ std_inclusions ПУСТЫ!")

    # Проверка base_price_m2
    base_price = db.query(models.BasePriceM2).first()
    if base_price:
        print(f"✓ base_price_m2 заполнены корректно")
    else:
        print("✗ base_price_m2 ПУСТЫ!")

    print("\n" + "="*50)

    all_ok = all(count > 0 for count in counts.values())
    if all_ok:
        print("✓ ВСЕ ДАННЫЕ ИНИЦИАЛИЗИРОВАНЫ КОРРЕКТНО!")
    else:
        print("✗ ЕСТЬ ПУСТЫЕ ТАБЛИЦЫ!")

    print("="*50 + "\n")

    return all_ok

def main():
    """Главная функция"""
    print("="*50)
    print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ КАЛЬКУЛЯТОРА")
    print("="*50)

    db = SessionLocal()

    try:
        # 1. Очистка
        clear_all_tables(db)

        # 2. Справочные таблицы
        refs = init_reference_tables(db)

        # 3. Базовые цены
        init_base_prices(db, refs)

        # 4. Стандартные включения
        init_std_inclusions(db, refs)

        # 5. Двери
        init_doors(db)

        # 6. Дополнительные таблицы
        init_additional_tables(db)

        # 7. Проверка
        if verify_data(db):
            print("\n✓ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            print("\nТеперь вы можете:")
            print("1. Запустить синхронизацию с Google Sheets: POST /admin/sync-prices")
            print("2. Использовать API для расчетов: POST /calculate")
            return 0
        else:
            print("\n✗ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА С ОШИБКАМИ!")
            return 1

    except Exception as e:
        print(f"\n✗ ОШИБКА ПРИ ИНИЦИАЛИЗАЦИИ: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()

if __name__ == '__main__':
    sys.exit(main())
