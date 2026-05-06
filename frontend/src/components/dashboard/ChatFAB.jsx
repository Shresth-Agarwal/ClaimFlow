import { useNavigate } from 'react-router-dom';

export default function ChatFAB() {
  const navigate = useNavigate();

  return (
    <div className="fixed bottom-[24px] right-[24px] z-50 flex flex-col items-end gap-2 group">
      {/* Tooltip */}
      <div className="bg-[#2d3133] text-[#eff1f3] text-[12px] px-3 py-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity shadow-lg mb-2 mr-2 whitespace-nowrap">
        Ask our AI (हिन्दी, English +5)
      </div>

      {/* Button */}
      <button
        onClick={() => navigate('/chatbot')}
        className="w-16 h-16 bg-[#fea619] text-white rounded-full shadow-[0px_10px_30px_rgba(26,54,93,0.2)] hover:bg-[#855300] hover:scale-105 active:scale-95 transition-all duration-300 flex items-center justify-center relative border-4 border-white"
      >
        <span className="material-symbols-outlined text-3xl icon-fill">smart_toy</span>
        {/* Online indicator */}
        <span className="absolute top-0 right-0 w-4 h-4 bg-green-500 border-2 border-white rounded-full" />
      </button>
    </div>
  );
}
