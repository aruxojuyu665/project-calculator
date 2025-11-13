import os
import json
import gspread
import re
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from typing import Type, List, Dict, Any
from sqlalchemy import Boolean, Integer, SmallInteger, Numeric, Enum, Text

# Импортируем модели из src.models
from src import models
from src.models import Base


# Mapping of Google Sheet names to SQLAlchemy Models
# Ключ - имя листа в Google Sheets, значение - модель SQLAlchemy
SYNC_MAP: Dict[str, Type[Base]] = {
    "addons": models.Addon,
    "window_base_prices": models.WindowBasePrice,
    "window_modifiers": models.WindowModifier,
    "doors": models.Door,
    "delivery_rules": models.DeliveryRule,
    "ceiling_height_prices": models.CeilingHeightPrice,
    "ridge_height_prices": models.RidgeHeightPrice,
    "roof_overhang_prices": models.RoofOverhangPrice,
    "partition_prices": models.PartitionPrice,
    "std_inclusions": models.StdInclusion,
    # base_price_m2 требует дополнительной обработки для преобразования кодов в ID
    # Синхронизируется отдельной функцией sync_base_price_m2
}

def get_gspread_client() -> gspread.Client:
    """Authenticates gspread using the service account key file."""
    # The path to the credentials file saved in the previous step
    CREDENTIALS_FILE = "gspread_credentials.json"
    
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"Credentials file not found at {CREDENTIALS_FILE}. Please ensure it is provided.")

    # gspread.service_account() automatically handles the authentication
    # using the provided JSON file path.
    gc = gspread.service_account(filename=CREDENTIALS_FILE)
    return gc

def fetch_sheet_data(gc: gspread.Client, sheet_name: str) -> List[Dict[str, Any]]:
    """Fetches all data from a specific sheet as a list of dictionaries."""
    SPREADSHEET_TITLE = 'KM_ADM_TABLE'
    
    try:
        # Open the spreadsheet by its title
        sh = gc.open(SPREADSHEET_TITLE)
        
        # Open the specific worksheet by its title
        worksheet = sh.worksheet(sheet_name)
        
        # Get all records as a list of dictionaries (header row is used as keys)
        data = worksheet.get_all_records()
        return data
        
    except gspread.SpreadsheetNotFound:
        print(f"Error: Spreadsheet '{SPREADSHEET_TITLE}' not found.")
        return []
    except gspread.WorksheetNotFound:
        print(f"Error: Worksheet '{sheet_name}' not found in '{SPREADSHEET_TITLE}'.")
        return []
    except Exception as e:
        print(f"An error occurred while fetching data from sheet '{sheet_name}': {e}")
        return []

def transform_data(model: Type[Base], data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transforms raw sheet data into a format suitable for SQLAlchemy insertion.
    This handles type conversions (e.g., string 'True'/'False' to boolean,
    string numbers to float/int) and JSON string parsing.
    
    NOTE: This function does NOT handle foreign key lookups (e.g., converting 
    'neman_plus' to an InsulationBrand ID). That would require a more complex 
    setup and is beyond the scope of a simple sync function without a full 
    ORM context and pre-populated reference tables.
    """
    transformed_data = []
    
    # Get the column names and types from the SQLAlchemy model
    model_columns = {c.key: c.type for c in model.__table__.columns if c.key != 'id'}
    
    for row in data:
        new_row = {}
        for col_name, col_type in model_columns.items():
            # The sheet column names are assumed to match the model column names
            sheet_value = row.get(col_name)
            
            if sheet_value is None or sheet_value == '':
                # Skip if value is missing or empty, letting SQLAlchemy use defaults/nulls
                continue

            try:
                # 1. Handle Boolean
                if isinstance(col_type, Boolean):
                    if isinstance(sheet_value, str):
                        new_row[col_name] = sheet_value.lower() in ('true', '1', 't', 'yes')
                    elif isinstance(sheet_value, int):
                        new_row[col_name] = bool(sheet_value)
                
                # 2. Handle Numeric (Integer, SmallInteger, Numeric)
                elif isinstance(col_type, (Integer, SmallInteger, Numeric)):
                    # Attempt to convert to float first, then to the target type
                    if isinstance(sheet_value, str):
                        # Clean up string: remove non-numeric characters except for a single decimal point
                        # Replace comma with dot for decimal separator
                        sheet_value = sheet_value.replace(',', '.')
                        # Remove all characters that are not digits or a dot
                        sheet_value = re.sub(r'[^\d.]', '', sheet_value)
                        # Handle multiple dots (keep only the first one)
                        if sheet_value.count('.') > 1:
                            parts = sheet_value.split('.', 1)
                            sheet_value = parts[0] + '.' + parts[1].replace('.', '')
                        
                        if not sheet_value:
                            # If the string is empty after cleaning, treat it as 0 or None
                            # We'll treat it as 0 for robust conversion
                            sheet_value = 0
                    
                    if col_type.python_type is int:
                        new_row[col_name] = int(float(sheet_value))
                    else:
                        new_row[col_name] = float(sheet_value)
                
                # 3. Handle Enum
                elif isinstance(col_type, Enum):
                    # Значение из листа должно соответствовать значению enum (например, 'AREA')
                    # Enum в SQLAlchemy может быть определен через python_type или через enum_class
                    try:
                        # Пробуем получить класс enum
                        enum_class = getattr(col_type, 'enum_class', None) or col_type.python_type
                        
                        # Если значение уже является значением enum (например, 'AREA' для AddonCalcModeEnum.AREA)
                        # Проверяем, существует ли такое значение в enum
                        enum_values = [e.value for e in enum_class]
                        if sheet_value in enum_values:
                            new_row[col_name] = sheet_value
                        else:
                            # Пробуем найти по имени атрибута
                            if hasattr(enum_class, sheet_value):
                                new_row[col_name] = getattr(enum_class, sheet_value).value
                            else:
                                new_row[col_name] = sheet_value
                    except Exception as enum_err:
                        # Если не удалось обработать enum, используем исходное значение
                        print(f"Warning: Enum conversion failed for {col_name}: {enum_err}")
                        new_row[col_name] = sheet_value
                
                # 4. Handle JSONB (e.g., for 'params' column in Addon)
                elif isinstance(col_type, JSONB):
                    if isinstance(sheet_value, str):
                        # Attempt to parse JSON string
                        new_row[col_name] = json.loads(sheet_value)
                    else:
                        new_row[col_name] = sheet_value
                
                # 5. Default to raw value for Text/String
                else:
                    new_row[col_name] = sheet_value
                    
            except Exception as e:
                print(f"Warning: Failed to transform value '{sheet_value}' for column '{col_name}' in model {model.__name__}. Error: {e}")
                # If transformation fails, skip this column for this row or use the raw value
                new_row[col_name] = sheet_value # Fallback to raw value
                
        transformed_data.append(new_row)
        
    return transformed_data

def sync_sheet_to_db(db: Session, model: Type[Base], sheet_name: str, gc: gspread.Client):
    """
    Performs the full sync process for a single sheet/model pair.
    """
    print(f"--- Starting sync for sheet '{sheet_name}' to table '{model.__tablename__}' ---")
    
    # 1. Fetch data from Google Sheet
    raw_data = fetch_sheet_data(gc, sheet_name)
    if not raw_data:
        print(f"Skipping sync for {sheet_name}: No data fetched.")
        return

    # 2. Transform data
    transformed_data = transform_data(model, raw_data)
    
    # 3. Truncate the table
    try:
        # Use TRUNCATE for a clean slate, which is often faster than DELETE
        # NOTE: Using 'CASCADE' might be necessary if there are foreign key constraints
        # but for simplicity, I'll use a simple DELETE first as requested.
        # db.execute(text(f"TRUNCATE TABLE {model.__tablename__} RESTART IDENTITY CASCADE;"))
        
        # As requested: db.execute(Addons.__table__.delete())
        db.execute(model.__table__.delete())
        print(f"Truncated table: {model.__tablename__}")
        
    except Exception as e:
        db.rollback()
        print(f"Error truncating table {model.__tablename__}: {e}")
        raise

    # 4. Insert new data
    try:
        # Use bulk insert for efficiency
        db.bulk_insert_mappings(model, transformed_data)
        db.commit()
        print(f"Successfully inserted {len(transformed_data)} records into {model.__tablename__}")
        
    except Exception as e:
        db.rollback()
        print(f"Error inserting data into table {model.__tablename__}: {e}")
        # Print the first few rows that caused the error for debugging
        print(f"First 5 rows of data that failed to insert: {transformed_data[:5]}")
        raise

def sync_base_price_m2(db: Session, gc: gspread.Client):
    """
    Синхронизация base_price_m2 с обработкой foreign keys.
    В Google Sheets должны быть колонки: tech_code, contour_code, brand_code, thickness_mm, storey_type_code, price_rub
    """
    print("--- Starting sync for sheet 'base_price_m2' to table 'base_price_m2' ---")
    
    # 1. Загружаем справочники
    tech_map = {t.code: t.id for t in db.query(models.BuildTechnology).all()}
    contour_map = {c.code: c.id for c in db.query(models.Contour).all()}
    brand_map = {b.code: b.id for b in db.query(models.InsulationBrand).all()}
    thickness_map = {t.mm: t.id for t in db.query(models.InsulationThickness).all()}
    storey_map = {s.code: s.id for s in db.query(models.StoreyType).all()}
    
    # 2. Получаем данные из Google Sheets
    raw_data = fetch_sheet_data(gc, "base_price_m2")
    if not raw_data:
        print("Skipping sync for base_price_m2: No data fetched.")
        return
    
    # 3. Преобразуем данные
    transformed_data = []
    for row in raw_data:
        tech_code = str(row.get('tech_code', '')).strip()
        contour_code = str(row.get('contour_code', '')).strip()
        brand_code = str(row.get('brand_code', '')).strip() if row.get('brand_code') else None
        thickness_mm = row.get('thickness_mm') or row.get('mm')
        storey_code = str(row.get('storey_type_code', '')).strip()
        price_rub = row.get('price_rub')
        
        # Пропускаем строки с пустыми обязательными полями
        if not tech_code or not contour_code or not storey_code or not price_rub:
            print(f"Warning: Skipping row with missing required fields: {row}")
            continue
        
        # Получаем ID из справочников
        tech_id = tech_map.get(tech_code)
        contour_id = contour_map.get(contour_code)
        storey_id = storey_map.get(storey_code)
        
        if not tech_id:
            print(f"Warning: Tech code '{tech_code}' not found. Skipping row: {row}")
            continue
        if not contour_id:
            print(f"Warning: Contour code '{contour_code}' not found. Skipping row: {row}")
            continue
        if not storey_id:
            print(f"Warning: Storey code '{storey_code}' not found. Skipping row: {row}")
            continue
        
        # Для brand и thickness могут быть NULL (для cold контура)
        brand_id = brand_map.get(brand_code) if brand_code else None
        thickness_id = thickness_map.get(int(thickness_mm)) if thickness_mm else None
        
        # Преобразуем цену
        try:
            price = float(str(price_rub).replace(',', '.'))
        except (ValueError, TypeError):
            print(f"Warning: Invalid price value '{price_rub}'. Skipping row: {row}")
            continue
        
        transformed_data.append({
            'tech_id': tech_id,
            'contour_id': contour_id,
            'brand_id': brand_id,
            'thickness_id': thickness_id,
            'storey_type_id': storey_id,
            'price_rub': price,
            'floor_no': row.get('floor_no'),
            'frame_thickness_mm': row.get('frame_thickness_mm')
        })
    
    # 4. Очищаем таблицу
    try:
        db.execute(models.BasePriceM2.__table__.delete())
        print(f"Truncated table: base_price_m2")
    except Exception as e:
        db.rollback()
        print(f"Error truncating table base_price_m2: {e}")
        raise
    
    # 5. Вставляем данные
    try:
        db.bulk_insert_mappings(models.BasePriceM2, transformed_data)
        db.commit()
        print(f"Successfully inserted {len(transformed_data)} records into base_price_m2")
    except Exception as e:
        db.rollback()
        print(f"Error inserting data into table base_price_m2: {e}")
        print(f"First 5 rows of data that failed to insert: {transformed_data[:5]}")
        raise

def sync_google_sheets_to_db(db: Session):
    """
    Main function to synchronize all specified Google Sheets to the database.
    """
    print("Starting Google Sheets to DB synchronization...")
    
    try:
        # 1. Authenticate gspread
        gc = get_gspread_client()
        print("gspread client authenticated successfully.")
        
        # 2. Сначала синхронизируем справочники (если они есть в SYNC_MAP)
        # Но обычно справочники заполняются вручную или через init_data.sql
        
        # 3. Синхронизируем обычные таблицы
        for sheet_name, model in SYNC_MAP.items():
            sync_sheet_to_db(db, model, sheet_name, gc)
        
        # 4. Синхронизируем base_price_m2 с обработкой FK
        try:
            sync_base_price_m2(db, gc)
        except Exception as e:
            print(f"Warning: Failed to sync base_price_m2: {e}")
            # Не прерываем весь процесс, если base_price_m2 не синхронизировался
            
        print("Google Sheets to DB synchronization completed successfully.")
        
    except FileNotFoundError as e:
        print(f"FATAL ERROR: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during synchronization: {e}")
        db.rollback()
        
if __name__ == '__main__':
    # Example usage (requires a running database and a configured Session)
    # This block is for demonstration and will not run in the sandbox without a DB setup.
    
    # from sqlalchemy import create_engine
    # from sqlalchemy.orm import sessionmaker
    
    # # Replace with your actual database URL
    # DATABASE_URL = "postgresql+psycopg2://user:password@host:port/dbname" 
    # engine = create_engine(DATABASE_URL)
    # SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # # Ensure tables are created (only for initial setup)
    # # Base.metadata.create_all(bind=engine)
    
    # # db = SessionLocal()
    # # try:
    # #     sync_google_sheets_to_db(db)
    # # finally:
    # #     db.close()
    print("Script created. Run sync_google_sheets_to_db(db) with a valid SQLAlchemy Session.")
