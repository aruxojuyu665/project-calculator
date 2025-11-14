# Интеграция с Google Sheets

## Обзор

Проект интегрирован с Google Sheets для управления ценами и справочными данными. Все данные синхронизируются из Google Таблицы в базу данных PostgreSQL.

## Связь компонентов

```
┌─────────────────────────────────────┐
│   Google Sheets (KM_ADM_TABLE)      │
│   https://docs.google.com/...       │
│                                      │
│   Листы:                             │
│   - base_price_m2                   │
│   - addons                          │
│   - window_base_prices              │
│   - window_modifiers                │
│   - doors                           │
│   - delivery_rules                  │
│   - std_inclusions                  │
│   - ceiling_height_prices           │
│   - ridge_height_prices             │
│   - roof_overhang_prices            │
│   - partition_prices                │
└──────────────┬──────────────────────┘
               │
               │ Синхронизация
               │ (POST /admin/sync-prices)
               ▼
┌─────────────────────────────────────┐
│   src/sync_service.py               │
│                                      │
│   - get_gspread_client()            │
│   - fetch_sheet_data()              │
│   - transform_data()                │
│   - sync_sheet_to_db()              │
│   - sync_google_sheets_to_db()      │
└──────────────┬──────────────────────┘
               │
               │ Запись данных
               ▼
┌─────────────────────────────────────┐
│   PostgreSQL Database               │
│                                      │
│   Таблицы:                          │
│   - base_price_m2                   │
│   - addons                          │
│   - window_base_prices              │
│   - window_modifiers                │
│   - doors                           │
│   - delivery_rules                  │
│   - std_inclusions                  │
│   - ceiling_height_prices           │
│   - ridge_height_prices             │
│   - roof_overhang_prices            │
│   - partition_prices                │
└──────────────┬──────────────────────┘
               │
               │ Чтение данных
               ▼
┌─────────────────────────────────────┐
│   src/pricing_engine.py             │
│                                      │
│   PricingEngine использует данные   │
│   из БД для расчета стоимости:      │
│   - _get_base_price()               │
│   - _calculate_addons_price()       │
│   - _calculate_windows_price()      │
│   - _get_delivery_price()           │
└──────────────┬──────────────────────┘
               │
               │ Расчет стоимости
               ▼
┌─────────────────────────────────────┐
│   POST /calculate                   │
│   Возвращает CalculateResponseSchema│
└─────────────────────────────────────┘
```

## Настройка

### 1. Создание сервисного аккаунта Google

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите **Google Sheets API**
4. Создайте **Service Account** (Сервисный аккаунт)
5. Создайте ключ (JSON) для сервисного аккаунта
6. Сохраните файл как `gspread_credentials.json` в корне проекта

### 2. Предоставление доступа к Google Sheets

1. Откройте Google Таблицу `KM_ADM_TABLE`
2. Нажмите "Настройки доступа" (Share)
3. Добавьте email сервисного аккаунта (можно найти в `gspread_credentials.json`, поле `client_email`)
4. Предоставьте права **Редактор** (Editor) или **Читатель** (Viewer)

### 3. Структура листов в Google Sheets

Каждый лист в Google Sheets должен соответствовать таблице в базе данных:

#### Лист `addons`
Колонки:
- `code` (Text) - уникальный код дополнения
- `title` (Text) - название
- `calc_mode` (Enum) - режим расчета: AREA, RUN_M, PERIMETER, COUNT, ROOF_L_SIDES, M2_PER_HOUSE
- `price` (Numeric) - цена
- `params` (JSON) - дополнительные параметры (JSON строка)
- `active` (Boolean) - активен ли доп

#### Лист `window_base_prices`
Колонки:
- `width_cm` (Integer) - ширина окна в см
- `height_cm` (Integer) - высота окна в см
- `type` (Enum) - тип окна: gluh, povorot, povorot_otkid
- `base_price_rub` (Numeric) - базовая цена в рублях

#### Лист `window_modifiers`
Колонки:
- `two_chambers` (Boolean) - двухкамерное окно
- `laminated` (Boolean) - ламинация
- `multiplier` (Numeric) - множитель цены

#### Лист `doors`
Колонки:
- `code` (Text) - уникальный код двери
- `title` (Text) - название
- `price_rub` (Numeric) - цена в рублях

#### Лист `delivery_rules`
Колонки:
- `free_km` (Integer) - бесплатная доставка до N км (по умолчанию 100)
- `rate_per_km` (Numeric) - стоимость за км после бесплатного пробега (по умолчанию 120)
- `note` (Text) - примечание

#### Лист `std_inclusions`
Колонки:
- `tech_code` (Text) - код технологии строительства (ссылка на build_technologies.code)
- `contour_code` (Text) - код контура (ссылка на contours.code, например: 'warm')
- `storey_type_code` (Text) - код типа этажности (ссылка на storey_types.code, например: 'one', 'mansard')
- `included_window_width_cm` (Integer) - ширина включенного окна в см (по умолчанию 100)
- `included_window_height_cm` (Integer) - высота включенного окна в см (по умолчанию 100)
- `included_window_type` (Enum) - тип включенного окна: gluh, povorot, povorot_otkid (по умолчанию povorot_otkid)
- `area_to_qty` (JSON) - JSON строка с зависимостью количества от площади, например: `[{"max_m2": 36, "qty": 2}, {"max_m2": 60, "qty": 3}]`
- `included_entry_door_code` (Text) - код входной двери (опционально)
- `included_interior_doors_qty` (Integer) - количество межкомнатных дверей (опционально)
- `note` (Text) - примечание (опционально)

**Важно:** Коды `tech_code`, `contour_code`, `storey_type_code` автоматически преобразуются в соответствующие ID при синхронизации.

## Использование

### Синхронизация данных

Для синхронизации данных из Google Sheets в базу данных используйте эндпоинт:

```bash
POST /admin/sync-prices
```

**Пример запроса:**
```bash
curl -X POST http://localhost:8000/admin/sync-prices
```

**Ответ при успехе:**
```json
{
  "status": "success",
  "message": "Синхронизация данных из Google Sheets завершена успешно"
}
```

### Процесс синхронизации

1. **Аутентификация**: Используется файл `gspread_credentials.json` для подключения к Google Sheets API
2. **Получение данных**: Данные читаются из каждого листа Google Sheets
3. **Преобразование**: Данные преобразуются в формат, подходящий для SQLAlchemy (типы, Enum, JSON)
4. **Очистка таблиц**: Существующие данные удаляются из соответствующих таблиц
5. **Вставка данных**: Новые данные вставляются в базу данных

### Расчет стоимости

После синхронизации данные из Google Sheets доступны в базе данных. `PricingEngine` использует эти данные для расчета стоимости:

- **Базовая цена** - из таблицы `base_price_m2` (синхронизируется вручную или требует дополнительной обработки)
- **Дополнения** - из таблицы `addons`
- **Окна** - из таблиц `window_base_prices` и `window_modifiers`
- **Двери** - из таблицы `doors`
- **Доставка** - из таблицы `delivery_rules`

## Особенности

### Обработка Enum

Значения Enum в Google Sheets должны соответствовать значениям enum в коде. Например:
- Для `calc_mode` используйте: `AREA`, `RUN_M`, `PERIMETER`, `COUNT`, `ROOF_L_SIDES`, `M2_PER_HOUSE`
- Для `type` (окна) используйте: `gluh`, `povorot`, `povorot_otkid`

### Обработка JSON

Поле `params` в таблице `addons` должно быть валидной JSON строкой:
```json
{"key": "value"}
```

### Обработка Boolean

Булевы значения могут быть указаны как:
- `true`, `1`, `t`, `yes` → `True`
- `false`, `0`, `f`, `no` → `False`

### Foreign Keys

Некоторые таблицы требуют преобразования кодов в ID для внешних ключей:

#### Таблица `std_inclusions`
Коды автоматически преобразуются в ID при синхронизации:
- `tech_code` → `tech_id` - ID технологии строительства
- `contour_code` → `contour_id` - ID контура
- `storey_type_code` → `storey_type_id` - ID типа этажности

Синхронизация `std_inclusions` полностью реализована и работает.

#### Таблица `base_price_m2`
Требует преобразования кодов в ID для внешних ключей:
- `tech_id` - ID технологии строительства
- `contour_id` - ID контура
- `brand_id` - ID бренда утеплителя
- `thickness_id` - ID толщины утеплителя
- `storey_type_id` - ID типа этажности

**Примечание**: Синхронизация `base_price_m2` в настоящее время отключена и требует дополнительной обработки для преобразования кодов в ID.

## Отладка

### Ошибки аутентификации

Если возникает ошибка `FileNotFoundError: gspread_credentials.json not found`:
1. Убедитесь, что файл `gspread_credentials.json` существует в корне проекта
2. Проверьте, что файл содержит валидные учетные данные Google

### Ошибки доступа к таблице

Если возникает ошибка `SpreadsheetNotFound`:
1. Убедитесь, что сервисный аккаунт имеет доступ к Google Таблице
2. Проверьте название таблицы: `KM_ADM_TABLE`
3. Проверьте, что email сервисного аккаунта добавлен в список редакторов/читателей

### Ошибки синхронизации данных

Если данные не синхронизируются:
1. Проверьте формат данных в Google Sheets
2. Убедитесь, что названия колонок соответствуют названиям полей в моделях
3. Проверьте типы данных (Enum, Boolean, Numeric)
4. Просмотрите логи для детальной информации об ошибках

## Безопасность

⚠️ **ВАЖНО**: 
- Файл `gspread_credentials.json` содержит секретные данные и **НЕ должен** попадать в Git
- Добавьте `gspread_credentials.json` в `.gitignore`
- Используйте переменные окружения для хранения секретов в продакшене
- Ограничьте доступ к эндпоинту `/admin/sync-prices` (добавьте аутентификацию)



