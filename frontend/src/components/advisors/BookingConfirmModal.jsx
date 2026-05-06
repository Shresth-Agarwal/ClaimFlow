/**
 * BookingConfirmModal
 * Shown after a successful advisor booking.
 * Displays the booked advisor's name and a confirmation message.
 */

export default function BookingConfirmModal({ advisor, onClose }) {
  if (!advisor) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-sm w-full mx-4 flex flex-col items-center gap-4">
        {/* Success icon */}
        <div className="w-16 h-16 bg-[#ffddb8] rounded-full flex items-center justify-center">
          <span
            className="material-symbols-outlined text-[#855300] text-[32px]"
            style={{ fontVariationSettings: "'FILL' 1" }}
          >
            check_circle
          </span>
        </div>

        <h3 className="font-['Be_Vietnam_Pro'] text-[22px] font-bold text-[#002045] text-center">
          Consultation Booked!
        </h3>

        <p className="font-['Work_Sans'] text-[15px] text-[#43474e] text-center">
          Your consultation with{' '}
          <span className="font-bold text-[#002045]">{advisor.name}</span> (
          {advisor.specialty}) has been confirmed. You'll receive a calendar invite shortly.
        </p>

        <button
          onClick={onClose}
          className="w-full py-3 bg-[#002045] text-white rounded-xl font-['Work_Sans'] font-semibold text-[14px] hover:bg-[#1a365d] active:scale-95 transition-all"
        >
          Done
        </button>
      </div>
    </div>
  );
}
