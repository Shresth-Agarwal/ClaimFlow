/**
 * ComparisonBar
 * Sticky bottom bar showing selected policies for comparison.
 * Appears only when at least one policy is selected.
 */

export default function ComparisonBar({ selected, onRemove, onClear, onCompare }) {
  if (selected.length === 0) return null;

  return (
    <nav className="fixed bottom-0 left-0 w-full z-50 flex justify-center items-center gap-[48px] px-[24px] py-4 bg-[#1a365d] rounded-t-xl shadow-lg">
      <div className="flex items-center gap-[24px] max-w-[1280px] w-full">
        {/* Selected policy chips */}
        <div className="hidden md:flex items-center gap-[12px] flex-1">
          {selected.map((p) => (
            <div key={p.id} className="flex items-center gap-2 bg-white/10 p-2 rounded-lg border border-white/20">
              <img src={p.logo} alt={p.name} className="h-8 w-8 rounded object-contain" />
              <span className="font-['Work_Sans'] text-[12px] text-white">{p.name}</span>
              <button
                onClick={() => onRemove(p.id)}
                className="material-symbols-outlined text-white text-[18px] cursor-pointer hover:text-[#ba1a1a] transition-colors"
              >
                close
              </button>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-[12px] ml-auto">
          <button
            onClick={onClear}
            className="text-[#86a0cd] flex flex-col items-center gap-1 hover:text-[#ffb95f] transition-all"
          >
            <span className="material-symbols-outlined">delete_sweep</span>
            <span className="font-['Work_Sans'] font-semibold text-[14px]">Clear</span>
          </button>

          <button
            onClick={onCompare}
            className="bg-[#855300] text-white rounded-full px-6 py-2 flex items-center gap-2 font-['Work_Sans'] font-bold text-[14px] shadow-md hover:opacity-90 active:scale-95 transition-all"
          >
            <span className="material-symbols-outlined">compare_arrows</span>
            Compare Selected ({selected.length})
          </button>
        </div>
      </div>
    </nav>
  );
}
