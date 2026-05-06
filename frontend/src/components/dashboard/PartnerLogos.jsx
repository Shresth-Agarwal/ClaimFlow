const PARTNERS = [
  'ICICI Lombard',
  'HDFC Life',
  'TATA AIG',
  'SBI General',
  'Bajaj Allianz',
  'Star Health',
];

export default function PartnerLogos() {
  return (
    <section className="w-full py-12 bg-white overflow-hidden border-b border-[#e0e3e5]">
      <div className="max-w-7xl mx-auto px-6 mb-8">
        <h2 className="font-['Work_Sans'] text-[14px] font-semibold text-[#43474e] text-center uppercase tracking-widest">
          Our Trusted Insurance Partners
        </h2>
      </div>

      <div className="relative flex overflow-x-hidden">
        {/* Duplicate set for seamless loop */}
        <div className="scroll-container flex items-center gap-12 md:gap-24 px-12">
          {[...PARTNERS, ...PARTNERS].map((name, i) => (
            <span
              key={i}
              className="logo-item font-bold text-xl text-[#002045] whitespace-nowrap"
            >
              {name}
            </span>
          ))}
        </div>

        {/* Gradient fade edges */}
        <div className="absolute inset-y-0 left-0 w-24 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />
        <div className="absolute inset-y-0 right-0 w-24 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />
      </div>
    </section>
  );
}
