import { useState } from 'react';
import InputField from './InputField';

/**
 * Password input with show/hide toggle.
 */
export default function PasswordInput({
  id = 'password',
  label = 'Password',
  placeholder = 'Enter your password',
  value,
  onChange,
  required,
  hint,
}) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="flex flex-col gap-[4px]">
      <InputField
        id={id}
        label={label}
        icon="lock"
        type={visible ? 'text' : 'password'}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        required={required}
        autoComplete={visible ? 'off' : 'current-password'}
        inputClassName="pr-10"
      >
        <button
          type="button"
          aria-label="Toggle password visibility"
          onClick={() => setVisible((v) => !v)}
          className="absolute right-3 text-[#74777f] hover:text-[#43474e] outline-none"
        >
          <span className="material-symbols-outlined">
            {visible ? 'visibility' : 'visibility_off'}
          </span>
        </button>
      </InputField>
      {hint && (
        <p className="text-[12px] leading-[1.4] text-[#74777f] mt-1">{hint}</p>
      )}
    </div>
  );
}
