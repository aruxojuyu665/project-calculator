import React, { useState, useCallback, ChangeEvent, FormEvent } from 'react';
import axios from 'axios';
import { CalculateResponseSchema } from './ResultsDisplay'; // Import type from ResultsDisplay

// --- Styled Components with Tailwind CSS ---

const inputBaseClasses = "mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm";
const labelBaseClasses = "block text-sm font-medium text-gray-700";

type StyledInputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};
const StyledInput: React.FC<StyledInputProps> = ({ label, name, ...props }) => (
  <div>
    <label htmlFor={name} className={labelBaseClasses}>{label}</label>
    <input id={name} name={name} {...props} className={inputBaseClasses} />
  </div>
);

type Option = { value: string | number; label: string };
type StyledSelectProps = React.SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  options: Option[];
};
const StyledSelect: React.FC<StyledSelectProps> = ({ label, name, options, ...props }) => (
  <div>
    <label htmlFor={name} className={labelBaseClasses}>{label}</label>
    <select id={name} name={name} {...props} className={inputBaseClasses}>
      <option value="" disabled>Выберите...</option>
      {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
  </select>
  </div>
);

type StyledCheckboxProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};
const StyledCheckbox: React.FC<StyledCheckboxProps> = ({ label, name, ...props }) => (
  <div className="flex items-center">
    <input id={name} name={name} type="checkbox" {...props} className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500" />
    <label htmlFor={name} className="ml-2 block text-sm text-gray-900">{label}</label>
  </div>
);


// --- TypeScript Interfaces for State (based on API_Spec.json requestBody) ---

interface House {
  length_m: number;
  width_m: number;
}

interface Accessory {
  enabled: boolean;
  length_m: number;
  width_m: number;
}

interface Terrace {
  primary: Accessory;
  extra: Accessory;
}

interface Porch {
  primary: Accessory;
  extra: Accessory;
}

interface Ceiling {
  type: 'flat' | 'rafters' | '';
  height_m: number | '';
  ridge_delta_cm?: number | '';
}

interface Roof {
  overhang_cm: 'std' | '30' | '40' | '50';
}

interface Partitions {
  enabled: boolean;
  type?: 'plain' | 'insul50' | 'insul100' | '';
  run_m: number;
}

interface Insulation {
    brand?: 'izobel' | 'neman_plus' | 'technonicol' | '';
    mm?: 100 | 150 | 200 | '';
  build_tech: 'panel' | 'frame';
    contour: 'cold' | 'warm';
    frame_mm?: 100 | 150 | '';
}

interface Delivery {
  distance_km: number;
}

interface Addon {
  code: string;
  quantity: number;
}

interface Window {
  width_cm: number;
  height_cm: number;
  type: 'gluh' | 'povorot' | 'povorot_otkid';
  quantity: number;
  dual_chamber: boolean;
  laminated: boolean;
}

interface CalculatorState {
  house: House;
  terrace: Terrace;
  porch: Porch;
  ceiling: Ceiling;
  roof: Roof;
  partitions: Partitions;
  insulation: Insulation;
  delivery: Delivery;
  commission_rub: number;
  // Arrays are complex to manage in a simple form, so we initialize them empty
  addons: Addon[];
  windows: Window[];
}

// --- Initial State (based on schema defaults) ---

const INITIAL_STATE: CalculatorState = {
  house: { length_m: 6, width_m: 6 },
  terrace: {
    primary: { enabled: false, length_m: 0, width_m: 0 },
    extra: { enabled: false, length_m: 0, width_m: 0 },
  },
  porch: {
    primary: { enabled: false, length_m: 0, width_m: 0 },
    extra: { enabled: false, length_m: 0, width_m: 0 },
  },
  ceiling: { type: 'rafters', height_m: 2.4 }, // Установлены значения по умолчанию
  roof: { overhang_cm: 'std' },
  partitions: { enabled: false, run_m: 0 }, // type убран, т.к. он опционален
  insulation: { 
    build_tech: 'panel',
    contour: 'warm', // По умолчанию 'теплый'
    brand: 'izobel', 
    mm: 150,
    frame_mm: '', // Добавляем frame_mm в начальное состояние
  },
  delivery: { distance_km: 100 },
  commission_rub: 0,
  addons: [],
  windows: [],
};

// --- TypeScript Interfaces for API Response ---

interface GabaritySchema {
  'Площадь_теплого_контура_м2': number;
  'Площадь_террас_м2': number;
  'Площадь_крылец_м2': number;
  'Высота_потолка_м': number;
  'Тип_потолка': string;
  'Повышение_конька_см': number;
  'Вынос_крыши': string;
}

interface StandardWindowItem {
  'Размер': string;
  'Тип': string;
  'Колво': number;
  'Цена_шт_руб': number;
  'Сумма_руб': number;
}

interface DoorItem {
  'Наименование': string;
  'Колво': number;
  'Цена_шт_руб': number;
  'Сумма_руб': number;
}

interface OknaIDveriSchema {
  'Стандартные_окна': StandardWindowItem[];
  'Двери': DoorItem[];
  'Итого_по_разделу_руб': number;
}

interface DopolneniyaItem {
  'Код': string;
  'Наименование': string;
  'Расчёт': string;
  'Сумма_руб': number;
}

interface KonstruktivSchema {
  'База_руб': number;
  'Дополнения': DopolneniyaItem[];
  'Доставка_руб': number;
}

interface ItogovayaStoimostSchema {
  'Итого_без_комиссии_руб': number;
  'Комиссия_руб': number;
  'Окончательная_цена_руб': number;
}

interface CalculateResponseSchema {
  'Габариты': GabaritySchema;
  'Окна_и_двери': OknaIDveriSchema;
  'Конструктив': KonstruktivSchema;
  'Итоговая_стоимость': ItogovayaStoimostSchema;
}

interface CalculatorFormProps {
  onCalculateSuccess: (data: CalculateResponseSchema) => void;
}


// --- Component ---

const CalculatorForm: React.FC<CalculatorFormProps> = ({ onCalculateSuccess }) => {
  const [formData, setFormData] = useState<CalculatorState>(INITIAL_STATE);

  // Function to handle changes for nested fields (e.g., house.length_m)
  const handleChange = useCallback((event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = event.target;
    const isCheckbox = type === 'checkbox';
    const isNumber = type === 'number';
    const checked = (event.target as HTMLInputElement).checked;
    // Поля, которые должны быть числами даже если приходят из <select>
    const numericSelectFields = new Set([
      'ceiling.height_m',
      'ceiling.ridge_delta_cm',
      'partitions.run_m',
      'insulation.mm',
      'insulation.frame_mm',
      'delivery.distance_km',
      'house.length_m',
      'house.width_m',
      'commission_rub'
    ]);

    // Split the name into parts (e.g., ['house', 'length_m'])
    const nameParts = name.split('.');

    setFormData(prevData => {
      // Create a deep copy of the previous state
      const newData = JSON.parse(JSON.stringify(prevData)) as CalculatorState;

      let currentLevel: any = newData;
      // Traverse the object structure up to the parent of the field being updated
      for (let i = 0; i < nameParts.length - 1; i++) {
        currentLevel = currentLevel[nameParts[i]];
      }

      const finalKey = nameParts[nameParts.length - 1];
      let finalValue: any;

      if (isCheckbox) {
        finalValue = checked;
      } else if (isNumber) {
        // Convert to number, but if input is cleared, keep it as an empty string for controlled components
        finalValue = value === '' ? '' : parseFloat(value);
      } else if (numericSelectFields.has(name)) {
        // Принудительно конвертируем значения select для числовых полей
        finalValue = value === '' ? '' : parseFloat(value);
      } else {
        finalValue = value;
      }

      currentLevel[finalKey] = finalValue;

      // --- НОВАЯ ЛОГИКА ОЧИСТКИ ---
      if (name === 'insulation.contour') {
        const newContour = value as 'warm' | 'cold';
        newData.insulation.contour = newContour;
        if (newContour === 'warm') {
          // Очищаем поле холодного контура
          newData.insulation.frame_mm = ''; 
          // Устанавливаем значения по умолчанию для теплого
          newData.insulation.brand = 'izobel';
          newData.insulation.mm = 150;
        } else { // cold
          // Очищаем поля теплого контура
          newData.insulation.brand = '';
          newData.insulation.mm = '';
          // Устанавливаем значение по умолчанию для холодного
          newData.insulation.frame_mm = 100;
        }
      }
      // --- КОНЕЦ НОВОЙ ЛОГИКИ ---

      return newData;
    });
  }, []);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();

    // Создаем глубокую копию данных для безопасной мутации
    const dataToSend = JSON.parse(JSON.stringify(formData));

    // --- ФИНАЛЬНАЯ ЛОГИКА ОЧИСТКИ ---
    if (dataToSend.insulation.contour === 'warm') {
      delete dataToSend.insulation.frame_mm;
      // Убеждаемся, что обязательные поля для теплого контура не пустые
      if (!dataToSend.insulation.brand || !dataToSend.insulation.mm) {
        console.error("Для теплого контура должны быть выбраны бренд и толщина утеплителя.");
        return; // Прерываем отправку
      }
    } else if (dataToSend.insulation.contour === 'cold') {
      delete dataToSend.insulation.brand;
      delete dataToSend.insulation.mm;
       // Убеждаемся, что обязательное поле для холодного контура не пустое
      if (!dataToSend.insulation.frame_mm) {
        console.error("Для холодного контура должна быть выбрана толщина каркаса.");
        return; // Прерываем отправку
      }
    }
    // --- КОНЕЦ ФИНАЛЬНОЙ ЛОГИКИ ---
    
    // Удаляем другие необязательные поля, если они пустые
    if (dataToSend.ceiling.type !== 'flat' || !dataToSend.ceiling.ridge_delta_cm) {
      delete dataToSend.ceiling.ridge_delta_cm;
    }
    if (!dataToSend.partitions.enabled || !dataToSend.partitions.type) {
      delete dataToSend.partitions.type;
    }

    console.log('Form Data to Send:', dataToSend);
    
    axios.post('http://localhost:8000/calculate', dataToSend)
      .then(response => {
        onCalculateSuccess(response.data);
        console.log('API Response:', response.data);
      })
      .catch(error => {
        if (error.response) {
            console.error('Validation Error:', error.response.data);
        } else {
        console.error('There was an error!', error);
        }
      });
  };

  // Helper function to create a bound change handler for StyledCheckbox
  const handleCheckboxChange = (name: string) => (event: ChangeEvent<HTMLInputElement>) => {
    // Create a synthetic event object that mimics the structure expected by handleChange
    const syntheticEvent = {
      target: {
        name: name,
        value: event.target.checked ? 'true' : 'false', // Value is not strictly used for checkbox, but good practice
        type: 'checkbox',
        checked: event.target.checked,
      }
    } as ChangeEvent<HTMLInputElement>;
    handleChange(syntheticEvent);
  };

  // --- Render Logic ---

  return (
    <div className="p-8 bg-white shadow-xl rounded-2xl max-w-4xl mx-auto my-10">
      <h1 className="text-3xl font-bold mb-8 text-center text-gray-800">Калькулятор</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        
        {/* House Parameters */}
        <fieldset className="p-4 border rounded-lg">
          <legend className="text-xl font-semibold px-2">Параметры Дома</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
      <StyledInput
        type="number"
        label="Длина дома (м)"
        name="house.length_m"
        value={formData.house.length_m}
        onChange={handleChange}
        min={1}
        step={0.1}
      />
      <StyledInput
        type="number"
        label="Ширина дома (м)"
        name="house.width_m"
        value={formData.house.width_m}
        onChange={handleChange}
        min={1}
        step={0.1}
      />
          </div>
        </fieldset>

        {/* Ceiling */}
        <fieldset className="p-4 border rounded-lg">
          <legend className="text-xl font-semibold px-2">Потолок</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
      <StyledSelect
        label="Тип потолка"
        name="ceiling.type"
        value={formData.ceiling.type}
        onChange={handleChange}
        options={[
          { value: 'flat', label: 'Ровный' },
          { value: 'rafters', label: 'По стропилам' },
        ]}
      />
      <StyledSelect
        label="Высота потолка (м)"
        name="ceiling.height_m"
        value={formData.ceiling.height_m}
        onChange={handleChange}
        options={[2.4, 2.5, 2.6, 2.7, 2.8, 3.0].map(v => ({ value: v, label: v.toString() }))}
      />
      {formData.ceiling.type === 'flat' && (
        <StyledSelect
          label="Повышение конька (см)"
          name="ceiling.ridge_delta_cm"
          value={formData.ceiling.ridge_delta_cm}
          onChange={handleChange}
          options={[0, 10, 20, 30, 40, 50, 60].map(v => ({ value: v, label: v.toString() }))}
        />
      )}
          </div>
        </fieldset>

        {/* Roof */}
        <fieldset className="p-4 border rounded-lg">
          <legend className="text-xl font-semibold px-2">Крыша</legend>
          <div className="mt-4">
      <StyledSelect
        label="Вынос крыши (см)"
        name="roof.overhang_cm"
        value={formData.roof.overhang_cm}
        onChange={handleChange}
        options={[
          { value: 'std', label: 'Стандартный' },
          { value: '30', label: '30 см' },
          { value: '40', label: '40 см' },
          { value: '50', label: '50 см' },
        ]}
      />
          </div>
        </fieldset>

        {/* Partitions */}
        <fieldset className="p-4 border rounded-lg">
          <legend className="text-xl font-semibold px-2">Перегородки</legend>
          <div className="mt-4 space-y-4">
      <StyledCheckbox
        label="Включить перегородки"
        name="partitions.enabled"
        checked={formData.partitions.enabled}
        onChange={handleCheckboxChange("partitions.enabled")}
      />
      {formData.partitions.enabled && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <StyledSelect
            label="Тип перегородок"
            name="partitions.type"
            value={formData.partitions.type}
            onChange={handleChange}
            options={[
              { value: 'plain', label: 'Простые' },
              { value: 'insul50', label: 'Утепление 50мм' },
              { value: 'insul100', label: 'Утепление 100мм' },
            ]}
          />
          <StyledInput
            type="number"
                  label="Общая длина (м)"
            name="partitions.run_m"
            value={formData.partitions.run_m}
            onChange={handleChange}
            min={0}
            step={0.1}
          />
              </div>
      )}
          </div>
        </fieldset>

        {/* Insulation */}
        <fieldset className="p-4 border rounded-lg">
          <legend className="text-xl font-semibold px-2">Утепление и Контур</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {/* Contour Selection */}
            <div className="col-span-1 md:col-span-2">
              <label className={labelBaseClasses}>Тип контура</label>
              <div className="mt-2 flex space-x-4">
                <label className="flex items-center">
                  <input type="radio" name="insulation.contour" value="warm" checked={formData.insulation.contour === 'warm'} onChange={handleChange} className="form-radio" />
                  <span className="ml-2">Теплый</span>
                </label>
                <label className="flex items-center">
                  <input type="radio" name="insulation.contour" value="cold" checked={formData.insulation.contour === 'cold'} onChange={handleChange} className="form-radio" />
                  <span className="ml-2">Холодный</span>
                </label>
              </div>
            </div>

            {/* Build Technology */}
            <StyledSelect
              label="Технология"
              name="insulation.build_tech"
              value={formData.insulation.build_tech}
              onChange={handleChange}
              options={[
                { value: 'panel', label: 'Панельная' },
                { value: 'frame', label: 'Каркасная' },
              ]}
            />
            
            {/* Conditional Fields */}
            {formData.insulation.contour === 'warm' ? (
              <>
      <StyledSelect
        label="Бренд утеплителя"
        name="insulation.brand"
        value={formData.insulation.brand}
        onChange={handleChange}
        options={[
          { value: 'izobel', label: 'Izobel' },
          { value: 'neman_plus', label: 'Neman Plus' },
          { value: 'technonicol', label: 'Technonicol' },
        ]}
      />
      <StyledSelect
        label="Толщина утеплителя (мм)"
        name="insulation.mm"
        value={formData.insulation.mm}
        onChange={handleChange}
        options={[100, 150, 200].map(v => ({ value: v, label: v.toString() }))}
      />
              </>
            ) : (
      <StyledSelect
                label="Толщина каркаса (мм)"
                name="insulation.frame_mm"
                value={formData.insulation.frame_mm}
        onChange={handleChange}
                options={[100, 150].map(v => ({ value: v, label: v.toString() }))}
      />
            )}
          </div>
        </fieldset>
        
        {/* Terrace */}
        <fieldset className="p-4 border rounded-lg">
          <legend className="text-xl font-semibold px-2">Террасы и Крыльца</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-4">
            {/* Primary Terrace */}
            <div className="space-y-4">
      <StyledCheckbox
        label="Включить основную террасу"
        name="terrace.primary.enabled"
        checked={formData.terrace.primary.enabled}
        onChange={handleCheckboxChange("terrace.primary.enabled")}
      />
      {formData.terrace.primary.enabled && (
                <div className="pl-4 space-y-4">
                  <StyledInput type="number" label="Длина (м)" name="terrace.primary.length_m" value={formData.terrace.primary.length_m} onChange={handleChange} min={0} step={0.1} />
                  <StyledInput type="number" label="Ширина (м)" name="terrace.primary.width_m" value={formData.terrace.primary.width_m} onChange={handleChange} min={0} step={0.1} />
                </div>
      )}
            </div>
            {/* Extra Terrace */}
            <div className="space-y-4">
      <StyledCheckbox
                label="Включить доп. террасу"
        name="terrace.extra.enabled"
        checked={formData.terrace.extra.enabled}
        onChange={handleCheckboxChange("terrace.extra.enabled")}
      />
      {formData.terrace.extra.enabled && (
                <div className="pl-4 space-y-4">
                  <StyledInput type="number" label="Длина (м)" name="terrace.extra.length_m" value={formData.terrace.extra.length_m} onChange={handleChange} min={0} step={0.1} />
                  <StyledInput type="number" label="Ширина (м)" name="terrace.extra.width_m" value={formData.terrace.extra.width_m} onChange={handleChange} min={0} step={0.1} />
                </div>
      )}
            </div>
             {/* Primary Porch */}
            <div className="space-y-4">
      <StyledCheckbox
        label="Включить основное крыльцо"
        name="porch.primary.enabled"
        checked={formData.porch.primary.enabled}
        onChange={handleCheckboxChange("porch.primary.enabled")}
      />
      {formData.porch.primary.enabled && (
                <div className="pl-4 space-y-4">
                  <StyledInput type="number" label="Длина (м)" name="porch.primary.length_m" value={formData.porch.primary.length_m} onChange={handleChange} min={0} step={0.1} />
                  <StyledInput type="number" label="Ширина (м)" name="porch.primary.width_m" value={formData.porch.primary.width_m} onChange={handleChange} min={0} step={0.1} />
                </div>
      )}
            </div>
            {/* Extra Porch */}
            <div className="space-y-4">
      <StyledCheckbox
                label="Включить доп. крыльцо"
        name="porch.extra.enabled"
        checked={formData.porch.extra.enabled}
        onChange={handleCheckboxChange("porch.extra.enabled")}
      />
      {formData.porch.extra.enabled && (
                <div className="pl-4 space-y-4">
                  <StyledInput type="number" label="Длина (м)" name="porch.extra.length_m" value={formData.porch.extra.length_m} onChange={handleChange} min={0} step={0.1} />
                  <StyledInput type="number" label="Ширина (м)" name="porch.extra.width_m" value={formData.porch.extra.width_m} onChange={handleChange} min={0} step={0.1} />
                </div>
              )}
            </div>
          </div>
        </fieldset>
        
        {/* Other */}
        <fieldset className="p-4 border rounded-lg">
          <legend className="text-xl font-semibold px-2">Прочее</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <StyledInput
            type="number"
              label="Расстояние доставки (км)"
              name="delivery.distance_km"
              value={formData.delivery.distance_km}
            onChange={handleChange}
            min={0}
              step={1}
          />
      <StyledInput
        type="number"
        label="Комиссия агента (руб)"
        name="commission_rub"
        value={formData.commission_rub}
        onChange={handleChange}
        min={0}
        step={1}
      />
          </div>
        </fieldset>

        <button 
          type="submit" 
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-lg font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
        >
        Рассчитать
      </button>
    </form>
    </div>
  );
};

export default CalculatorForm;
