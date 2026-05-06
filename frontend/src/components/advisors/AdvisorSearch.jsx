/**
 * AdvisorSearch
 * Full-width search bar for filtering advisors by name, specialty, or keyword.
 */

export default function AdvisorSearch({ value, onChange }) {
  return (
    <div className="px-4 py-3">
      <label className="flex flex-col min-w-40 h-14 w-full">
        <div className="flex w-full flex-1 items-stretch rounded-xl h-full shadow-sm">
          <div className="text-[#586e8d] flex border-none bg-[#e9ecf1] items-center justify-center pl-4 rounded-l-xl border-r-0">
            <span className="material-symbols-outlined">search</span>
          </div>
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Search by name, specialty, or keyword"
            className="flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-xl text-[#101419] focus:outline-none focus:ring-0 border-none bg-[#e9ecf1] h-full placeholder:text-[#586e8d] px-4 rounded-l-none border-l-0 pl-2 text-lg font-normal leading-normal font-['Work_Sans']"
          />
          {value && (
            <button
              onClick={() => onChange('')}
              className="bg-[#e9ecf1] rounded-r-xl px-3 text-[#586e8d] hover:text-[#101419] transition-colors"
              aria-label="Clear search"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          )}
        </div>
      </label>
    </div>
  );
}
