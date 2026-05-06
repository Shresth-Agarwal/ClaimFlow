export default function HeroSection() {
  return (
    <section className="relative w-full py-[80px] px-6 flex flex-col items-center justify-center hero-pattern border-b border-[#e0e3e5] overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute top-0 left-10 w-64 h-64 bg-[#d6e3ff] rounded-full mix-blend-multiply filter blur-3xl opacity-50 z-0" />
      <div className="absolute bottom-10 right-10 w-72 h-72 bg-[#ffddb8] rounded-full mix-blend-multiply filter blur-3xl opacity-40 z-0" />

      <div className="relative z-10 flex flex-col items-center text-center max-w-4xl mx-auto gap-[24px] w-full">
        {/* Trust badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#e0e3e5] border border-[#c4c6cf] shadow-sm mb-2">
          <span className="material-symbols-outlined text-[#fea619] text-sm icon-fill">stars</span>
          <span className="text-[14px] font-semibold text-[#43474e]">Trusted by 10 Lacs+ Happy Smiles</span>
        </div>

        {/* Headline */}
        <h1 className="font-['Be_Vietnam_Pro'] text-[48px] leading-[1.2] font-bold text-[#1a365d] tracking-tight">
          Secure Your Tomorrow,{' '}
          <br />
          <span className="text-[#fea619] relative inline-block">
            Simply Today.
            <svg
              className="absolute w-full h-3 -bottom-1 left-0 text-[#fea619] opacity-30"
              preserveAspectRatio="none"
              viewBox="0 0 100 10"
            >
              <path d="M0 5 Q 50 10 100 5" fill="none" stroke="currentColor" strokeWidth="4" />
            </svg>
          </span>
        </h1>

        <p className="font-['Work_Sans'] text-[18px] leading-[1.6] text-[#43474e] max-w-2xl mx-auto">
          Compare plans from India's top insurers. Find the right coverage for your health, family,
          and assets in minutes with expert guidance.
        </p>

        {/* Search bar */}
        <div className="w-full max-w-3xl mt-[24px] relative bg-white rounded-xl shadow-[0px_10px_30px_rgba(26,54,93,0.08)] border border-[#c4c6cf] p-2 flex flex-col sm:flex-row items-center gap-2 focus-within:ring-2 focus-within:ring-[#fea619] transition-all">
          <div className="flex items-center w-full px-4 py-2 border-b sm:border-b-0 sm:border-r border-[#e0e3e5] group">
            <span className="material-symbols-outlined text-[#74777f] group-focus-within:text-[#1a365d] mr-3 transition-colors">
              search
            </span>
            <input
              className="w-full bg-transparent border-none outline-none focus:ring-0 font-['Work_Sans'] text-[16px] text-[#191c1e] placeholder:text-[#c4c6cf]"
              placeholder="What kind of insurance are you looking for?"
              type="text"
            />
          </div>
          <button className="w-full sm:w-auto bg-[#fea619] hover:bg-[#855300] text-white font-['Work_Sans'] font-semibold text-[14px] px-8 py-4 rounded-lg shadow-sm transition-all active:scale-95 whitespace-nowrap flex items-center justify-center gap-2">
            Find Plans
            <span className="material-symbols-outlined text-sm">arrow_forward</span>
          </button>
        </div>
      </div>
    </section>
  );
}
