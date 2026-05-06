/**
 * PolicyFilters
 * Left sidebar with category-specific filter controls.
 * All state is local — no backend calls needed.
 */
import { useState } from 'react';

export default function PolicyFilters({ category, onReset }) {
  const [checkboxes, setCheckboxes] = useState(() => {
    const init = {};
    (category.filters || []).forEach((f) => {
      if (f.type === 'checkbox') init[f.id] = f.default ?? false;
    });
    return init;
  });

  const [chipActive, setChipActive] = useState(
    category.filters?.find((f) => f.type === 'chips')?.default ?? null
  );

  return (
    <aside className="hidden lg:flex flex-col gap-[24px] p-[24px] w-80 h-[calc(100vh-64px)] sticky top-16 overflow-y-auto bg-[#f2f4f6] border-r border-[#c4c6cf] flex-shrink-0">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045]">Filters</h2>
          <p className="font-['Work_Sans'] text-[16px] text-[#43474e]">Refine Policy Search</p>
        </div>
        <button
          onClick={onReset}
          className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045] hover:underline"
        >
          Reset All
        </button>
      </div>

      {(category.filters || []).map((filter) => {
        if (filter.type === 'select') {
          return (
            <div key={filter.id} className="flex flex-col gap-[12px]">
              <label className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045]">
                {filter.label}
              </label>
              <select className="w-full p-3 rounded-lg border border-[#74777f] bg-white focus:ring-2 focus:ring-[#002045] outline-none font-['Work_Sans'] text-[16px]">
                {filter.options.map((o) => (
                  <option key={o} selected={o === filter.default}>{o}</option>
                ))}
              </select>
            </div>
          );
        }

        if (filter.type === 'checkbox') {
          return (
            <label key={filter.id} className="flex items-center gap-2 font-['Work_Sans'] text-[16px] cursor-pointer">
              <input
                type="checkbox"
                checked={checkboxes[filter.id] ?? false}
                onChange={(e) => setCheckboxes((p) => ({ ...p, [filter.id]: e.target.checked }))}
                className="rounded text-[#002045] focus:ring-[#002045]"
              />
              {filter.label}
            </label>
          );
        }

        if (filter.type === 'chips') {
          return (
            <div key={filter.id} className="flex flex-col gap-[12px]">
              <label className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045]">
                {filter.label}
              </label>
              <div className="flex flex-wrap gap-2">
                {filter.options.map((o) => (
                  <button
                    key={o}
                    onClick={() => setChipActive(o)}
                    className={`px-3 py-1 rounded-full font-['Work_Sans'] text-[12px] font-semibold border transition-colors ${
                      chipActive === o
                        ? 'bg-[#fea619]/50 text-[#684000] border-[#fea619]'
                        : 'bg-[#e0e3e5] text-[#43474e] border-transparent'
                    }`}
                  >
                    {o}
                  </button>
                ))}
              </div>
            </div>
          );
        }

        return null;
      })}

      {/* Coverage slider — shown for health */}
      {category.chips && (
        <>
          <div className="flex flex-col gap-[12px]">
            <label className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045]">Key Features</label>
            <div className="flex flex-wrap gap-2">
              {category.chips.map(({ label, active }) => (
                <span
                  key={label}
                  className={`px-3 py-1 rounded-full font-['Work_Sans'] text-[12px] border ${
                    active
                      ? 'bg-[#fea619]/50 text-[#684000] border-[#fea619]'
                      : 'bg-[#e0e3e5] text-[#43474e] border-transparent'
                  }`}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-[12px]">
            <div className="flex justify-between items-center">
              <label className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045]">Coverage Amount</label>
              <span className="font-['Work_Sans'] font-semibold text-[14px] text-[#855300]">₹10L+</span>
            </div>
            <input type="range" className="w-full h-2 bg-[#002045] rounded-lg appearance-none cursor-pointer accent-[#fea619]" />
            <div className="flex justify-between font-['Work_Sans'] text-[12px] text-[#43474e]">
              <span>₹3L</span><span>₹1Cr</span>
            </div>
          </div>

          <div className="p-4 bg-[#ffdad6]/30 border border-[#ba1a1a]/20 rounded-xl">
            <p className="font-['Work_Sans'] font-semibold text-[14px] text-[#ba1a1a] flex items-center gap-1">
              <span className="material-symbols-outlined text-[18px]">info</span>
              Pre-existing conditions?
            </p>
            <p className="font-['Work_Sans'] text-[12px] text-[#43474e] mt-1">
              Declaring ensures smoother claims later.
            </p>
            <button className="mt-2 w-full py-2 border border-[#74777f] rounded-lg font-['Work_Sans'] font-semibold text-[14px] hover:bg-[#e0e3e5] transition-all">
              Add Medical Info
            </button>
          </div>
        </>
      )}
    </aside>
  );
}
