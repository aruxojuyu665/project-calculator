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
    DoorItem
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
            # Если окна не выбраны, стандартные остаются (уже включены в базовую цену)
            windows_cost_after_replacement = 0.0
        doors_cost, doors_details = self._calculate_doors_cost(db, req)
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
            # TODO: Add proper error handling for missing prices
            return 0.0
        
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
            ridge_height_m = 1.5 + (req.ceiling.ridge_delta_cm / 10) # Примерная логика, нужна точная
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

    def _calculate_doors_cost(self, db: Session, req: CalculateRequestSchema):
        """
        Рассчитывает стоимость дверей на основе стандартных включений.

        В стандартное включение могут входить:
        - Входная дверь (included_entry_door_code) - 1 шт
        - Межкомнатные двери (included_interior_doors_qty) - N шт

        Возвращает (doors_cost, doors_details)
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
            # Если стандартное включение не найдено, возвращаем пустой список
            return 0.0, []

        doors_details = []
        total_doors_cost = 0.0

        # 2. Обрабатываем входную дверь
        if std_inclusion.included_entry_door_code:
            entry_door = db.query(models.Door).filter_by(
                code=std_inclusion.included_entry_door_code
            ).first()

            if entry_door:
                entry_door_price = float(entry_door.price_rub)
                entry_door_qty = 1
                entry_door_total = entry_door_price * entry_door_qty
                total_doors_cost += entry_door_total

                doors_details.append(DoorItem(
                    Наименование=entry_door.title,
                    Колво=entry_door_qty,
                    Цена_шт_руб=entry_door_price,
                    Сумма_руб=entry_door_total
                ))

        # 3. Обрабатываем межкомнатные двери
        if std_inclusion.included_interior_doors_qty and std_inclusion.included_interior_doors_qty > 0:
            # Ищем межкомнатную дверь по коду (обычно используется общий код для всех межкомнатных)
            # Если код не указан в std_inclusion, пробуем найти дверь с кодом содержащим "interior" или "межкомнатная"
            interior_door = db.query(models.Door).filter(
                models.Door.code.ilike('%interior%')
            ).first()

            # Если не нашли, пробуем по title
            if not interior_door:
                interior_door = db.query(models.Door).filter(
                    models.Door.title.ilike('%межкомнатн%')
                ).first()

            if interior_door:
                interior_door_price = float(interior_door.price_rub)
                interior_door_qty = std_inclusion.included_interior_doors_qty
                interior_door_total = interior_door_price * interior_door_qty
                total_doors_cost += interior_door_total

                doors_details.append(DoorItem(
                    Наименование=interior_door.title,
                    Колво=interior_door_qty,
                    Цена_шт_руб=interior_door_price,
                    Сумма_руб=interior_door_total
                ))

        return total_doors_cost, doors_details
