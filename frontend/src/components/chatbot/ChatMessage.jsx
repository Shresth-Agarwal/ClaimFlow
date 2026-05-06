const AGENT_AVATAR =
  'https://lh3.googleusercontent.com/aida/ADBb0uioYvpV3fjcZMM0FqyuCh26zKbZQ-Hei1GOJgRgwZ_43NIkMm4BQmZCDDXzCAJ5QLcCJTq4nYAxsZ-NStovhp4bjPwylv_NQwxue1DYxVrWTqrSAYjIjDnuX3_emt9zOkzDy-CvQbr5LG84LIXBheVqKtFN5M5R41b7Ne5yEuGNaYw_XCryYNAnfYrx3FnLT1gD5v5_Fyi2ihP5Llpgp3afiYMyTfc8lnWEemui0cUV-SK-1UoSh44tIaXhGP4mBj3uNqaIs1FFW58';

/**
 * Renders a string that may contain markdown-style formatting:
 *   **bold**  →  <strong>
 *   \n        →  line break
 *   • bullet  →  preserved as-is
 */
function FormattedText({ text }) {
  // Split on newlines first, then handle **bold** within each line
  const lines = text.split('\n');

  return (
    <>
      {lines.map((line, lineIdx) => {
        // Split each line on **...** markers
        const parts = line.split(/\*\*(.+?)\*\*/g);
        const rendered = parts.map((part, partIdx) =>
          // Every odd index is the captured bold group
          partIdx % 2 === 1 ? (
            <strong key={partIdx} className="font-semibold">
              {part}
            </strong>
          ) : (
            part
          )
        );

        return (
          <span key={lineIdx}>
            {rendered}
            {lineIdx < lines.length - 1 && <br />}
          </span>
        );
      })}
    </>
  );
}

/**
 * Single chat message bubble.
 * @param {{ role: 'agent'|'user', text: string, time: string, initials?: string }} props
 */
export default function ChatMessage({ role, text, time, initials = 'U' }) {
  if (role === 'agent') {
    return (
      <div className="flex gap-4 max-w-[80%]">
        <img
          src={AGENT_AVATAR}
          alt="Agent"
          className="w-8 h-8 rounded-full flex-shrink-0 mt-1 object-cover"
        />
        <div className="space-y-1">
          <div className="bg-white border border-slate-100 p-4 rounded-2xl rounded-tl-none shadow-sm font-['Work_Sans'] text-[16px] text-[#191c1e] leading-relaxed">
            <FormattedText text={text} />
          </div>
          <span className="font-['Work_Sans'] text-[10px] text-[#74777f] px-1">{time}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-row-reverse gap-4 max-w-[80%] ml-auto">
      <div className="w-8 h-8 rounded-full bg-[#002045] flex items-center justify-center text-white font-['Work_Sans'] text-[12px] font-bold mt-1 flex-shrink-0">
        {initials}
      </div>
      <div className="flex flex-col items-end space-y-1">
        <div className="bg-[#002045] text-white p-4 rounded-2xl rounded-tr-none shadow-md font-['Work_Sans'] text-[16px] leading-relaxed">
          <FormattedText text={text} />
        </div>
        <span className="font-['Work_Sans'] text-[10px] text-[#74777f] px-1">{time}</span>
      </div>
    </div>
  );
}

/** Typing indicator bubble */
export function TypingIndicator() {
  return (
    <div className="flex gap-4 max-w-[80%] items-center">
      <img
        src={AGENT_AVATAR}
        alt="Agent typing"
        className="w-8 h-8 rounded-full object-cover flex-shrink-0"
      />
      <div className="flex gap-1.5 bg-white border border-slate-100 px-4 py-3 rounded-2xl shadow-sm">
        <div className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce" />
        <div className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:75ms]" />
        <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce [animation-delay:150ms]" />
      </div>
    </div>
  );
}
