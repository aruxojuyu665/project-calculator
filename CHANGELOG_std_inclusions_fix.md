# Исправление ошибки tech_id null constraint в std_inclusions

## Проблема

При синхронизации данных из Google Sheets в таблицу `std_inclusions` возникала ошибка:
```
null value in column "tech_id" of relation "std_inclusions" violates not-null constraint
```

Таблица `std_inclusions` имеет три обязательных внешних ключа:
- `tech_id` (ссылка на `build_technologies.id`)
- `contour_id` (ссылка на `contours.id`)
- `storey_type_id` (ссылка на `storey_types.id`)

При синхронизации эти поля не заполнялись, что приводило к нарушению NOT NULL constraint.

## Решение

### 1. Изменения в `src/sync_service.py`

#### 1.1. Исключение std_inclusions из стандартного SYNC_MAP
Таблица `std_inclusions` требует специальной обработки для преобразования кодов в ID.

#### 1.2. Добавлена функция `resolve_foreign_keys()`
```python
def resolve_foreign_keys(db: Session, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

Функция преобразует коды из Google Sheets в ID:
- `tech_code` → `tech_id`
- `contour_code` → `contour_id`
- `storey_type_code` → `storey_type_id`

Создаются lookup-таблицы для быстрого поиска ID по коду.

#### 1.3. Добавлена функция `sync_std_inclusions()`
```python
def sync_std_inclusions(db: Session, gc: gspread.Client)
```

Специальная функция синхронизации для `std_inclusions`:
1. Читает данные из Google Sheets
2. Преобразует данные (типы, JSON, enum)
3. Преобразует коды в ID через `resolve_foreign_keys()`
4. Очищает таблицу
5. Вставляет новые данные

#### 1.4. Обновлена функция `sync_google_sheets_to_db()`
Теперь вызывает `sync_std_inclusions()` после стандартной синхронизации.

### 2. Изменения в документации

#### 2.1. Обновлен `docs/GOOGLE_SHEETS_INTEGRATION.md`

**Добавлена секция для std_inclusions:**
- Описание структуры колонок
- Объяснение преобразования кодов в ID
- Примеры значений enum
- Формат JSON для `area_to_qty`

**Обновлена секция Foreign Keys:**
- Разделена на две подсекции
- Указано, что синхронизация std_inclusions реализована

**Обновлены диаграммы:**
- Добавлены все листы, которые синхронизируются
- Обновлен список таблиц в БД

#### 2.2. Создан новый файл `docs/GOOGLE_SHEETS_STD_INCLUSIONS_EXAMPLE.md`

Подробное руководство по структуре данных для листа `std_inclusions`:
- Описание обязательных и опциональных колонок
- Примеры данных
- Формат JSON для `area_to_qty`
- Список допустимых значений enum
- Объяснение кодов для справочных таблиц
- Инструкции по проверке данных
- Описание процесса синхронизации
- Распространенные ошибки и их решения

### 3. Структура данных в Google Sheets

Для таблицы `std_inclusions` в Google Sheets теперь требуется следующая структура:

**Обязательные колонки:**
- `tech_code` - код технологии (например: 'frame', 'log', 'brick')
- `contour_code` - код контура (например: 'warm', 'cold')
- `storey_type_code` - код типа этажности (например: 'one', 'mansard')
- `included_window_width_cm` - ширина окна в см
- `included_window_height_cm` - высота окна в см
- `included_window_type` - тип окна (enum: 'gluh', 'povorot', 'povorot_otkid')
- `area_to_qty` - JSON строка с зависимостью количества от площади

**Пример:**
```
tech_code | contour_code | storey_type_code | included_window_width_cm | included_window_height_cm | included_window_type | area_to_qty
frame     | warm         | one              | 100                      | 100                       | povorot_otkid        | [{"max_m2": 36, "qty": 2}, {"max_m2": 60, "qty": 3}]
```

## Преимущества решения

1. **Автоматическое преобразование:** Коды автоматически преобразуются в ID, не требуя ручного ввода ID
2. **Читаемость:** Пользователям проще работать с кодами, чем с числовыми ID
3. **Валидация:** Если код не найден, строка пропускается с предупреждением
4. **Безопасность:** Используются транзакции, при ошибке данные откатываются
5. **Расширяемость:** Подход можно использовать для других таблиц с FK (например, `base_price_m2`)

## Тестирование

Для тестирования необходимо:
1. Убедиться, что в Google Sheets есть лист `std_inclusions` с правильной структурой
2. Заполнить справочные таблицы: `build_technologies`, `contours`, `storey_types`
3. Вызвать эндпоинт: `POST /admin/sync-prices`
4. Проверить логи на наличие ошибок
5. Проверить данные в таблице `std_inclusions`

## Миграция существующих данных

Если в Google Sheets уже есть данные с колонками `tech_id`, `contour_id`, `storey_type_id`:
1. Переименуйте колонки: `tech_id` → `tech_code` и т.д.
2. Замените числовые ID на соответствующие коды из справочных таблиц
3. Запустите синхронизацию

## Файлы, затронутые изменениями

- `src/sync_service.py` - основной код синхронизации
- `docs/GOOGLE_SHEETS_INTEGRATION.md` - обновленная документация
- `docs/GOOGLE_SHEETS_STD_INCLUSIONS_EXAMPLE.md` - новое подробное руководство
- `CHANGELOG_std_inclusions_fix.md` - этот файл

## Дополнительные улучшения

В будущем можно:
1. Добавить аналогичную обработку для `base_price_m2`
2. Добавить более детальное логирование
3. Добавить валидацию данных перед вставкой
4. Создать unit-тесты для `resolve_foreign_keys()`
5. Добавить обработку других таблиц с FK
