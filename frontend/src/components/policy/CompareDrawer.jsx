/**
 * CompareDrawer
 * Slide-up confirmation panel shown BEFORE the comparison table.
 * Colour palette: ClaimFlow standard (#002045, #1a365d, #fea619, #f2f4f6, #eceef0).
 */

export default function CompareDrawer({ selected, onRemove, onConfirm, onCancel }) {
  if (!selected || selected.length === 0) return null;

  const canCompare = selected.length >= 2;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-[55] bg-[#002045]/40 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Drawer panel */}
      <div className="fixed bottom-0 left-0 right-0 z-[60] bg-[#f2f4f6] rounded-t-2xl shadow-2xl border-t-4 border-[#fea619] animate-slide-up">

        {/* Handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 bg-[#c4c6cf] rounded-full" />
        </div>

        <div className="px-6 pb-8 pt-2 max-w-[1280px] mx-auto">

          {/* Header */}
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="w-1 h-8 bg-[#fea619] rounded-full" />
              <div>
                <h3 className="font-['Be_Vietnam_Pro'] text-[22px] font-bold text-[#002045]">
                  Review Your Selection
                </h3>
                <p className="font-['Work_Sans'] text-[13px] text-[#43474e] mt-0.5">
                  {selected.length === 1
                    ? 'Add at least one more policy to compare.'
                    : `You're about to compare ${selected.length} ${selected.length === 2 ? 'policy' : 'policies'} side-by-side.`}
                </p>
              </div>
            </div>
            <button
              onClick={onCancel}
              className="p-2 rounded-full bg-[#eceef0] hover:bg-[#e0e3e5] transition-colors text-[#43474e]"
              aria-label="Close"
            >
              <span className="material-symbols-outlined">close</span>
            </button>
          </div>

          {/* Policy checklist */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 mb-5">
            {selected.map((policy) => (
              <div
                key={policy.id}
                className="flex items-center gap-3 p-3 bg-white rounded-xl border border-[#c4c6cf]/50 shadow-sm"
              >
                {/* Checked box — click removes */}
                <button
                  onClick={() => onRemove(policy.id)}
                  className="flex-shrink-0 w-5 h-5 rounded border-2 border-[#002045] bg-[#002045] flex items-center justify-center hover:bg-[#ba1a1a] hover:border-[#ba1a1a] transition-colors"
                  aria-label={`Remove ${policy.name}`}
                >
                  <span className="material-symbols-outlined text-white text-[14px]">check</span>
                </button>

                {/* Logo */}
                {policy.logo && (
                  <img
                    src={policy.logo}
                    alt={policy.name}
                    className="h-8 w-12 object-contain rounded flex-shrink-0 border border-[#eceef0]"
                  />
                )}

                {/* Name + price */}
                <div className="flex-1 min-w-0">
                  <p className="font-['Be_Vietnam_Pro'] font-bold text-[14px] text-[#002045] truncate">
                    {policy.name}
                  </p>
                  <p className="font-['Work_Sans'] text-[12px] text-[#855300] font-semibold">
                    {policy.price ?? policy.premium ?? '—'} /yr
                  </p>
                </div>
              </div>
            ))}

            {/* Empty slot placeholders */}
            {Array.from({ length: Math.max(0, 2 - selected.length) }).map((_, i) => (
              <div
                key={`empty-${i}`}
                className="flex items-center justify-center gap-2 p-3 rounded-xl border-2 border-dashed border-[#c4c6cf] text-[#74777f] bg-white/50"
              >
                <span className="material-symbols-outlined text-[20px]">add_circle</span>
                <span className="font-['Work_Sans'] text-[13px]">Add a policy</span>
              </div>
            ))}
          </div>

          {/* Tip — only when < 2 selected */}
          {!canCompare && (
            <div className="flex items-center gap-2 mb-4 bg-[#ffddb8] border border-[#fea619]/40 px-4 py-2.5 rounded-lg">
              <span className="material-symbols-outlined text-[#855300] text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>info</span>
              <span className="font-['Work_Sans'] text-[13px] text-[#653e00]">
                Select at least <strong>2 policies</strong> to enable comparison.
              </span>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 justify-end">
            <button
              onClick={onCancel}
              className="px-5 py-2.5 rounded-xl border-2 border-[#c4c6cf] text-[#43474e] bg-white font-['Work_Sans'] font-semibold text-[14px] hover:bg-[#eceef0] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              disabled={!canCompare}
              className="px-6 py-2.5 rounded-xl bg-[#002045] text-white font-['Work_Sans'] font-bold text-[14px] flex items-center gap-2 hover:bg-[#1a365d] active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md"
            >
              <span className="material-symbols-outlined text-[18px]">compare_arrows</span>
              Proceed to Compare
            </button>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes slide-up {
          from { transform: translateY(100%); opacity: 0; }
          to   { transform: translateY(0);    opacity: 1; }
        }
        .animate-slide-up { animation: slide-up 0.25s ease-out; }
      `}</style>
    </>
  );
}
