import { useRef } from 'react';

/**
 * Message input bar with attach/camera/mic/send controls.
 */
export default function ChatInput({ value, onChange, onSend }) {
  const textareaRef = useRef(null);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  const handleInput = (e) => {
    // Auto-resize textarea
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
    }
    onChange(e.target.value);
  };

  return (
    <div className="p-6 bg-white border-t border-slate-100">
      <div className="max-w-4xl mx-auto flex items-end gap-3 bg-white border border-slate-200 p-2 rounded-2xl shadow-sm focus-within:border-[#002045] transition-all">
        {/* Action buttons */}
        <div className="flex items-center gap-1 mb-1 px-2">
          {[
            { icon: 'attach_file', title: 'Attach File' },
            { icon: 'photo_camera', title: 'Upload Photo' },
            { icon: 'mic', title: 'Voice Message' },
          ].map(({ icon, title }) => (
            <button
              key={icon}
              type="button"
              title={title}
              className="p-2 text-[#74777f] hover:text-[#002045] hover:bg-slate-100 rounded-full transition-all"
            >
              <span className="material-symbols-outlined">{icon}</span>
            </button>
          ))}
        </div>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Type your message here..."
          rows={1}
          className="flex-grow border-none focus:ring-0 font-['Work_Sans'] text-[16px] py-3 bg-transparent resize-none min-h-[48px] placeholder:text-[#74777f] outline-none"
          style={{ scrollbarWidth: 'none' }}
        />

        {/* Send button */}
        <button
          type="button"
          onClick={onSend}
          disabled={!value.trim()}
          className="bg-[#fea619] text-[#684000] h-12 w-12 flex items-center justify-center rounded-xl shadow-md hover:brightness-105 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
        >
          <span className="material-symbols-outlined">send</span>
        </button>
      </div>

      <div className="flex justify-center mt-3">
        <span className="font-['Work_Sans'] text-[10px] text-[#74777f] flex items-center gap-1">
          <span className="material-symbols-outlined text-[12px]">lock</span>
          End-to-end encrypted. Your data is secure with ClaimFlow.
        </span>
      </div>
    </div>
  );
}
