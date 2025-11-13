-- Минимальные начальные данные для работы калькулятора

-- Справочники
INSERT INTO build_technologies (code, title) VALUES 
    ('panel', 'Панельная'),
    ('frame', 'Каркасная')
ON CONFLICT (code) DO NOTHING;

INSERT INTO storey_types (code, title) VALUES 
    ('one', 'Одноэтажный'),
    ('mansard', 'Мансардный'),
    ('two', 'Двухэтажный')
ON CONFLICT (code) DO NOTHING;

INSERT INTO contours (code, title) VALUES 
    ('warm', 'Теплый'),
    ('cold', 'Холодный')
ON CONFLICT (code) DO NOTHING;

INSERT INTO insulation_brands (code, title) VALUES 
    ('izobel', 'Изобел'),
    ('neman_plus', 'Неман+'),
    ('technonicol', 'Технониколь')
ON CONFLICT (code) DO NOTHING;

INSERT INTO insulation_thicknesses (mm) VALUES 
    (100), (150), (200)
ON CONFLICT (mm) DO NOTHING;

-- Базовая цена (примерные значения для тестирования)
-- Получаем ID из справочников
INSERT INTO base_price_m2 (tech_id, contour_id, brand_id, thickness_id, storey_type_id, price_rub)
SELECT 
    bt.id, c.id, ib.id, it.id, st.id,
    15000.00 -- Примерная цена за м²
FROM build_technologies bt
CROSS JOIN contours c
CROSS JOIN insulation_brands ib
CROSS JOIN insulation_thicknesses it
CROSS JOIN storey_types st
WHERE bt.code = 'panel' 
  AND c.code = 'warm'
  AND ib.code = 'izobel'
  AND it.mm = 100
  AND st.code = 'one'
ON CONFLICT DO NOTHING;

-- Добавляем еще несколько комбинаций
INSERT INTO base_price_m2 (tech_id, contour_id, brand_id, thickness_id, storey_type_id, price_rub)
SELECT 
    bt.id, c.id, ib.id, it.id, st.id,
    16500.00
FROM build_technologies bt
CROSS JOIN contours c
CROSS JOIN insulation_brands ib
CROSS JOIN insulation_thicknesses it
CROSS JOIN storey_types st
WHERE bt.code = 'panel' 
  AND c.code = 'warm'
  AND ib.code = 'izobel'
  AND it.mm = 150
  AND st.code = 'one'
ON CONFLICT DO NOTHING;

INSERT INTO base_price_m2 (tech_id, contour_id, brand_id, thickness_id, storey_type_id, price_rub)
SELECT 
    bt.id, c.id, ib.id, it.id, st.id,
    18000.00
FROM build_technologies bt
CROSS JOIN contours c
CROSS JOIN insulation_brands ib
CROSS JOIN insulation_thicknesses it
CROSS JOIN storey_types st
WHERE bt.code = 'panel' 
  AND c.code = 'warm'
  AND ib.code = 'izobel'
  AND it.mm = 200
  AND st.code = 'mansard'
ON CONFLICT DO NOTHING;

-- Высота потолка
INSERT INTO ceiling_height_prices (height_m, price_per_m2) VALUES
    (2.4, 0),
    (2.5, 100),
    (2.6, 200),
    (2.7, 300),
    (2.8, 400),
    (3.0, 600)
ON CONFLICT (height_m) DO NOTHING;

-- Повышение конька (в метрах: 0.1 = 10см, 0.2 = 20см и т.д.)
INSERT INTO ridge_height_prices (ridge_height_m, price_per_m2) VALUES
    (0.1, 50),
    (0.2, 100),
    (0.3, 150),
    (0.4, 200),
    (0.5, 250),
    (0.6, 300)
ON CONFLICT (ridge_height_m) DO NOTHING;

-- Вынос крыши
INSERT INTO roof_overhang_prices (overhang_cm, price_per_m2) VALUES
    (30, 150),
    (40, 200),
    (50, 250)
ON CONFLICT (overhang_cm) DO NOTHING;

-- Перегородки
INSERT INTO partition_prices (type, price_per_pm) VALUES
    ('plain', 1000),
    ('insul50', 1500),
    ('insul100', 2000)
ON CONFLICT (type) DO NOTHING;

