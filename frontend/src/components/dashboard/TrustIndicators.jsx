const ITEMS = [
  {
    icon: 'speed',
    iconColor: 'text-[#fea619]',
    title: 'Instant Quotes',
    body: "Compare top insurers side-by-side in under 2 minutes. No paperwork needed.",
  },
  {
    icon: 'support_agent',
    iconColor: 'text-[#1a365d]',
    title: 'Claim Support',
    body: 'Dedicated 24/7 assistance team to hold your hand during the claims process.',
  },
];

export default function TrustIndicators() {
  return (
    <section className="w-full bg-[#f2f4f6] py-[80px] px-6 mt-[24px] border-y border-[#e0e3e5]">
      <div className="max-w-4xl mx-auto grid grid-cols-1 gap-[48px] text-center divide-y md:divide-y-0 divide-[#c4c6cf] md:grid-cols-2 md:divide-x">
        {ITEMS.map(({ icon, iconColor, title, body }) => (
          <div key={title} className="flex flex-col items-center gap-4 p-4">
            <span className={`material-symbols-outlined text-4xl icon-fill ${iconColor}`}>
              {icon}
            </span>
            <h3 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#1a365d]">
              {title}
            </h3>
            <p className="font-['Work_Sans'] text-[16px] leading-[1.5] text-[#43474e]">{body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
