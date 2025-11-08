import sys
import os
from decimal import Decimal
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.schemas import CalculateRequestSchema, HouseSchema, CeilingSchema, RoofSchema, PartitionsSchema, InsulationSchema, DeliverySchema, WindowSelectionSchema, AddonSchema
from src.pricing_engine import PricingEngine
from src import models

def seed_database(db_session):
    """A comprehensive seeder for the test database."""
    db_session.query(models.BasePriceM2).delete()
    db_session.query(models.CeilingHeightPrice).delete()
    db_session.query(models.RidgeHeightPrice).delete()
    db_session.query(models.RoofOverhangPrice).delete()
    db_session.query(models.PartitionPrice).delete()
    db_session.query(models.Addon).delete()
    db_session.query(models.BuildTechnology).delete()
    db_session.query(models.Contour).delete()
    db_session.query(models.InsulationBrand).delete()
    db_session.query(models.InsulationThickness).delete()
    db_session.query(models.StoreyType).delete()
    db_session.commit()

    tech_panel = models.BuildTechnology(code='panel', title='Панельная')
    tech_frame = models.BuildTechnology(code='frame', title='Каркасная')
    contour_warm = models.Contour(code='warm', title='Теплый')
    brand_izobel = models.InsulationBrand(code='izobel', title='Изобел')
    brand_neman = models.InsulationBrand(code='neman_plus', title='Неман+')
    brand_techno = models.InsulationBrand(code='technonicol', title='Технониколь')
    thick_100 = models.InsulationThickness(mm=100)
    thick_150 = models.InsulationThickness(mm=150)
    thick_200 = models.InsulationThickness(mm=200)
    storey_one = models.StoreyType(code='one', title='Одноэтажный')
    storey_mansard = models.StoreyType(code='mansard', title='Мансардный')
    
    db_session.add_all([
        tech_panel, tech_frame, contour_warm, brand_izobel, brand_neman, brand_techno,
        thick_100, thick_150, thick_200, storey_one, storey_mansard
    ])
    db_session.commit()

    db_session.add_all([
        models.BasePriceM2(tech_id=tech_panel.id, contour_id=contour_warm.id, brand_id=brand_izobel.id, thickness_id=thick_100.id, storey_type_id=storey_one.id, price_rub=Decimal('10000')),
        models.BasePriceM2(tech_id=tech_panel.id, contour_id=contour_warm.id, brand_id=brand_izobel.id, thickness_id=thick_150.id, storey_type_id=storey_one.id, price_rub=Decimal('12000')),
        models.BasePriceM2(tech_id=tech_panel.id, contour_id=contour_warm.id, brand_id=brand_neman.id, thickness_id=thick_150.id, storey_type_id=storey_one.id, price_rub=Decimal('12500')),
        models.BasePriceM2(tech_id=tech_panel.id, contour_id=contour_warm.id, brand_id=brand_izobel.id, thickness_id=thick_200.id, storey_type_id=storey_mansard.id, price_rub=Decimal('15000')),
        models.BasePriceM2(tech_id=tech_frame.id, contour_id=contour_warm.id, brand_id=brand_techno.id, thickness_id=thick_150.id, storey_type_id=storey_one.id, price_rub=Decimal('11000')),
        models.BasePriceM2(tech_id=tech_frame.id, contour_id=contour_warm.id, brand_id=brand_neman.id, thickness_id=thick_200.id, storey_type_id=storey_mansard.id, price_rub=Decimal('18000')),
        models.CeilingHeightPrice(height_m=Decimal('2.4'), price_per_m2=Decimal('0')),
        models.CeilingHeightPrice(height_m=Decimal('2.5'), price_per_m2=Decimal('100')),
        models.CeilingHeightPrice(height_m=Decimal('2.6'), price_per_m2=Decimal('200')),
        models.CeilingHeightPrice(height_m=Decimal('2.7'), price_per_m2=Decimal('300')),
        models.CeilingHeightPrice(height_m=Decimal('2.8'), price_per_m2=Decimal('400')),
        models.CeilingHeightPrice(height_m=Decimal('3.0'), price_per_m2=Decimal('600')),
        models.RoofOverhangPrice(overhang_cm=30, price_per_m2=Decimal('150')),
        models.RoofOverhangPrice(overhang_cm=40, price_per_m2=Decimal('200')),
        models.RoofOverhangPrice(overhang_cm=50, price_per_m2=Decimal('250')),
        models.PartitionPrice(type='plain', price_per_pm=Decimal('1000')),
        models.PartitionPrice(type='insul50', price_per_pm=Decimal('1500')),
        models.PartitionPrice(type='insul100', price_per_pm=Decimal('2000')),
        models.Addon(code='ADDON_AREA', title='Area Addon', calc_mode='AREA', price=Decimal('100')),
        models.Addon(code='ADDON_PERIMETER', title='Perimeter Addon', calc_mode='PERIMETER', price=Decimal('200')),
        models.Addon(code='ADDON_COUNT', title='Count Addon', calc_mode='COUNT', price=Decimal('5000')),
        models.Addon(code='ADDON_ROOF', title='Roof Addon', calc_mode='ROOF_L_SIDES', price=Decimal('300'), params={'sides': 2, 'reserve_m': 1.5}),
    ])
    db_session.commit()

@pytest.fixture
def engine_instance():
    return PricingEngine()

@pytest.fixture
def base_req():
    return CalculateRequestSchema(
        house=HouseSchema(length_m=6.0, width_m=8.0),
        ceiling=CeilingSchema(type='flat', height_m=2.4),
        roof=RoofSchema(overhang_cm='std'),
        partitions=PartitionsSchema(enabled=False),
        insulation=InsulationSchema(brand='izobel', mm=100, build_tech='panel'),
        delivery=DeliverySchema(distance_km=0.0)
    )

class TestBasePrice:
    @pytest.mark.parametrize("brand, mm, tech, storey, expected_price_m2", [
        ('izobel', 100, 'panel', 'one', 10000),
        ('izobel', 150, 'panel', 'one', 12000),
        ('neman_plus', 150, 'panel', 'one', 12500),
        ('izobel', 200, 'panel', 'mansard', 15000),
        ('technonicol', 150, 'frame', 'one', 11000),
        ('neman_plus', 200, 'frame', 'mansard', 18000),
    ])
    def test_matrix_combinations(self, engine_instance, base_req, db_session, brand, mm, tech, storey, expected_price_m2):
        seed_database(db_session)
        base_req.insulation.brand = brand
        base_req.insulation.mm = mm
        base_req.insulation.build_tech = tech
        base_req.ceiling.type = 'rafters' if storey == 'mansard' else 'flat'
        area = base_req.house.length_m * base_req.house.width_m
        price = engine_instance._get_base_price(db_session, base_req, area)
        assert price == pytest.approx(expected_price_m2 * area)

    def test_price_not_found(self, engine_instance, base_req, db_session):
        seed_database(db_session)
        base_req.insulation.brand = 'technonicol'
        area = base_req.house.length_m * base_req.house.width_m
        price = engine_instance._get_base_price(db_session, base_req, area)
        assert price == 0.0

class TestRoofCosts:
    @pytest.mark.parametrize("height, expected_add", [(2.4, 0), (2.5, 100), (2.6, 200), (2.7, 300), (2.8, 400), (3.0, 600)])
    def test_ceiling_height(self, engine_instance, base_req, db_session, height, expected_add):
        seed_database(db_session)
        base_req.ceiling.height_m = height
        area = base_req.house.length_m * base_req.house.width_m
        cost, _ = engine_instance._calculate_roof_costs(db_session, base_req, area)
        assert cost == pytest.approx(area * expected_add)

    @pytest.mark.parametrize("overhang, expected_add", [('std', 0), ('30', 150), ('40', 200), ('50', 250)])
    def test_overhang(self, engine_instance, base_req, db_session, overhang, expected_add):
        seed_database(db_session)
        base_req.roof.overhang_cm = overhang
        area = base_req.house.length_m * base_req.house.width_m
        cost, _ = engine_instance._calculate_roof_costs(db_session, base_req, area)
        assert cost == pytest.approx(area * expected_add)

    def test_ridge_height_ignored_for_rafters(self, engine_instance, base_req, db_session):
        seed_database(db_session)
        base_req.ceiling.type = 'rafters'
        base_req.ceiling.ridge_delta_cm = 50
        area = base_req.house.length_m * base_req.house.width_m
        cost, _ = engine_instance._calculate_roof_costs(db_session, base_req, area)
        assert cost == 0.0

    @pytest.mark.parametrize("delta_cm", [10, 50])
    def test_ridge_height_finds_no_exact_match(self, engine_instance, base_req, db_session, delta_cm):
        seed_database(db_session)
        base_req.ceiling.ridge_delta_cm = delta_cm
        area = base_req.house.length_m * base_req.house.width_m
        cost, _ = engine_instance._calculate_roof_costs(db_session, base_req, area)
        assert cost == 0.0

class TestPartitions:
    @pytest.mark.parametrize("part_type, run_m, expected_price_pm", [('plain', 10, 1000), ('insul50', 20, 1500), ('insul100', 30, 2000)])
    def test_partition_types(self, engine_instance, base_req, db_session, part_type, run_m, expected_price_pm):
        seed_database(db_session)
        base_req.partitions.enabled = True
        base_req.partitions.type = part_type
        base_req.partitions.run_m = run_m
        cost, _ = engine_instance._calculate_partitions_cost(db_session, base_req)
        assert cost == pytest.approx(run_m * expected_price_pm)

    @pytest.mark.parametrize("enabled, p_type, p_run_m", [(False, 'plain', 10), (True, 'none', 10), (True, 'plain', 0), (True, 'plain', None)])
    def test_partitions_zero_cost(self, engine_instance, base_req, db_session, enabled, p_type, p_run_m):
        seed_database(db_session)
        base_req.partitions.enabled = enabled
        base_req.partitions.type = p_type
        base_req.partitions.run_m = p_run_m
        cost, _ = engine_instance._calculate_partitions_cost(db_session, base_req)
        assert cost == 0.0

class TestAddons:
    def test_addon_area(self, engine_instance, base_req, db_session):
        seed_database(db_session)
        base_req.addons = [AddonSchema(code='ADDON_AREA')]
        area = base_req.house.length_m * base_req.house.width_m
        cost, _ = engine_instance._calculate_generic_addons_cost(db_session, base_req, area)
        assert cost == pytest.approx(100 * area)

    def test_addon_perimeter(self, engine_instance, base_req, db_session):
        seed_database(db_session)
        base_req.addons = [AddonSchema(code='ADDON_PERIMETER')]
        area = base_req.house.length_m * base_req.house.width_m
        perimeter = (base_req.house.length_m + base_req.house.width_m) * 2
        cost, _ = engine_instance._calculate_generic_addons_cost(db_session, base_req, area)
        assert cost == pytest.approx(200 * perimeter)

    def test_addon_count(self, engine_instance, base_req, db_session):
        seed_database(db_session)
        base_req.addons = [AddonSchema(code='ADDON_COUNT', quantity=5)]
        area = base_req.house.length_m * base_req.house.width_m
        cost, _ = engine_instance._calculate_generic_addons_cost(db_session, base_req, area)
        assert cost == pytest.approx(5000 * 5)

    def test_addon_roof_l_sides(self, engine_instance, base_req, db_session):
        seed_database(db_session)
        base_req.addons = [AddonSchema(code='ADDON_ROOF')]
        area = base_req.house.length_m * base_req.house.width_m
        l_long = max(base_req.house.length_m, base_req.house.width_m)
        cost, _ = engine_instance._calculate_generic_addons_cost(db_session, base_req, area)
        assert cost == pytest.approx(300 * (l_long + 1.5) * 2)

    def test_addon_not_found(self, engine_instance, base_req, db_session):
        seed_database(db_session)
        base_req.addons = [AddonSchema(code='FAKE_ADDON')]
        area = base_req.house.length_m * base_req.house.width_m
        cost, _ = engine_instance._calculate_generic_addons_cost(db_session, base_req, area)
        assert cost == 0.0
