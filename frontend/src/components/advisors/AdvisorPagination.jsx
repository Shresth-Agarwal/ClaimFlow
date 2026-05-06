/**
 * AdvisorPagination
 * Page number controls — prev / numbered pages / next.
 */

export default function AdvisorPagination({ currentPage, totalPages, onPageChange }) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className="flex items-center justify-center p-8 mt-4">
      {/* Prev */}
      <button
        onClick={() => onPageChange(Math.max(1, currentPage - 1))}
        disabled={currentPage === 1}
        className="flex w-10 h-10 items-center justify-center hover:bg-[#f2f4f6] rounded-full transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        aria-label="Previous page"
      >
        <span className="material-symbols-outlined text-[#101419]">chevron_left</span>
      </button>

      {/* Page numbers */}
      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          className={`text-sm font-bold leading-normal tracking-wide flex w-10 h-10 items-center justify-center rounded-full transition-colors ${
            p === currentPage
              ? 'bg-[#002045] text-white'
              : 'text-[#101419] hover:bg-[#f2f4f6]'
          }`}
        >
          {p}
        </button>
      ))}

      {/* Next */}
      <button
        onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
        disabled={currentPage === totalPages}
        className="flex w-10 h-10 items-center justify-center hover:bg-[#f2f4f6] rounded-full transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        aria-label="Next page"
      >
        <span className="material-symbols-outlined text-[#101419]">chevron_right</span>
      </button>
    </div>
  );
}
