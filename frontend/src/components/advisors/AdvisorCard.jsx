/**
 * AdvisorCard
 * Single advisor tile — photo, name, specialty, badge.
 * Accepts an `onBook` callback for the "Book" action (wired to API).
 */

export default function AdvisorCard({ advisor, onBook, isBooking }) {
  const { name, specialty, badge, badgeIcon, photo } = advisor;

  return (
    <div className="flex flex-col gap-3 pb-3 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow border border-[#eceef0] overflow-hidden p-3">
      {/* Photo */}
      <div
        className="w-full bg-center bg-no-repeat aspect-square bg-cover rounded-lg"
        style={{ backgroundImage: `url("${photo}")` }}
        role="img"
        aria-label={name}
      />

      {/* Info */}
      <div className="mt-2">
        <p className="text-[#101419] text-lg font-bold leading-normal font-['Be_Vietnam_Pro']">
          {name}
        </p>
        <p className="text-[#002045] font-semibold text-sm leading-normal font-['Work_Sans']">
          {specialty}
        </p>
        <div className="flex items-center gap-1 mt-1">
          <span
            className="material-symbols-outlined text-[#855300] text-sm"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            {badgeIcon}
          </span>
          <p className="text-[#586e8d] text-sm font-normal leading-normal font-['Work_Sans']">
            {badge}
          </p>
        </div>
      </div>

      {/* Book button */}
      <button
        onClick={() => onBook(advisor)}
        disabled={isBooking}
        className="mt-auto w-full py-2 rounded-lg bg-[#002045] text-white font-['Work_Sans'] font-semibold text-[13px] hover:bg-[#1a365d] active:scale-95 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-1"
      >
        {isBooking ? (
          <>
            <svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Booking…
          </>
        ) : (
          'Book Consultation'
        )}
      </button>
    </div>
  );
}
