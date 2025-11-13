import React from 'react';

interface Option {
  value: string;
  label: string;
}

interface StyledSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: Option[];
}

const StyledSelect: React.FC<StyledSelectProps> = ({ label, options, id, ...rest }) => {
  const selectId = id || `select-${label.toLowerCase().replace(/\s/g, '-')}`;

  return (
    <div className="mb-4">
      <label htmlFor={selectId} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <select
        id={selectId}
        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md shadow-sm transition duration-150 ease-in-out"
        {...rest}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};

export default StyledSelect;
