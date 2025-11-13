-- Добавляем недостающие записи в std_inclusions

-- panel + warm + mansard
INSERT INTO std_inclusions (tech_id, contour_id, storey_type_id, included_window_width_cm, included_window_height_cm, included_window_type, area_to_qty)
SELECT 
    bt.id, c.id, st.id,
    100, 100, 'povorot_otkid',
    '[{"qty": 2, "max_m2": 40}, {"qty": 4, "max_m2": 70}]'::json
FROM build_technologies bt
CROSS JOIN contours c
CROSS JOIN storey_types st
WHERE bt.code = 'panel' 
  AND c.code = 'warm'
  AND st.code = 'mansard'
ON CONFLICT (tech_id, contour_id, storey_type_id) DO NOTHING;

-- frame + warm + one
INSERT INTO std_inclusions (tech_id, contour_id, storey_type_id, included_window_width_cm, included_window_height_cm, included_window_type, area_to_qty)
SELECT 
    bt.id, c.id, st.id,
    100, 100, 'povorot_otkid',
    '[{"qty": 2, "max_m2": 36}, {"qty": 3, "max_m2": 60}]'::json
FROM build_technologies bt
CROSS JOIN contours c
CROSS JOIN storey_types st
WHERE bt.code = 'frame' 
  AND c.code = 'warm'
  AND st.code = 'one'
ON CONFLICT (tech_id, contour_id, storey_type_id) DO NOTHING;



