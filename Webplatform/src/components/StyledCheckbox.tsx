import React from 'react';

interface StyledCheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
}

const StyledCheckbox: React.FC<StyledCheckboxProps> = ({ label, id, ...rest }) => {
  const checkboxId = id || `checkbox-${label.toLowerCase().replace(/\s/g, '-')}`;

  return (
    <div className="relative flex items-start mb-4">
      <div className="flex items-center h-5">
        <input
          id={checkboxId}
          aria-describedby={`${checkboxId}-description`}
          name={checkboxId}
          type="checkbox"
          className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded transition duration-150 ease-in-out"
          {...rest}
        />
      </div>
      <div className="ml-3 text-sm">
        <label htmlFor={checkboxId} className="font-medium text-gray-700">
          {label}
        </label>
      </div>
    </div>
  );
};

export default StyledCheckbox;
