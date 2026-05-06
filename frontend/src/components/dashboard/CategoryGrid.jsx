const CATEGORIES = [
  { label: 'Health', icon: 'favorite', offset: '' },
  { label: 'Life Cover', icon: 'shield', offset: 'md:-translate-y-4' },
  { label: 'Vehicle', icon: 'directions_car', offset: 'md:-translate-y-8' },
  { label: 'Home', icon: 'home', offset: 'md:-translate-y-4' },
  { label: 'Travel', icon: 'flight', offset: 'col-span-2 md:col-span-1' },
];

export default function CategoryGrid() {
  return (
    <section className="w-full max-w-7xl mx-auto px-6 py-[48px] relative z-20 mt-8">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-[12px] md:gap-[24px]">
        {CATEGORIES.map(({ label, icon, offset }) => (
          <a
            key={label}
            href="#"
            className={`bg-white rounded-xl p-[24px] flex flex-col items-center justify-center gap-4 border border-[#c4c6cf] shadow-ambient hover:shadow-[0px_10px_30px_rgba(26,54,93,0.12)] hover:border-[#ffddb8] transition-all duration-300 group cursor-pointer h-40 ${offset}`}
          >
            <div className="w-14 h-14 rounded-full bg-[#d6e3ff] flex items-center justify-center group-hover:bg-[#ffddb8] transition-colors">
              <span className="material-symbols-outlined text-[#1a365d] group-hover:text-[#fea619] icon-fill text-3xl">
                {icon}
              </span>
            </div>
            <span className="font-['Work_Sans'] text-[14px] font-semibold text-[#1a365d] group-hover:text-[#fea619] text-center transition-colors">
              {label}
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}
