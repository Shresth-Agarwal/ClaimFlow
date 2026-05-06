/**
 * Reusable labeled input with a leading Material Symbol icon.
 */
export default function InputField({
  id,
  label,
  icon,
  type = 'text',
  placeholder,
  value,
  onChange,
  required,
  autoComplete,
  children, // optional slot for right-side elements (e.g. password toggle)
  prefix,   // optional inline prefix text (e.g. "+91")
  inputClassName = '',
  ...rest
}) {
  return (
    <div className="flex flex-col gap-[4px]">
      {label && (
        <label
          htmlFor={id}
          className="text-[14px] leading-[1.2] tracking-[0.02em] font-semibold text-[#43474e] ml-1"
        >
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {icon && (
          <span className="material-symbols-outlined absolute left-3 text-[#74777f] pointer-events-none">
            {icon}
          </span>
        )}
        {prefix && (
          <span className="absolute left-[44px] text-[16px] leading-[1.5] text-[#43474e] border-r border-[#c4c6cf] pr-2 py-1 pointer-events-none">
            {prefix}
          </span>
        )}
        <input
          id={id}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          required={required}
          autoComplete={autoComplete}
          className={[
            'w-full h-12 rounded-lg border border-[#c4c6cf] bg-white',
            'text-[16px] leading-[1.5] text-[#191c1e]',
            'focus:border-[#002045] focus:ring-1 focus:ring-[#002045] outline-none transition-shadow',
            'placeholder:text-[#c4c6cf]',
            icon ? 'pl-10' : 'pl-4',
            prefix ? 'pl-[90px]' : '',
            children ? 'pr-10' : 'pr-4',
            inputClassName,
          ]
            .filter(Boolean)
            .join(' ')}
          {...rest}
        />
        {children}
      </div>
    </div>
  );
}
