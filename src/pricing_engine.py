import math
from sqlalchemy.orm import Session
from src.schemas import (
    CalculateRequestSchema,
    CalculateResponseSchema,
    GabaritySchema,
    OknaIDveriSchema,
    KonstruktivSchema,
    ItogovayaStoimostSchema,
    DopolneniyaItem,
    StandardWindowItem,
    DoorItem,
    DoorSelectionSchema
)
from src import models


class PricingEngine:
    """
    Основной класс для расчёта стоимости проекта на основе бизнес-логики.
    """

    def calculate_total(self, db: Session, req: CalculateRequestSchema) -> CalculateResponseSchema:
        """
        Рассчитывает полную стоимость проекта, вызывая все необходимые под-расчеты.
        """
        # --- 0. Предварительные расчеты (Обозначения) ---
        A_house = req.house.length_m * req.house.width_m
        
        # Рассчитываем площади террас и крылец
        A_terrace = 0.0
        if req.terrace:
            if req.terrace.primary and req.terrace.primary.enabled:
                A_terrace += (req.terrace.primary.length_m or 0) * (req.terrace.primary.width_m or 0)
            if req.terrace.extra and req.terrace.extra.enabled:
                A_terrace += (req.terrace.extra.length_m or 0) * (req.terrace.extra.width_m or 0)
        
        A_porch = 0.0
        if req.porch:
            if req.porch.primary and req.porch.primary.enabled:
                A_porch += (req.porch.primary.length_m or 0) * (req.porch.primary.width_m or 0)
            if req.porch.extra and req.porch.extra.enabled:
                A_porch += (req.porch.extra.length_m or 0) * (req.porch.extra.width_m or 0)
        
        # --- 1. Базовая цена ---
        base_price = self._get_base_price(db, req, A_house)

        # --- 2. Дополнения ---
        # 2.1 Потолки, конёк, вынос крыши (отдельные таблицы)
        roof_costs, roof_details = self._calculate_roof_costs(db, req, A_house)

        # 2.2 Перегородки (отдельная таблица)
        partitions_cost, partitions_details = self._calculate_partitions_cost(db, req)
        
        # 2.3 Прочие "допы" (используем существующий метод _calculate_generic_addons_cost)
        generic_addons_cost, generic_addons_details = self._calculate_generic_addons_cost(db, req, A_house)

        all_addons_details = roof_details + partitions_details + generic_addons_details
        
        # --- 3. Окна и двери ---
        windows_cost, windows_details = self._calculate_windows_price(db, req)
        # Применяем логику замещения: вычитаем стоимость стандартных окон только если выбраны новые окна
        if req.windows and len(req.windows) > 0:
            replacement_delta = self._handle_replacements(db, req, A_house)
            windows_cost_after_replacement = windows_cost - replacement_delta
        else:
            # Если окна не выбраны, показываем стандартные окна
            std_windows_details, std_windows_cost = self._get_standard_windows_details(db, req, A_house)
            windows_details = std_windows_details
            windows_cost_after_replacement = std_windows_cost
        doors_cost, doors_details = self._calculate_doors_price(db, req)
        windows_doors_cost = windows_cost_after_replacement + doors_cost

        # --- 4. Доставка ---
        delivery_cost = self._get_delivery_price(db, req)
        delivery_cost_with_details, delivery_details = self._calculate_delivery_cost(db, req)
        if delivery_details:
            all_addons_details.append(delivery_details)

        # --- 5. Итоговый расчет ---
        # Суммируем все компоненты стоимости
        subtotal = base_price + roof_costs + partitions_cost + generic_addons_cost + windows_doors_cost + delivery_cost
        
        # Добавляем комиссию агента
        commission_rub = req.commission_rub
        final_price = subtotal + commission_rub

        # --- 6. Сборка ответа ---
        response = CalculateResponseSchema(
            Габариты=GabaritySchema(
                Площадь_теплого_контура_м2=A_house,
                Площадь_террас_м2=A_terrace,
                Площадь_крылец_м2=A_porch,
                Высота_потолка_м=req.ceiling.height_m,
                Тип_потолка=req.ceiling.type,
                Повышение_конька_см=req.ceiling.ridge_delta_cm or 0,
                Вынос_крыши=req.roof.overhang_cm,
            ),
            Окна_и_двери=OknaIDveriSchema(
                Стандартные_окна=windows_details,
                Двери=doors_details,
                Итого_по_разделу_руб=round(windows_doors_cost, 2)
            ),
            Конструктив=KonstruktivSchema(
                База_руб=round(base_price, 2),
                Дополнения=all_addons_details,
                Доставка_руб=round(delivery_cost, 2)
            ),
            Итоговая_стоимость=ItogovayaStoimostSchema(
                Итого_без_комиссии_руб=round(subtotal, 2),
                Комиссия_руб=round(commission_rub, 2),
                Окончательная_цена_руб=round(final_price, 2),
            )
        )
        return response

    def _get_base_price(self, db: Session, req: CalculateRequestSchema, A_house: float) -> float:
        """
        Расчет базовой цены (матрица стр. 1–5 прайса).
        """
        if req.ceiling.type == 'flat':
            storey_type_code = 'one'
        else: # 'rafters'
            storey_type_code = 'mansard'
        
        # Проверяем, есть ли вообще данные в таблице
        total_records = db.query(models.BasePriceM2).count()
        print(f"DEBUG: Всего записей в base_price_m2: {total_records}")
        
        # Проверяем справочники
        tech_count = db.query(models.BuildTechnology).filter_by(code=req.insulation.build_tech).count()
        brand_count = db.query(models.InsulationBrand).filter_by(code=req.insulation.brand).count()
        thickness_count = db.query(models.InsulationThickness).filter_by(mm=req.insulation.mm).count()
        storey_count = db.query(models.StoreyType).filter_by(code=storey_type_code).count()
        contour_count = db.query(models.Contour).filter_by(code='warm').count()
        
        print(f"DEBUG: Поиск цены для tech={req.insulation.build_tech} (найдено: {tech_count}), "
              f"brand={req.insulation.brand} (найдено: {brand_count}), "
              f"mm={req.insulation.mm} (найдено: {thickness_count}), "
              f"storey={storey_type_code} (найдено: {storey_count}), "
              f"contour=warm (найдено: {contour_count})")
        
        price_per_sqm = db.query(models.BasePriceM2.price_rub).join(
            models.BuildTechnology, models.BasePriceM2.tech_id == models.BuildTechnology.id
        ).join(
            models.InsulationBrand, models.BasePriceM2.brand_id == models.InsulationBrand.id
        ).join(
            models.InsulationThickness, models.BasePriceM2.thickness_id == models.InsulationThickness.id
        ).join(
            models.StoreyType, models.BasePriceM2.storey_type_id == models.StoreyType.id
        ).join(
            models.Contour, models.BasePriceM2.contour_id == models.Contour.id
        ).filter(
            models.BuildTechnology.code == req.insulation.build_tech,
            models.InsulationBrand.code == req.insulation.brand,
            models.InsulationThickness.mm == req.insulation.mm,
            models.StoreyType.code == storey_type_code,
            models.Contour.code == 'warm'
        ).scalar()

        if price_per_sqm is None:
            print(f"WARNING: Базовая цена не найдена в БД для указанных параметров. Возвращаю 0.0")
            return 0.0
        
        print(f"DEBUG: Найдена базовая цена {price_per_sqm} руб/м², площадь {A_house} м²")
        base_price = float(price_per_sqm) * A_house
        return base_price

    def _calculate_roof_costs(self, db: Session, req: CalculateRequestSchema, A_house: float) -> tuple[float, list[DopolneniyaItem]]:
        """
        Расчет стоимости допов по потолку и кровле (стр. 20 прайса).
        """
        total_cost = 0.0
        details = []

        # 1. Стоимость за высоту потолка
        price_model = db.query(models.CeilingHeightPrice).filter_by(height_m=req.ceiling.height_m).first()
        if price_model and price_model.price_per_m2 > 0:
            cost = float(price_model.price_per_m2) * A_house
            total_cost += cost
            details.append(DopolneniyaItem(Код="CEILING_H", Наименование=f"Увеличение высоты потолка до {req.ceiling.height_m}м", Расчёт=f"{A_house:.2f}м² × {price_model.price_per_m2}₽", Сумма_руб=cost))

        # 2. Стоимость за повышение конька (только для 'flat')
        if req.ceiling.type == 'flat' and req.ceiling.ridge_delta_cm is not None and req.ceiling.ridge_delta_cm > 0:
            # Конвертируем см в метры для поиска в БД
            ridge_height_m = req.ceiling.ridge_delta_cm / 100.0
            price_model = db.query(models.RidgeHeightPrice).filter_by(ridge_height_m=ridge_height_m).first()
            if price_model and price_model.price_per_m2 > 0:
                cost = float(price_model.price_per_m2) * A_house
                total_cost += cost
                details.append(DopolneniyaItem(Код="RIDGE_H", Наименование=f"Увеличение конька на {req.ceiling.ridge_delta_cm}см", Расчёт=f"{A_house:.2f}м² × {price_model.price_per_m2}₽", Сумма_руб=cost))

        # 3. Стоимость за вынос крыши (std - бесплатно)
        if req.roof.overhang_cm != 'std':
            overhang_cm_val = int(req.roof.overhang_cm)
            price_model = db.query(models.RoofOverhangPrice).filter_by(overhang_cm=overhang_cm_val).first()
            if price_model and price_model.price_per_m2 > 0:
                cost = float(price_model.price_per_m2) * A_house
                total_cost += cost
                details.append(DopolneniyaItem(Код="OVERHANG", Наименование=f"Увеличение выноса крыши до {overhang_cm_val}см", Расчёт=f"{A_house:.2f}м² × {price_model.price_per_m2}₽", Сумма_руб=cost))

        return total_cost, details

    def _calculate_partitions_cost(self, db: Session, req: CalculateRequestSchema) -> tuple[float, list[DopolneniyaItem]]:
        """
        Расчет стоимости перегородок (стр. 21 прайса).
        """
        if not req.partitions.enabled or not req.partitions.type or req.partitions.type == 'none' or not req.partitions.run_m:
            return 0.0, []
        
        price_model = db.query(models.PartitionPrice).filter_by(type=req.partitions.type).first()
        if not price_model:
            return 0.0, []
        
        cost = float(price_model.price_per_pm) * req.partitions.run_m
        details = [DopolneniyaItem(Код="PARTITIONS", Наименование=f"Перегородки ({price_model.type.value})", Расчёт=f"{req.partitions.run_m}п.м. × {price_model.price_per_pm}₽", Сумма_руб=cost)]
        return cost, details

    def _calculate_generic_addons_cost(self, db: Session, req: CalculateRequestSchema, A_house: float) -> tuple[float, list[DopolneniyaItem]]:
        """
        Расчет стоимости прочих "допов" (стр. 11–19, 21 прайса).
        """
        total_cost = 0.0
        details = []
        if not req.addons:
            return total_cost, details

        addon_codes = [addon.code for addon in req.addons]
        db_addons = {addon.code: addon for addon in db.query(models.Addon).filter(models.Addon.code.in_(addon_codes)).all()}

        for addon_req in req.addons:
            db_addon = db_addons.get(addon_req.code)
            if not db_addon:
                continue

            price = float(db_addon.price)
            calc_mode = db_addon.calc_mode.name
            cost = 0.0
            calc_str = ""

            if calc_mode == 'AREA':
                cost = price * A_house
                calc_str = f"{A_house:.2f}м² × {price}₽"
            elif calc_mode in ('RUN_M', 'PERIMETER'):
                P_perimeter = (req.house.length_m + req.house.width_m) * 2
                cost = price * P_perimeter
                calc_str = f"{P_perimeter:.2f}п.м. × {price}₽"
            elif calc_mode == 'ROOF_L_SIDES':
                L_long = max(req.house.length_m, req.house.width_m)
                sides = db_addon.params.get('sides', 2)
                reserve_m = db_addon.params.get('reserve_m', 1)
                cost = price * (L_long + reserve_m) * sides
                calc_str = f"({L_long}+{reserve_m})м × {sides} стороны × {price}₽"
            elif calc_mode == 'COUNT':
                cost = price * addon_req.quantity
                calc_str = f"{addon_req.quantity}шт × {price}₽"
            
            if cost > 0:
                total_cost += cost
                details.append(DopolneniyaItem(Код=db_addon.code, Наименование=db_addon.title, Расчёт=calc_str, Сумма_руб=cost))

        return total_cost, details

    def _get_delivery_price(self, db: Session, req: CalculateRequestSchema) -> float:
        """
        Расчет стоимости доставки по фиксированной формуле (стр. 29 прайса).
        
        Формула: (distance_km - 100) * 120
        Если дистанция <= 100 км, цена = 0.
        """
        if req.delivery.distance_km <= 100:
            return 0.0
        
        cost = (req.delivery.distance_km - 100) * 120
        return cost

    def _calculate_delivery_cost(self, db: Session, req: CalculateRequestSchema) -> tuple[float, DopolneniyaItem | None]:
        """
        Расчет стоимости доставки (стр. 29 прайса).
        Использует метод _get_delivery_price для получения цены.
        """
        cost = self._get_delivery_price(db, req)
        if cost == 0:
            return 0.0, None

        details = DopolneniyaItem(
            Код="DELIVERY",
            Наименование="Доставка",
            Расчёт=f"({req.delivery.distance_km}км - 100км) × 120₽",
            Сумма_руб=cost
        )
        return cost, details

    def _calculate_windows_price(self, db: Session, req: CalculateRequestSchema) -> tuple[float, list[StandardWindowItem]]:
        """
        Расчет стоимости окон (стр. 23-24 прайса).
        
        Важно: Модификаторы НЕ аддитивны!
        Если выбраны оба (dual_chamber + laminated), используется специальный 
        multiplier 1.70, а не 1.20 * 1.40.
        """
        total_cost = 0.0
        windows_details = []
        
        if not req.windows:
            return total_cost, windows_details

        for window_req in req.windows:
            # 1. Найти базовую цену окна по размеру и типу
            base_price_model = db.query(models.WindowBasePrice).filter_by(
                width_cm=window_req.width_cm,
                height_cm=window_req.height_cm,
                type=window_req.type
            ).first()
            
            if not base_price_model:
                # Если окно не найдено, пропускаем его
                continue
            
            base_price = float(base_price_model.base_price_rub)
            
            # 2. Определить комбинацию модификаторов и найти соответствующий multiplier
            # Важно: логика НЕ аддитивная! Ищем точную комбинацию в БД
            modifier = db.query(models.WindowModifier).filter_by(
                two_chambers=window_req.dual_chamber,
                laminated=window_req.laminated
            ).first()
            
            if not modifier:
                # Если модификатор не найден, используем базовый множитель 1.0
                multiplier = 1.0
            else:
                multiplier = float(modifier.multiplier)
            
            # 3. Рассчитать цену окна: Базовая_Цена * Множитель * Количество
            price_per_unit = base_price * multiplier
            total_price = price_per_unit * window_req.quantity
            total_cost += total_price
            
            # 4. Формируем строку размера для отображения
            size_str = f"{window_req.width_cm}×{window_req.height_cm}"
            
            # Формируем описание типа окна
            type_str_map = {
                'gluh': 'глухое',
                'povorot': 'поворотное',
                'povorot_otkid': 'поворотно-откидное'
            }
            type_str = type_str_map.get(window_req.type, window_req.type)
            
            # Добавляем информацию о модификаторах в описание, если они есть
            mods = []
            if window_req.dual_chamber:
                mods.append("2-камерное")
            if window_req.laminated:
                mods.append("ламинация")
            if mods:
                type_str += f" ({', '.join(mods)})"
            
            # 5. Добавляем детали в список для ответа
            windows_details.append(StandardWindowItem(
                Размер=size_str,
                Тип=type_str,
                Колво=window_req.quantity,
                Цена_шт_руб=round(price_per_unit, 2),
                Сумма_руб=round(total_price, 2)
            ))
        
        return total_cost, windows_details

    def _handle_replacements(self, db: Session, req: CalculateRequestSchema, A_house: float) -> float:
        """
        Реализует логику замещения стандартных окон (стр. 3, 6 прайса).
        
        В стандарт входят окна 100×100 однокамерные (кол-во зависит от площади).
        При замене считаем разницу: delta = Σ (price_new - price_std) × qty
        
        Метод возвращает стоимость стандартных окон, которую нужно вычесть
        из общей стоимости выбранных окон.
        """
        # 1. Определяем параметры для поиска стандартного включения
        if req.ceiling.type == 'flat':
            storey_type_code = 'one'
        else:  # 'rafters'
            storey_type_code = 'mansard'
        
        # Находим стандартное включение для текущей конфигурации
        std_inclusion = db.query(models.StdInclusion).join(
            models.BuildTechnology, models.StdInclusion.tech_id == models.BuildTechnology.id
        ).join(
            models.Contour, models.StdInclusion.contour_id == models.Contour.id
        ).join(
            models.StoreyType, models.StdInclusion.storey_type_id == models.StoreyType.id
        ).filter(
            models.BuildTechnology.code == req.insulation.build_tech,
            models.Contour.code == 'warm',
            models.StoreyType.code == storey_type_code
        ).first()
        
        if not std_inclusion:
            # Если стандартное включение не найдено, не вычитаем ничего
            return 0.0
        
        # 2. Определяем количество стандартных окон на основе площади
        # area_to_qty имеет формат: [{"max_m2":36,"qty":2},{"max_m2":60,"qty":3},{"max_m2":9999,"qty":4}]
        area_to_qty = std_inclusion.area_to_qty
        if not area_to_qty or not isinstance(area_to_qty, list):
            return 0.0
        
        std_windows_qty = 0
        for rule in sorted(area_to_qty, key=lambda x: x.get('max_m2', 0)):
            if A_house <= rule.get('max_m2', 0):
                std_windows_qty = rule.get('qty', 0)
                break
        
        if std_windows_qty == 0:
            return 0.0
        
        # 3. Находим базовую цену стандартного окна (100×100, однокамерное, без ламинации)
        std_window_base = db.query(models.WindowBasePrice).filter_by(
            width_cm=std_inclusion.included_window_width_cm,
            height_cm=std_inclusion.included_window_height_cm,
            type=std_inclusion.included_window_type
        ).first()
        
        if not std_window_base:
            # Если стандартное окно не найдено в базе цен, не вычитаем
            return 0.0
        
        # 4. Стандартное окно - однокамерное без ламинации, значит multiplier = 1.0
        # Находим модификатор для однокамерного без ламинации
        std_modifier = db.query(models.WindowModifier).filter_by(
            two_chambers=False,
            laminated=False
        ).first()
        
        if std_modifier:
            std_multiplier = float(std_modifier.multiplier)
        else:
            std_multiplier = 1.0
        
        # 5. Рассчитываем стоимость стандартных окон
        std_window_price_per_unit = float(std_window_base.base_price_rub) * std_multiplier
        std_windows_total_cost = std_window_price_per_unit * std_windows_qty
        
        return std_windows_total_cost

    def _get_standard_windows_details(self, db: Session, req: CalculateRequestSchema, A_house: float) -> tuple[list[StandardWindowItem], float]:
        """
        Получает детали стандартных окон, включенных в базовую цену.
        """
        windows_details = []
        total_cost = 0.0
        
        # Определяем параметры для поиска стандартного включения
        if req.ceiling.type == 'flat':
            storey_type_code = 'one'
        else:  # 'rafters'
            storey_type_code = 'mansard'
        
        # Находим стандартное включение
        std_inclusion = db.query(models.StdInclusion).join(
            models.BuildTechnology, models.StdInclusion.tech_id == models.BuildTechnology.id
        ).join(
            models.Contour, models.StdInclusion.contour_id == models.Contour.id
        ).join(
            models.StoreyType, models.StdInclusion.storey_type_id == models.StoreyType.id
        ).filter(
            models.BuildTechnology.code == req.insulation.build_tech,
            models.Contour.code == 'warm',
            models.StoreyType.code == storey_type_code
        ).first()
        
        if not std_inclusion:
            print(f"DEBUG: Стандартное включение не найдено для tech={req.insulation.build_tech}, contour=warm, storey={storey_type_code}")
            return windows_details, total_cost
        
        # Определяем количество стандартных окон
        area_to_qty = std_inclusion.area_to_qty
        if not area_to_qty or not isinstance(area_to_qty, list):
            print(f"DEBUG: area_to_qty невалиден: {area_to_qty}")
            return windows_details, total_cost
        
        std_windows_qty = 0
        for rule in sorted(area_to_qty, key=lambda x: x.get('max_m2', 0)):
            if A_house <= rule.get('max_m2', 0):
                std_windows_qty = rule.get('qty', 0)
                break
        
        if std_windows_qty == 0:
            print(f"DEBUG: Количество стандартных окон = 0 для площади {A_house}")
            return windows_details, total_cost
        
        # Находим базовую цену стандартного окна
        # Проверяем тип окна - может быть Enum или строка
        window_type_value = std_inclusion.included_window_type
        if hasattr(window_type_value, 'value'):
            window_type_value = window_type_value.value
        elif isinstance(window_type_value, str):
            pass  # Уже строка
        else:
            window_type_value = str(window_type_value)
        
        print(f"DEBUG: Поиск стандартного окна: {std_inclusion.included_window_width_cm}×{std_inclusion.included_window_height_cm}, тип={window_type_value}")
        
        # Пробуем найти окно, используя Enum если нужно
        std_window_base = db.query(models.WindowBasePrice).filter(
            models.WindowBasePrice.width_cm == std_inclusion.included_window_width_cm,
            models.WindowBasePrice.height_cm == std_inclusion.included_window_height_cm,
            models.WindowBasePrice.type == window_type_value
        ).first()
        
        if not std_window_base:
            # Пробуем найти через сравнение строк или любое окно такого размера
            std_window_base = db.query(models.WindowBasePrice).filter(
                models.WindowBasePrice.width_cm == std_inclusion.included_window_width_cm,
                models.WindowBasePrice.height_cm == std_inclusion.included_window_height_cm
            ).first()
            if std_window_base:
                print(f"DEBUG: Найдено окно размера {std_inclusion.included_window_width_cm}×{std_inclusion.included_window_height_cm}, но с другим типом. Используем его.")
        
        if not std_window_base:
            print(f"DEBUG: Стандартное окно {std_inclusion.included_window_width_cm}×{std_inclusion.included_window_height_cm} типа {window_type_value} не найдено в базе цен")
            return windows_details, total_cost
        
        # Находим модификатор для однокамерного без ламинации
        std_modifier = db.query(models.WindowModifier).filter_by(
            two_chambers=False,
            laminated=False
        ).first()
        
        if std_modifier:
            std_multiplier = float(std_modifier.multiplier)
        else:
            std_multiplier = 1.0
        
        # Рассчитываем стоимость
        base_price = float(std_window_base.base_price_rub)
        price_per_unit = base_price * std_multiplier
        total_cost = price_per_unit * std_windows_qty
        
        # Формируем описание
        size_str = f"{std_inclusion.included_window_width_cm}×{std_inclusion.included_window_height_cm}"
        type_str_map = {
            'gluh': 'глухое',
            'povorot': 'поворотное',
            'povorot_otkid': 'поворотно-откидное'
        }
        type_str = type_str_map.get(window_type_value, window_type_value)
        
        windows_details.append(StandardWindowItem(
            Размер=size_str,
            Тип=type_str,
            Колво=std_windows_qty,
            Цена_шт_руб=round(price_per_unit, 2),
            Сумма_руб=round(total_cost, 2)
        ))
        
        print(f"DEBUG: Стандартные окна: {std_windows_qty} шт, цена за шт: {price_per_unit}, итого: {total_cost}")
        return windows_details, total_cost

    def _calculate_doors_price(self, db: Session, req: CalculateRequestSchema) -> tuple[float, list[DoorItem]]:
        """
        Расчет стоимости дверей (стр. 25 прайса).
        """
        total_cost = 0.0
        doors_details = []

        if not req.doors:
            print("DEBUG: Двери не выбраны (req.doors пустой)")
            return total_cost, doors_details

        print(f"DEBUG: Обработка {len(req.doors)} дверей")
        for door_req in req.doors:
            # 1. Найти цену двери по коду
            door_model = db.query(models.Door).filter_by(code=door_req.code).first()

            if not door_model:
                print(f"DEBUG: Дверь с кодом '{door_req.code}' не найдена в БД")
                continue

            price_per_unit = float(door_model.price_rub)
            total_price = price_per_unit * door_req.quantity
            total_cost += total_price

            # 2. Формируем детали для ответа
            doors_details.append(DoorItem(
                Наименование=door_model.title,
                Колво=door_req.quantity,
                Цена_шт_руб=round(price_per_unit, 2),
                Сумма_руб=round(total_price, 2)
            ))
            print(f"DEBUG: Дверь '{door_model.title}': {door_req.quantity}шт × {price_per_unit}₽ = {total_price}₽")

        print(f"DEBUG: Итого по дверям: {total_cost}₽")
        return total_cost, doors_details
