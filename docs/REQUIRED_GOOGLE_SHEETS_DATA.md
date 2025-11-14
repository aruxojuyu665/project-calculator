# Обязательные данные в Google Sheets для работы всех функций

## Обзор

Для полноценной работы калькулятора необходимо заполнить все листы в Google Sheets соответствующими данными. Без этих данных некоторые функции не будут работать корректно.

## Критические таблицы (обязательны для работы)

### 1. Справочные таблицы (Reference Tables)

Эти таблицы должны быть заполнены в первую очередь, так как от них зависят другие таблицы:

#### build_technologies (Технологии строительства)
**Важность:** ⭐⭐⭐ Критично
**Где хранится:** В базе данных (не синхронизируется из Google Sheets)

Примеры данных:
```sql
INSERT INTO build_technologies (code, title) VALUES
('panel', 'Панельная технология'),
('frame', 'Каркасная технология');
```

#### contours (Контуры)
**Важность:** ⭐⭐⭐ Критично
**Где хранится:** В базе данных (не синхронизируется из Google Sheets)

Примеры данных:
```sql
INSERT INTO contours (code, title) VALUES
('warm', 'Тёплый контур'),
('cold', 'Холодный контур');
```

#### storey_types (Типы этажности)
**Важность:** ⭐⭐⭐ Критично
**Где хранится:** В базе данных (не синхронизируется из Google Sheets)

Примеры данных:
```sql
INSERT INTO storey_types (code, title) VALUES
('one', 'Одноэтажный'),
('mansard', 'Мансардный'),
('two', 'Двухэтажный');
```

#### insulation_brands (Марки утеплителя)
**Важность:** ⭐⭐⭐ Критично
**Где хранится:** В базе данных (не синхронизируется из Google Sheets)

Примеры данных:
```sql
INSERT INTO insulation_brands (code, title) VALUES
('izobel', 'Изобел'),
('neman_plus', 'Неман+'),
('technonicol', 'Технониколь');
```

#### insulation_thicknesses (Толщины утеплителя)
**Важность:** ⭐⭐⭐ Критично
**Где хранится:** В базе данных (не синхронизируется из Google Sheets)

Примеры данных:
```sql
INSERT INTO insulation_thicknesses (mm) VALUES
(100), (150), (200);
```

### 2. Основные таблицы цен (синхронизируются из Google Sheets)

#### window_base_prices (Базовые цены на окна)
**Важность:** ⭐⭐⭐ Критично (без этого окна не будут работать)
**Лист в Google Sheets:** `window_base_prices`

**Обязательные колонки:**
- `width_cm` - ширина окна в см
- `height_cm` - высота окна в см
- `type` - тип окна (gluh, povorot, povorot_otkid)
- `base_price_rub` - базовая цена в рублях

**Пример данных:**
| width_cm | height_cm | type | base_price_rub |
|----------|-----------|------|----------------|
| 100 | 100 | povorot_otkid | 15000 |
| 100 | 120 | povorot_otkid | 17000 |
| 80 | 120 | povorot | 14000 |
| 60 | 120 | gluh | 10000 |

#### window_modifiers (Модификаторы цен на окна)
**Важность:** ⭐⭐⭐ Критично (без этого двухкамерные окна и ламинация не будут работать)
**Лист в Google Sheets:** `window_modifiers`

**Обязательные колонки:**
- `two_chambers` - двухкамерное окно (TRUE/FALSE)
- `laminated` - ламинация (TRUE/FALSE)
- `multiplier` - множитель цены (например, 1.0, 1.15, 1.3)

**Пример данных:**
| two_chambers | laminated | multiplier |
|--------------|-----------|------------|
| FALSE | FALSE | 1.0 |
| TRUE | FALSE | 1.15 |
| FALSE | TRUE | 1.2 |
| TRUE | TRUE | 1.3 |

**Важно:** Должна быть строка с `two_chambers=FALSE` и `laminated=FALSE` (базовая конфигурация).

#### doors (Двери)
**Важность:** ⭐⭐⭐ Критично (без этого двери не будут работать)
**Лист в Google Sheets:** `doors`

**Обязательные колонки:**
- `code` - уникальный код двери
- `title` - название двери
- `price_rub` - цена в рублях

**Пример данных:**
| code | title | price_rub |
|------|-------|-----------|
| entry_door_01 | Входная дверь металлическая | 25000 |
| entry_door_02 | Входная дверь утепленная | 35000 |
| interior_door_01 | Межкомнатная дверь стандарт | 8000 |

**Важно:** Коды для входных дверей лучше начинать с `entry_`, а для межкомнатных с `interior_`.

#### std_inclusions (Стандартные включения)
**Важность:** ⭐⭐⭐ Критично (без этого окна и двери в стандарте не будут работать)
**Лист в Google Sheets:** `std_inclusions`

**Обязательные колонки:**
- `tech_code` - код технологии (panel, frame) - если не указан, будет использован дефолтный
- `contour_code` - код контура (warm) - если не указан, будет использован дефолтный
- `storey_type_code` - код типа этажности (one, mansard) - если не указан, будет использован дефолтный
- `included_window_width_cm` - ширина стандартного окна (100)
- `included_window_height_cm` - высота стандартного окна (100)
- `included_window_type` - тип стандартного окна (povorot_otkid)
- `area_to_qty` - JSON с зависимостью количества окон от площади
- `included_entry_door_code` - код входной двери (опционально)
- `included_interior_doors_qty` - количество межкомнатных дверей (опционально)

**Пример данных:**
| tech_code | contour_code | storey_type_code | included_window_width_cm | included_window_height_cm | included_window_type | area_to_qty | included_entry_door_code | included_interior_doors_qty |
|-----------|--------------|------------------|--------------------------|---------------------------|---------------------|-------------|--------------------------|----------------------------|
| frame | warm | one | 100 | 100 | povorot_otkid | `[{"max_m2": 36, "qty": 2}, {"max_m2": 60, "qty": 3}, {"max_m2": 9999, "qty": 4}]` | entry_door_01 | 3 |
| frame | warm | mansard | 100 | 100 | povorot_otkid | `[{"max_m2": 40, "qty": 2}, {"max_m2": 70, "qty": 4}, {"max_m2": 9999, "qty": 5}]` | entry_door_01 | 5 |

**Важно:**
- Если колонки tech_code, contour_code, storey_type_code отсутствуют, система будет использовать первую запись из справочных таблиц
- JSON в area_to_qty должен быть валидным
- Последний элемент в area_to_qty должен иметь большое значение max_m2 (например, 9999) для "всех остальных" площадей

#### addons (Дополнительные опции)
**Важность:** ⭐⭐ Важно (без этого допы не будут работать)
**Лист в Google Sheets:** `addons`

**Обязательные колонки:**
- `code` - уникальный код дополнения
- `title` - название
- `calc_mode` - режим расчета (AREA, RUN_M, PERIMETER, COUNT, ROOF_L_SIDES, M2_PER_HOUSE)
- `price` - цена
- `params` - JSON с параметрами (обязательно {})
- `active` - активность (TRUE/FALSE)

**Пример данных:**
| code | title | calc_mode | price | params | active |
|------|-------|-----------|-------|--------|--------|
| terrace | Терраса | AREA | 5000 | {} | TRUE |
| porch | Крыльцо | AREA | 6000 | {} | TRUE |
| extra_insulation | Дополнительная изоляция | AREA | 1000 | {} | TRUE |

#### ceiling_height_prices (Цены на высоту потолка)
**Важность:** ⭐⭐ Важно
**Лист в Google Sheets:** `ceiling_height_prices`

**Обязательные колонки:**
- `height_m` - высота в метрах (2.4, 2.5, 2.6, 2.7, 2.8, 3.0)
- `price_per_m2` - цена за м²

**Пример данных:**
| height_m | price_per_m2 |
|----------|--------------|
| 2.4 | 0 |
| 2.5 | 100 |
| 2.6 | 200 |
| 2.7 | 300 |
| 2.8 | 400 |
| 3.0 | 600 |

#### ridge_height_prices (Цены на высоту конька)
**Важность:** ⭐⭐ Важно
**Лист в Google Sheets:** `ridge_height_prices`

**Обязательные колонки:**
- `ridge_height_m` - высота конька в метрах (0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6)
- `price_per_m2` - цена за м²

#### roof_overhang_prices (Цены на вынос крыши)
**Важность:** ⭐⭐ Важно
**Лист в Google Sheets:** `roof_overhang_prices`

**Обязательные колонки:**
- `overhang_cm` - вынос в см (std, 30, 40, 50)
- `price_per_m2` - цена за м²

#### partition_prices (Цены на перегородки)
**Важность:** ⭐ Средне
**Лист в Google Sheets:** `partition_prices`

**Обязательные колонки:**
- `type` - тип перегородки (plain, insul50, insul100)
- `price_per_pm` - цена за погонный метр

#### delivery_rules (Правила доставки)
**Важность:** ⭐ Средне
**Лист в Google Sheets:** `delivery_rules`

**Обязательные колонки:**
- `free_km` - бесплатная доставка до N км
- `rate_per_km` - стоимость за км
- `note` - примечание (опционально)

## Таблицы, которые НЕ синхронизируются из Google Sheets

### base_price_m2 (Базовая цена за м²)

**Где хранится:** Только в базе данных
**Важность:** ⭐⭐⭐ Критично

Эта таблица должна быть заполнена вручную через SQL или миграции. Она содержит базовые цены за м² для разных комбинаций:
- Технологии строительства (tech_id)
- Контура (contour_id)
- Марки утеплителя (brand_id)
- Толщины утеплителя (thickness_id)
- Типа этажности (storey_type_id)

**Пример SQL для заполнения:**
```sql
-- Получаем ID из справочных таблиц
-- panel/warm/izobel/100/one = 10000 руб/м²
INSERT INTO base_price_m2 (tech_id, contour_id, brand_id, thickness_id, storey_type_id, price_rub)
SELECT
    (SELECT id FROM build_technologies WHERE code = 'panel'),
    (SELECT id FROM contours WHERE code = 'warm'),
    (SELECT id FROM insulation_brands WHERE code = 'izobel'),
    (SELECT id FROM insulation_thicknesses WHERE mm = 100),
    (SELECT id FROM storey_types WHERE code = 'one'),
    10000.00;
```

## Проверка корректности данных

После заполнения всех таблиц выполните синхронизацию:

```bash
curl -X POST http://localhost:8000/admin/sync-prices
```

И проверьте логи на наличие ошибок и предупреждений.

## Минимальный набор данных для тестирования

Для базового тестирования достаточно:

1. **Справочные таблицы:** заполнить минимум по одной записи в каждой
2. **window_base_prices:** хотя бы одно окно 100x100 povorot_otkid
3. **window_modifiers:** обязательно строка FALSE/FALSE/1.0
4. **doors:** одна входная и одна межкомнатная дверь
5. **std_inclusions:** одна запись для тестовой конфигурации
6. **base_price_m2:** одна запись для тестовой комбинации параметров

## Распространенные ошибки

### 1. "Двери не отображаются на фронтенде"

**Причины:**
- Таблица `doors` пуста в Google Sheets
- В `std_inclusions` не заполнены `included_entry_door_code` или `included_interior_doors_qty`
- Коды дверей в `std_inclusions` не совпадают с кодами в таблице `doors`

**Решение:**
1. Заполните таблицу `doors` в Google Sheets
2. Укажите коды дверей и количество в `std_inclusions`
3. Запустите синхронизацию: `POST /admin/sync-prices`

### 2. "Окна не работают"

**Причины:**
- Таблица `window_base_prices` пуста
- Отсутствует базовый модификатор в `window_modifiers` (FALSE/FALSE/1.0)
- В `std_inclusions` не настроены параметры стандартных окон

**Решение:**
1. Заполните `window_base_prices`
2. Добавьте строку FALSE/FALSE/1.0 в `window_modifiers`
3. Настройте `std_inclusions`
4. Запустите синхронизацию

### 3. "Половина функций не работает"

**Причины:**
- Не все таблицы заполнены в Google Sheets
- Справочные таблицы (build_technologies, contours, etc.) пусты в БД
- Таблица `base_price_m2` пуста

**Решение:**
1. Проверьте какие таблицы заполнены
2. Заполните справочные таблицы в БД через SQL
3. Заполните `base_price_m2` для нужных комбинаций параметров
4. Заполните все листы в Google Sheets
5. Запустите синхронизацию

## SQL скрипт для инициализации справочных таблиц

```sql
-- Технологии строительства
INSERT INTO build_technologies (code, title) VALUES
('panel', 'Панельная технология'),
('frame', 'Каркасная технология');

-- Контуры
INSERT INTO contours (code, title) VALUES
('warm', 'Тёплый контур'),
('cold', 'Холодный контур');

-- Типы этажности
INSERT INTO storey_types (code, title) VALUES
('one', 'Одноэтажный'),
('mansard', 'Мансардный'),
('two', 'Двухэтажный');

-- Марки утеплителя
INSERT INTO insulation_brands (code, title) VALUES
('izobel', 'Изобел'),
('neman_plus', 'Неман+'),
('technonicol', 'Технониколь');

-- Толщины утеплителя
INSERT INTO insulation_thicknesses (mm) VALUES
(100), (150), (200);

-- Базовые цены (пример для одной конфигурации)
INSERT INTO base_price_m2 (tech_id, contour_id, brand_id, thickness_id, storey_type_id, price_rub)
SELECT
    bt.id, c.id, ib.id, it.id, st.id, 10000.00
FROM
    build_technologies bt,
    contours c,
    insulation_brands ib,
    insulation_thicknesses it,
    storey_types st
WHERE
    bt.code = 'panel'
    AND c.code = 'warm'
    AND ib.code = 'izobel'
    AND it.mm = 100
    AND st.code = 'one';
```

## Дополнительная помощь

Для получения дополнительной помощи см.:
- [GOOGLE_SHEETS_INTEGRATION.md](GOOGLE_SHEETS_INTEGRATION.md) - подробная инструкция по интеграции
- [GOOGLE_SHEETS_STD_INCLUSIONS_EXAMPLE.md](GOOGLE_SHEETS_STD_INCLUSIONS_EXAMPLE.md) - примеры для std_inclusions
- [CHANGELOG_std_inclusions_fix.md](../CHANGELOG_std_inclusions_fix.md) - история изменений
