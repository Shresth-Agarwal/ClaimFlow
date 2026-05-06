/**
 * WhyClaimFlow
 * Trust indicators — updated structure from new HTML, original colour palette retained.
 * New: icon circles use #fea619/10 bg + #855300 icon (vs old solid #002045 bg).
 * New: updated body copy and icons (bolt, support_agent, verified_user).
 * Colours: bg #f7f9fb, border #c4c6cf/20, title #002045, body #43474e.
 */

const REASONS = [
  {
    icon: 'bolt',
    filled: true,
    title: 'Fast Settlements',
    body: 'Industry-leading claim settlement ratio with digital-first verification.',
  },
  {
    icon: 'support_agent',
    filled: false,
    title: '24/7 Expert Support',
    body: 'Dedicated advisors available around the clock for your peace of mind.',
  },
  {
    icon: 'verified_user',
    filled: false,
    title: 'Secure & Transparent',
    body: 'Zero hidden costs and IRDAI-regulated processes for total transparency.',
  },
];

export default function WhyClaimFlow() {
  return (
    <section className="bg-[#f7f9fb] py-[80px] border-y border-[#c4c6cf]/20">
      <div className="max-w-[1280px] mx-auto px-[24px] text-center">
        <h2 className="font-['Be_Vietnam_Pro'] text-[32px] leading-[1.3] font-semibold text-[#002045] mb-[80px]">
          Why Choose ClaimFlow?
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-[48px]">
          {REASONS.map(({ icon, filled, title, body }) => (
            <div key={title} className="flex flex-col items-center">
              <div className="w-16 h-16 bg-[#fea619]/10 rounded-full flex items-center justify-center mb-[24px]">
                <span
                  className="material-symbols-outlined text-[#855300] text-[24px]"
                  style={filled ? { fontVariationSettings: "'FILL' 1" } : {}}
                >
                  {icon}
                </span>
              </div>
              <h3 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#191c1e] mb-[4px]">
                {title}
              </h3>
              <p className="font-['Work_Sans'] text-[16px] text-[#43474e]">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
