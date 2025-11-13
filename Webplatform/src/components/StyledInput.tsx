import React from 'react';

interface StyledInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  type: 'text' | 'number';
}

const StyledInput: React.FC<StyledInputProps> = ({ label, id, type, ...rest }) => {
  const inputId = id || `input-${label.toLowerCase().replace(/\s/g, '-')}`;

  return (
    <div className="mb-4">
      <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
        {label}
      </label>
      <input
        id={inputId}
        type={type}
        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-150 ease-in-out"
        {...rest}
      />
    </div>
  );
};

export default StyledInput;
