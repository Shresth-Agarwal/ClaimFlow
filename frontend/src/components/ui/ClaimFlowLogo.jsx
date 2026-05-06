/**
 * ClaimFlowLogo
 * Inline SVG logo — faithfully recreated from the brand image.
 * Shield mark: navy (#002045) outer shield + amber (#fea619) upward arrow/wave.
 * Wordmark: "Claim" in navy, "Flow" in amber.
 *
 * Variants:
 *   "full"    — shield + "ClaimFlow" wordmark (default, light backgrounds)
 *   "dark"    — shield + "CLAIM FLOW" all-white (dark backgrounds)
 *   "compact" — smaller shield + wordmark (footer compact)
 *   "icon"    — shield mark only, no text (favicon / minimal navbar)
 *
 * Props:
 *   variant  : 'full' | 'dark' | 'compact' | 'icon'
 *   className: extra classes for the wrapper
 *   height   : number (px) — controls overall size, default varies by variant
 */

const DEFAULTS = { full: 40, dark: 36, compact: 28, icon: 32 };

export default function ClaimFlowLogo({ variant = 'full', className = '', height }) {
  const h = height ?? DEFAULTS[variant];

  // ── Shield + arrow mark ──────────────────────────────────────────────────
  // Viewbox 0 0 60 60 — shield outline in navy, arrow/wave in amber
  const ShieldMark = ({ size = h }) => (
    <svg
      width={size}
      height={size}
      viewBox="0 0 60 60"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Outer shield — navy */}
      <path
        d="M30 4L8 13v16c0 12.5 9.3 24.2 22 27 12.7-2.8 22-14.5 22-27V13L30 4z"
        fill="#002045"
      />
      {/* Inner shield highlight — slightly lighter navy */}
      <path
        d="M30 9L12 17v12c0 10 7.4 19.3 18 21.8C40.6 48.3 48 39 48 29V17L30 9z"
        fill="#1a365d"
      />
      {/* Amber upward arrow / trend line */}
      <path
        d="M16 38 Q22 30 28 34 Q34 38 40 22 L44 18"
        stroke="#fea619"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Arrow head */}
      <path
        d="M38 14 L44 18 L40 24"
        stroke="#fea619"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );

  // ── Full / compact variant ───────────────────────────────────────────────
  if (variant === 'full' || variant === 'compact') {
    const textSize = variant === 'compact' ? Math.round(h * 0.55) : Math.round(h * 0.6);
    return (
      <span className={`inline-flex items-center gap-2 select-none ${className}`}>
        <ShieldMark size={h} />
        <span
          style={{ fontSize: textSize, lineHeight: 1, fontFamily: "'Be Vietnam Pro', sans-serif", fontWeight: 700 }}
        >
          <span style={{ color: '#002045' }}>Claim</span>
          <span style={{ color: '#fea619' }}>Flow</span>
        </span>
      </span>
    );
  }

  // ── Dark variant (white text + white-tinted shield) ──────────────────────
  if (variant === 'dark') {
    const textSize = Math.round(h * 0.6);
    return (
      <span className={`inline-flex items-center gap-2 select-none ${className}`}>
        {/* White-tinted shield for dark backgrounds */}
        <svg
          width={h}
          height={h}
          viewBox="0 0 60 60"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
        >
          <path
            d="M30 4L8 13v16c0 12.5 9.3 24.2 22 27 12.7-2.8 22-14.5 22-27V13L30 4z"
            fill="rgba(255,255,255,0.15)"
          />
          <path
            d="M30 9L12 17v12c0 10 7.4 19.3 18 21.8C40.6 48.3 48 39 48 29V17L30 9z"
            fill="rgba(255,255,255,0.08)"
          />
          <path
            d="M16 38 Q22 30 28 34 Q34 38 40 22 L44 18"
            stroke="#fea619"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
          <path
            d="M38 14 L44 18 L40 24"
            stroke="#fea619"
            strokeWidth="4"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>
        <span
          style={{ fontSize: textSize, lineHeight: 1, fontFamily: "'Be Vietnam Pro', sans-serif", fontWeight: 700, color: '#ffffff', letterSpacing: '0.04em', textTransform: 'uppercase' }}
        >
          CLAIM <span style={{ color: '#fea619' }}>FLOW</span>
        </span>
      </span>
    );
  }

  // ── Icon only ────────────────────────────────────────────────────────────
  return (
    <span className={`inline-flex items-center select-none ${className}`}>
      <ShieldMark size={h} />
    </span>
  );
}
