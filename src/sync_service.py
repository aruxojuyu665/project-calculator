import os
import json
import gspread
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
    # std_inclusions требует дополнительной обработки для преобразования кодов в ID
    # "std_inclusions": models.StdInclusion,  # Отключено, требует специальной обработки
    # base_price_m2 требует дополнительной обработки для преобразования кодов в ID
    # "base_price_m2": models.BasePriceM2,  # Пока отключено, требует доработки
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
                        # Clean up string (e.g., remove spaces, replace comma)
                        sheet_value = sheet_value.replace(' ', '').replace(',', '.')
                    
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

def resolve_foreign_keys(db: Session, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Resolves foreign key codes to IDs for std_inclusions table.

    Expected columns in Google Sheets (option 1 - codes):
    - tech_code -> tech_id
    - contour_code -> contour_id
    - storey_type_code -> storey_type_id

    Or (option 2 - direct IDs):
    - tech_id
    - contour_id
    - storey_type_id

    If codes are missing, tries to use first available ID from reference tables.
    """
    # Build lookup dictionaries
    tech_lookup = {t.code: t.id for t in db.query(models.BuildTechnology).all()}
    contour_lookup = {c.code: c.id for c in db.query(models.Contour).all()}
    storey_lookup = {s.code: s.id for s in db.query(models.StoreyType).all()}

    # Get default IDs (first record from each table)
    default_tech_id = db.query(models.BuildTechnology.id).first()
    default_contour_id = db.query(models.Contour.id).first()
    default_storey_id = db.query(models.StoreyType.id).first()

    if not default_tech_id or not default_contour_id or not default_storey_id:
        print("ERROR: Reference tables (build_technologies, contours, storey_types) are empty!")
        print("Please populate these tables before syncing std_inclusions.")
        return []

    default_tech_id = default_tech_id[0]
    default_contour_id = default_contour_id[0]
    default_storey_id = default_storey_id[0]

    resolved_data = []
    for row in data:
        new_row = row.copy()
        skip_row = False

        # Resolve tech_code -> tech_id or use existing tech_id or use default
        if 'tech_code' in new_row:
            tech_code = new_row.pop('tech_code')
            if tech_code and tech_code in tech_lookup:
                new_row['tech_id'] = tech_lookup[tech_code]
            elif tech_code:
                print(f"Warning: Unknown tech_code '{tech_code}', using default tech_id={default_tech_id}")
                new_row['tech_id'] = default_tech_id
        elif 'tech_id' not in new_row or not new_row.get('tech_id'):
            print(f"Warning: No tech_code or tech_id provided, using default tech_id={default_tech_id}")
            new_row['tech_id'] = default_tech_id

        # Resolve contour_code -> contour_id or use existing contour_id or use default
        if 'contour_code' in new_row:
            contour_code = new_row.pop('contour_code')
            if contour_code and contour_code in contour_lookup:
                new_row['contour_id'] = contour_lookup[contour_code]
            elif contour_code:
                print(f"Warning: Unknown contour_code '{contour_code}', using default contour_id={default_contour_id}")
                new_row['contour_id'] = default_contour_id
        elif 'contour_id' not in new_row or not new_row.get('contour_id'):
            print(f"Warning: No contour_code or contour_id provided, using default contour_id={default_contour_id}")
            new_row['contour_id'] = default_contour_id

        # Resolve storey_type_code -> storey_type_id or use existing storey_type_id or use default
        if 'storey_type_code' in new_row:
            storey_code = new_row.pop('storey_type_code')
            if storey_code and storey_code in storey_lookup:
                new_row['storey_type_id'] = storey_lookup[storey_code]
            elif storey_code:
                print(f"Warning: Unknown storey_type_code '{storey_code}', using default storey_type_id={default_storey_id}")
                new_row['storey_type_id'] = default_storey_id
        elif 'storey_type_id' not in new_row or not new_row.get('storey_type_id'):
            print(f"Warning: No storey_type_code or storey_type_id provided, using default storey_type_id={default_storey_id}")
            new_row['storey_type_id'] = default_storey_id

        if not skip_row:
            resolved_data.append(new_row)

    return resolved_data

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

def sync_std_inclusions(db: Session, gc: gspread.Client):
    """
    Special sync function for std_inclusions table that handles foreign key resolution.
    """
    sheet_name = "std_inclusions"
    model = models.StdInclusion

    print(f"--- Starting sync for sheet '{sheet_name}' to table '{model.__tablename__}' (with FK resolution) ---")

    # 1. Fetch data from Google Sheet
    raw_data = fetch_sheet_data(gc, sheet_name)
    if not raw_data:
        print(f"Skipping sync for {sheet_name}: No data fetched.")
        return

    # 2. Transform data
    transformed_data = transform_data(model, raw_data)

    # 3. Resolve foreign keys (convert codes to IDs)
    resolved_data = resolve_foreign_keys(db, transformed_data)

    if not resolved_data:
        print(f"Warning: No valid data to insert after FK resolution for {sheet_name}")
        return

    # 4. Truncate the table
    try:
        db.execute(model.__table__.delete())
        print(f"Truncated table: {model.__tablename__}")

    except Exception as e:
        db.rollback()
        print(f"Error truncating table {model.__tablename__}: {e}")
        raise

    # 5. Insert new data
    try:
        db.bulk_insert_mappings(model, resolved_data)
        db.commit()
        print(f"Successfully inserted {len(resolved_data)} records into {model.__tablename__}")

    except Exception as e:
        db.rollback()
        print(f"Error inserting data into table {model.__tablename__}: {e}")
        print(f"First 5 rows of data that failed to insert: {resolved_data[:5]}")
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

        # 2. Iterate through all sheets and sync
        for sheet_name, model in SYNC_MAP.items():
            sync_sheet_to_db(db, model, sheet_name, gc)

        # 3. Sync std_inclusions with special FK resolution
        sync_std_inclusions(db, gc)

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
