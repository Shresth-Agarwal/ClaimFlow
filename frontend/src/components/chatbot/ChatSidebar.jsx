import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ACTIVE = [
  {
    id: 1,
    name: 'ClaimFlow AI',
    preview: 'Ask me anything about your claim...',
    time: 'Now',
    online: true,
    initials: 'CF',
    active: true,
  },
  {
    id: 2,
    name: 'Priya Sharma',
    preview: 'Claim #9821 approved...',
    time: '2h ago',
    online: false,
    initials: 'PS',
    active: false,
  },
];

const HISTORY = [
  { id: 3, name: 'Health Renewal', preview: 'Policy successfully renewed', time: 'Sep 12' },
  { id: 4, name: 'Motor Claim', preview: 'Claim CLM-20260412 approved', time: 'Apr 12' },
];

/**
 * @param {{ onNewConversation?: () => void }} props
 */
export default function ChatSidebar({ onNewConversation }) {
  const navigate = useNavigate();
  const [activeId, setActiveId] = useState(1);

  const handleNewConversation = () => {
    // Notify parent (ChatbotPage) to reset the chat window
    if (onNewConversation) {
      onNewConversation();
    }
    setActiveId(null);
  };

  const handleSelectActive = (item) => {
    setActiveId(item.id);
    // If it's the AI agent (id=1), just focus the chat window
    // For real advisors you'd navigate to their thread
    if (item.id !== 1) {
      // Placeholder: in a full app, load that conversation thread
      alert(`Opening conversation with ${item.name}…\n(Multi-advisor threads coming soon)`);
    }
  };

  const handleSelectHistory = (item) => {
    setActiveId(item.id);
    // Placeholder: load historical session
    alert(`Loading past conversation: "${item.name}"\n(Session history coming soon)`);
  };

  return (
    <aside className="w-80 bg-slate-50 border-r border-slate-200 flex-col h-full hidden md:flex">
      <div className="p-6">
        <h2 className="font-['Be_Vietnam_Pro'] text-[24px] font-semibold text-[#002045] mb-4">
          Support Hub
        </h2>
        <button
          onClick={handleNewConversation}
          className="w-full flex items-center justify-center gap-2 bg-[#fea619] text-[#684000] py-3 rounded-xl font-['Work_Sans'] font-semibold text-[14px] shadow-sm hover:brightness-105 active:scale-95 transition-all"
        >
          <span className="material-symbols-outlined">add_comment</span>
          New Conversation
        </button>
      </div>

      <div className="flex-grow overflow-y-auto px-4 space-y-2" style={{ scrollbarWidth: 'none' }}>
        <div className="px-2 pb-2 font-['Work_Sans'] text-[12px] font-semibold uppercase tracking-wider text-[#74777f]">
          Active Now
        </div>

        {ACTIVE.map((item) => (
          <button
            key={item.id}
            onClick={() => handleSelectActive(item)}
            className={`w-full flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors text-left ${
              activeId === item.id
                ? 'bg-white shadow-sm border border-[#fea619]/30'
                : 'hover:bg-[#eceef0] border border-transparent'
            }`}
          >
            <div className="relative flex-shrink-0">
              <div className="w-12 h-12 rounded-full bg-[#002045] flex items-center justify-center text-white font-['Work_Sans'] font-bold text-[14px]">
                {item.initials}
              </div>
              <div
                className={`absolute bottom-0 right-0 w-3 h-3 border-2 border-white rounded-full ${
                  item.online ? 'bg-green-500' : 'bg-slate-300'
                }`}
              />
            </div>
            <div className="flex-grow min-w-0">
              <div className="flex justify-between items-center">
                <span className="font-['Work_Sans'] font-semibold text-[14px] text-[#002045] truncate">
                  {item.name}
                </span>
                <span className="font-['Work_Sans'] text-[10px] text-[#74777f] ml-2 flex-shrink-0">
                  {item.time}
                </span>
              </div>
              <p className="font-['Work_Sans'] text-[12px] text-[#43474e] truncate">{item.preview}</p>
            </div>
          </button>
        ))}

        <div className="px-2 pt-6 pb-2 font-['Work_Sans'] text-[12px] font-semibold uppercase tracking-wider text-[#74777f]">
          History
        </div>

        {HISTORY.map((item) => (
          <button
            key={item.id}
            onClick={() => handleSelectHistory(item)}
            className={`w-full flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-colors text-left ${
              activeId === item.id
                ? 'bg-white shadow-sm border border-[#fea619]/30'
                : 'hover:bg-[#eceef0] border border-transparent'
            }`}
          >
            <div className="w-12 h-12 rounded-full bg-[#e0e3e5] flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-[#74777f]">history</span>
            </div>
            <div className="flex-grow min-w-0">
              <div className="flex justify-between items-center">
                <span className="font-['Work_Sans'] font-semibold text-[14px] text-[#191c1e] truncate">
                  {item.name}
                </span>
                <span className="font-['Work_Sans'] text-[10px] text-[#74777f] ml-2 flex-shrink-0">
                  {item.time}
                </span>
              </div>
              <p className="font-['Work_Sans'] text-[12px] text-[#74777f] truncate">{item.preview}</p>
            </div>
          </button>
        ))}
      </div>
    </aside>
  );
}
