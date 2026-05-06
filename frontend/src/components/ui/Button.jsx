/**
 * Primary action button — matches the amber/saffron CTA from the design.
 */
export default function Button({
  children,
  type = 'button',
  onClick,
  loading = false,
  disabled = false,
  className = '',
  variant = 'primary', // 'primary' | 'outline'
}) {
  const base =
    'w-full h-12 rounded-lg font-semibold text-[14px] leading-[1.2] tracking-[0.02em] flex items-center justify-center gap-2 transition-all active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed';

  const variants = {
    primary:
      'bg-[#fea619] text-[#684000] hover:bg-[#855300] hover:text-white shadow-[0px_4px_12px_rgba(254,166,25,0.2)] hover:shadow-[0px_6px_16px_rgba(254,166,25,0.3)]',
    outline:
      'bg-white border border-[#c4c6cf] text-[#191c1e] hover:bg-[#f2f4f6]',
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {loading ? (
        <>
          <span className="material-symbols-outlined animate-spin text-[20px]">
            progress_activity
          </span>
          <span>Please wait…</span>
        </>
      ) : (
        children
      )}
    </button>
  );
}
