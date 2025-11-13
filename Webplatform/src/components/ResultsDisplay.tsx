import React from 'react';

// --- TypeScript Interfaces based on API_Spec.json response schema ---

interface Габариты {
  Площадь_теплого_контура_м2: number;
  Площадь_террас_м2: number;
  Площадь_крылец_м2: number;
  Высота_потолка_м: number;
  Тип_потолка: string;
  Повышение_конька_см: number;
  Вынос_крыши: string;
}

interface СтандартноеОкно {
  Размер: string;
  Тип: string;
  Колво: number;
  Цена_шт_руб: number;
  Сумма_руб: number;
}

interface Дверь {
  Наименование: string;
  Колво: number;
  Цена_шт_руб: number;
  Сумма_руб: number;
}

interface ОкнаИДвери {
  Стандартные_окна: СтандартноеОкно[];
  Двери: Дверь[];
  Итого_по_разделу_руб: number;
}

interface Дополнение {
  Код: string;
  Наименование: string;
  Расчёт: string;
  Сумма_руб: number;
}

interface Конструктив {
  База_руб: number;
  Дополнения: Дополнение[];
  Доставка_руб: number;
}

interface ИтоговаяСтоимость {
  Итого_без_комиссии_руб: number;
  Комиссия_руб: number;
  Окончательная_цена_руб: number;
}

export interface CalculateResponseSchema {
  Габариты: Габариты;
  Окна_и_двери: ОкнаИДвери;
  Конструктив: Конструктив;
  Итоговая_стоимость: ИтоговаяСтоимость;
}

// --- Helper function for currency formatting ---

const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

// --- ResultsDisplay Component ---

interface ResultsDisplayProps {
  results: CalculateResponseSchema;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  const { Габариты, Окна_и_двери, Конструктив, Итоговая_стоимость } = results;

  const sectionClass = "mb-8 p-6 bg-white shadow-lg rounded-xl";
  const titleClass = "text-2xl font-bold mb-4 border-b pb-2 text-gray-800";
  const itemClass = "flex justify-between py-1 border-b border-gray-100 last:border-b-0";
  const labelClass = "text-gray-600";
  const valueClass = "font-semibold text-gray-800";

  // 1. Секция 'Габариты'
  const renderГабариты = () => (
    <div className={sectionClass}>
      <h2 className={titleClass}>Габариты</h2>
      <div className="space-y-2">
        <div className={itemClass}>
          <span className={labelClass}>Площадь теплого контура, м²:</span>
          <span className={valueClass}>{Габариты.Площадь_теплого_контура_м2}</span>
        </div>
        <div className={itemClass}>
          <span className={labelClass}>Площадь террас, м²:</span>
          <span className={valueClass}>{Габариты.Площадь_террас_м2}</span>
        </div>
        <div className={itemClass}>
          <span className={labelClass}>Площадь крылец, м²:</span>
          <span className={valueClass}>{Габариты.Площадь_крылец_м2}</span>
        </div>
        <div className={itemClass}>
          <span className={labelClass}>Высота потолка, м:</span>
          <span className={valueClass}>{Габариты.Высота_потолка_м}</span>
        </div>
        <div className={itemClass}>
          <span className={labelClass}>Тип потолка:</span>
          <span className={valueClass}>{Габариты.Тип_потолка}</span>
        </div>
        <div className={itemClass}>
          <span className={labelClass}>Повышение конька, см:</span>
          <span className={valueClass}>{Габариты.Повышение_конька_см}</span>
        </div>
        <div className={itemClass}>
          <span className={labelClass}>Вынос крыши:</span>
          <span className={valueClass}>{Габариты.Вынос_крыши}</span>
        </div>
      </div>
    </div>
  );

  // 2. Секция 'Окна и двери'
  const renderОкнаИДвери = () => (
    <div className={sectionClass}>
      <h2 className={titleClass}>Окна и двери</h2>
      
      <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-700">Стандартные окна</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200">
          <thead>
            <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3 border-b">Наименование</th>
              <th className="px-4 py-3 border-b">Кол-во</th>
              <th className="px-4 py-3 border-b text-right">Цена, шт (руб)</th>
              <th className="px-4 py-3 border-b text-right">Сумма (руб)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {Окна_и_двери.Стандартные_окна.map((окно, index) => (
              <tr key={`window-${index}`} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{`${окно.Размер} (${окно.Тип})`}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{окно.Колво}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">{formatCurrency(окно.Цена_шт_руб)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold text-gray-800 text-right">{formatCurrency(окно.Сумма_руб)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-700">Двери</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200">
          <thead>
            <tr className="bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3 border-b">Наименование</th>
              <th className="px-4 py-3 border-b">Кол-во</th>
              <th className="px-4 py-3 border-b text-right">Цена, шт (руб)</th>
              <th className="px-4 py-3 border-b text-right">Сумма (руб)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {Окна_и_двери.Двери.map((дверь, index) => (
              <tr key={`door-${index}`} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">{дверь.Наименование}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">{дверь.Колво}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-right">{formatCurrency(дверь.Цена_шт_руб)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm font-semibold text-gray-800 text-right">{formatCurrency(дверь.Сумма_руб)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-200 flex justify-between items-center">
        <span className="text-lg font-bold text-gray-700">Итого по разделу:</span>
        <span className="text-xl font-extrabold text-indigo-600">{formatCurrency(Окна_и_двери.Итого_по_разделу_руб)}</span>
      </div>
    </div>
  );

  // 3. Секция 'Конструктив'
  const renderКонструктив = () => (
    <div className={sectionClass}>
      <h2 className={titleClass}>Конструктив</h2>
      
      <div className={itemClass}>
        <span className="text-lg font-bold text-gray-700">Базовая стоимость (руб):</span>
        <span className="text-xl font-extrabold text-gray-800">{formatCurrency(Конструктив.База_руб)}</span>
      </div>

      <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-700">Дополнения</h3>
      <ul className="space-y-2 pl-4 list-disc">
        {Конструктив.Дополнения.map((доп, index) => (
          <li key={`addon-${index}`} className="text-sm text-gray-700">
            <span className="font-medium">{доп.Наименование}</span> ({доп.Расчёт}): <span className="font-semibold">{formatCurrency(доп.Сумма_руб)}</span>
          </li>
        ))}
      </ul>

      <div className="mt-6 pt-4 border-t border-gray-200 flex justify-between items-center">
        <span className="text-lg font-bold text-gray-700">Доставка (руб):</span>
        <span className="text-xl font-extrabold text-gray-800">{formatCurrency(Конструктив.Доставка_руб)}</span>
      </div>
    </div>
  );

  // 4. Секция 'Итоговая стоимость'
  const renderИтоговаяСтоимость = () => (
    <div className={`${sectionClass} bg-indigo-50 border-4 border-indigo-200`}>
      <h2 className="text-3xl font-extrabold mb-4 text-indigo-800">Итоговая стоимость</h2>
      
      <div className={itemClass}>
        <span className={labelClass}>Итого без комиссии (руб):</span>
        <span className={valueClass}>{formatCurrency(Итоговая_стоимость.Итого_без_комиссии_руб)}</span>
      </div>
      <div className={itemClass}>
        <span className={labelClass}>Комиссия (руб):</span>
        <span className={valueClass}>{formatCurrency(Итоговая_стоимость.Комиссия_руб)}</span>
      </div>

      <div className="mt-6 pt-4 border-t-4 border-indigo-300 flex justify-between items-center">
        <span className="text-2xl font-bold text-indigo-800">Окончательная цена:</span>
        <span className="text-5xl font-extrabold text-indigo-900">
          {formatCurrency(Итоговая_стоимость.Окончательная_цена_руб)}
        </span>
      </div>
    </div>
  );

  return (
    <div className="p-4 md:p-8 bg-gray-100 min-h-screen">
      <h1 className="text-3xl font-extrabold text-center mb-10 text-gray-900">Результаты расчета стоимости</h1>
      <div className="max-w-4xl mx-auto">
        {renderГабариты()}
        {renderОкнаИДвери()}
        {renderКонструктив()}
        {renderИтоговаяСтоимость()}
      </div>
    </div>
  );
};

export default ResultsDisplay;
