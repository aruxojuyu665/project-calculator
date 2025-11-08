import enum
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    Boolean,
    Enum,
    DateTime,
    SmallInteger,
    BigInteger,
    Text,
    UniqueConstraint,
    CheckConstraint,
    func
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import JSON

Base = declarative_base()

# Custom ENUM types from the schema
class AddonCalcModeEnum(enum.Enum):
    AREA = 'AREA'
    RUN_M = 'RUN_M'
    PERIMETER = 'PERIMETER'
    COUNT = 'COUNT'
    ROOF_L_SIDES = 'ROOF_L_SIDES'
    M2_PER_HOUSE = 'M2_PER_HOUSE'

class PartitionTypeEnum(enum.Enum):
    plain = 'plain'
    insul50 = 'insul50'
    insul100 = 'insul100'

class WindowTypeEnum(enum.Enum):
    gluh = 'gluh'
    povorot = 'povorot'
    povorot_otkid = 'povorot_otkid'

# 1) Reference tables
class BuildTechnology(Base):
    __tablename__ = 'build_technologies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)

class StoreyType(Base):
    __tablename__ = 'storey_types'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)

class Contour(Base):
    __tablename__ = 'contours'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)

class InsulationBrand(Base):
    __tablename__ = 'insulation_brands'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)

class InsulationThickness(Base):
    __tablename__ = 'insulation_thicknesses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    mm = Column(Integer, unique=True, nullable=False)

# 2) Base price matrix
class BasePriceM2(Base):
    __tablename__ = 'base_price_m2'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tech_id = Column(Integer, ForeignKey('build_technologies.id'), nullable=False)
    contour_id = Column(Integer, ForeignKey('contours.id'), nullable=False)
    brand_id = Column(Integer, ForeignKey('insulation_brands.id'))
    thickness_id = Column(Integer, ForeignKey('insulation_thicknesses.id'))
    storey_type_id = Column(Integer, ForeignKey('storey_types.id'), nullable=False)
    floor_no = Column(SmallInteger)
    frame_thickness_mm = Column(SmallInteger)
    price_rub = Column(Numeric(12, 2), nullable=False)

    technology = relationship("BuildTechnology")
    contour = relationship("Contour")
    brand = relationship("InsulationBrand")
    thickness = relationship("InsulationThickness")
    storey_type = relationship("StoreyType")

    # Примечание: сложное UniqueConstraint с coalesce не поддерживается напрямую в SQLAlchemy
    # Уникальность должна обеспечиваться на уровне базы данных через миграции
    # __table_args__ = (
    #     UniqueConstraint('tech_id', 'contour_id', 'brand_id', 'thickness_id',
    #                      'storey_type_id', 'floor_no', 'frame_thickness_mm',
    #                      name='uniq_base_price'),
    # )

# 3) Dedicated price tables
class CeilingHeightPrice(Base):
    __tablename__ = 'ceiling_height_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    height_m = Column(Numeric(3, 1), unique=True, nullable=False)
    price_per_m2 = Column(Numeric(12, 2), nullable=False)

class RidgeHeightPrice(Base):
    __tablename__ = 'ridge_height_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ridge_height_m = Column(Numeric(3, 1), unique=True, nullable=False)
    price_per_m2 = Column(Numeric(12, 2), nullable=False)

class RoofOverhangPrice(Base):
    __tablename__ = 'roof_overhang_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    overhang_cm = Column(Integer, unique=True, nullable=False)
    price_per_m2 = Column(Numeric(12, 2), nullable=False)

# 4) Generic add-ons
class Addon(Base):
    __tablename__ = 'addons'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    calc_mode = Column(Enum(AddonCalcModeEnum), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    params = Column(JSON, nullable=False, server_default='{}')
    active = Column(Boolean, nullable=False, default=True)

# 5) Partitions
class PartitionPrice(Base):
    __tablename__ = 'partition_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(Enum(PartitionTypeEnum), unique=True, nullable=False)
    price_per_pm = Column(Numeric(12, 2), nullable=False)

# 6) Windows
class WindowBasePrice(Base):
    __tablename__ = 'window_base_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    width_cm = Column(Integer, nullable=False)
    height_cm = Column(Integer, nullable=False)
    type = Column(Enum(WindowTypeEnum), nullable=False)
    base_price_rub = Column(Numeric(12, 2), nullable=False)
    __table_args__ = (UniqueConstraint('width_cm', 'height_cm', 'type', name='uniq_window_size'),)

class WindowModifier(Base):
    __tablename__ = 'window_modifiers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    two_chambers = Column(Boolean, nullable=False)
    laminated = Column(Boolean, nullable=False)
    multiplier = Column(Numeric(6, 3), nullable=False)
    __table_args__ = (UniqueConstraint('two_chambers', 'laminated', name='uniq_window_modifier'),)

# 7) Doors and accessories
class Door(Base):
    __tablename__ = 'doors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    price_rub = Column(Numeric(12, 2), nullable=False)

class DoorAccessory(Base):
    __tablename__ = 'door_accessories'
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(Text, unique=True, nullable=False)
    title = Column(Text, nullable=False)
    unit = Column(Text, nullable=False)
    price_rub = Column(Numeric(12, 2), nullable=False)

# 8) Delivery
class DeliveryRule(Base):
    __tablename__ = 'delivery_rules'
    id = Column(Integer, primary_key=True, autoincrement=True)
    free_km = Column(Integer, nullable=False, default=100)
    rate_per_km = Column(Numeric(10, 2), nullable=False, default=120.00)
    note = Column(Text)

# 9) Standard inclusions
class StdInclusion(Base):
    __tablename__ = 'std_inclusions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tech_id = Column(Integer, ForeignKey('build_technologies.id'), nullable=False)
    contour_id = Column(Integer, ForeignKey('contours.id'), nullable=False)
    storey_type_id = Column(Integer, ForeignKey('storey_types.id'), nullable=False)
    included_window_width_cm = Column(Integer, nullable=False, default=100)
    included_window_height_cm = Column(Integer, nullable=False, default=100)
    included_window_type = Column(Enum(WindowTypeEnum), nullable=False, default='povorot_otkid')
    area_to_qty = Column(JSON, nullable=False)
    included_entry_door_code = Column(Text)
    included_interior_doors_qty = Column(Integer)
    note = Column(Text)

    technology = relationship("BuildTechnology")
    contour = relationship("Contour")
    storey_type = relationship("StoreyType")

    __table_args__ = (UniqueConstraint('tech_id', 'contour_id', 'storey_type_id', name='uniq_std_inclusion'),)

# 10) Global settings / defaults
class GlobalDefault(Base):
    __tablename__ = 'global_defaults'
    id = Column(Integer, primary_key=True, autoincrement=True)
    insulation_brand_id = Column(Integer, ForeignKey('insulation_brands.id'))
    insulation_thickness_id = Column(Integer, ForeignKey('insulation_thicknesses.id'))
    tech_id = Column(Integer, ForeignKey('build_technologies.id'))
    storey_type_id = Column(Integer, ForeignKey('storey_types.id'))
    contour_id = Column(Integer, ForeignKey('contours.id'), default=lambda: 1) # Assuming 1 is 'warm'
    default_commission_rub = Column(Numeric(12, 2), nullable=False, default=0)

    insulation_brand = relationship("InsulationBrand")
    insulation_thickness = relationship("InsulationThickness")
    technology = relationship("BuildTechnology")
    storey_type = relationship("StoreyType")
    contour = relationship("Contour")

# 11) Audit
class PriceAudit(Base):
    __tablename__ = 'price_audit'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    entity = Column(Text, nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    action = Column(Text, nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    payload = Column(JSON, nullable=False)
