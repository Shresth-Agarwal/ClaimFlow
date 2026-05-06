/**
 * AdvisorGrid
 * Responsive grid of AdvisorCard tiles.
 * Filters the advisors list by the current search query.
 */

import AdvisorCard from './AdvisorCard';

export default function AdvisorGrid({ advisors, searchQuery, onBook, bookingId }) {
  const filtered = advisors.filter((a) => {
    const q = searchQuery.toLowerCase();
    return (
      a.name.toLowerCase().includes(q) ||
      a.specialty.toLowerCase().includes(q) ||
      a.badge.toLowerCase().includes(q)
    );
  });

  if (filtered.length === 0) {
    return (
      <div className="col-span-full py-16 text-center">
        <span className="material-symbols-outlined text-[48px] text-[#c4c6cf]">search_off</span>
        <p className="font-['Work_Sans'] text-[16px] text-[#74777f] mt-3">
          No advisors match "<span className="font-semibold">{searchQuery}</span>"
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6 p-4">
      {filtered.map((advisor) => (
        <AdvisorCard
          key={advisor.id}
          advisor={advisor}
          onBook={onBook}
          isBooking={bookingId === advisor.id}
        />
      ))}
    </div>
  );
}
