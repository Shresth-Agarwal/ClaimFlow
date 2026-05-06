import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../../context/AuthContext';
import ChatMessage, { TypingIndicator } from './ChatMessage';
import ChatInput from './ChatInput';

const AGENT_AVATAR =
  'https://lh3.googleusercontent.com/aida/ADBb0uioYvpV3fjcZMM0FqyuCh26zKbZQ-Hei1GOJgRgwZ_43NIkMm4BQmZCDDXzCAJ5QLcCJTq4nYAxsZ-NStovhp4bjPwylv_NQwxue1DYxVrWTqrSAYjIjDnuX3_emt9zOkzDy-CvQbr5LG84LIXBheVqKtFN5M5R41b7Ne5yEuGNaYw_XCryYNAnfYrx3FnLT1gD5v5_Fyi2ihP5Llpgp3afiYMyTfc8lnWEemui0cUV-SK-1UoSh44tIaXhGP4mBj3uNqaIs1FFW58';

const INITIAL_MESSAGES = [
  {
    id: 1,
    role: 'agent',
    text: "Hello! I've reviewed your claim for the motor insurance policy (SRK-8821). I see you've already uploaded the garage estimate.",
    time: '10:24 AM',
  },
  {
    id: 2,
    role: 'agent',
    text: 'Could you please confirm if the vehicle has been moved to the authorized service center?',
    time: '10:25 AM',
  },
];

const AGENT_REPLIES = [
  "Thank you for the information! I'll process this right away.",
  'Got it. Let me check the details and get back to you shortly.',
  'I understand. Could you provide any additional documents?',
  'Your claim is being reviewed. Expected resolution within 2-3 business days.',
  'Perfect. I have updated your claim status. Is there anything else I can help you with?',
];

/**
 * Claim context that will be forwarded to ProductsPage via location.state.
 * In a real app this would come from the active claim session / API.
 */
const CLAIM_CONTEXT = {
  policyType: 'Comprehensive Motor',
  policyNumber: '#SRK-294022',
  insuredAmount: 845000,
};

/** Show the "Proceed" banner after this many user messages */
const PROCEED_THRESHOLD = 2;

function formatTime(date) {
  return date.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

export default function ChatWindow() {
  const { user } = useAuthContext();
  const navigate = useNavigate();
  const [messages, setMessages] = useState(INITIAL_MESSAGES);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const bottomRef = useRef(null);

  // Count how many messages the user has sent
  const userMessageCount = messages.filter((m) => m.role === 'user').length;
  const showProceed = userMessageCount >= PROCEED_THRESHOLD;

  // Get user initials for avatar
  const initials = user?.email ? user.email.slice(0, 2).toUpperCase() : 'U';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = () => {
    const text = input.trim();
    if (!text) return;

    const now = new Date();
    const userMsg = { id: Date.now(), role: 'user', text, time: formatTime(now) };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Simulate agent reply after 1.5s
    setTimeout(() => {
      const reply = AGENT_REPLIES[Math.floor(Math.random() * AGENT_REPLIES.length)];
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: 'agent', text: reply, time: formatTime(new Date()) },
      ]);
    }, 1500);
  };

  /**
   * Redirect to /products, passing the full conversation context via
   * React Router location.state so ProductsPage can inherit it.
   */
  const handleProceed = () => {
    navigate('/products', {
      state: {
        chatContext: CLAIM_CONTEXT,
        messages,
        recommendation: null, // ProductsPage will fetch this from the backend
      },
    });
  };

  return (
    <section className="flex-grow flex flex-col bg-white relative min-w-0">
      {/* Chat header */}
      <header className="h-20 border-b border-slate-100 flex items-center justify-between px-8 bg-white/80 backdrop-blur-md z-10 flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="relative">
            <img
              src={AGENT_AVATAR}
              alt="Agent Rajesh"
              className="w-11 h-11 rounded-full object-cover"
            />
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-['Be_Vietnam_Pro'] text-[18px] font-semibold text-[#002045]">
                Rajesh Kumar
              </h3>
              <span className="bg-[#002045]/5 text-[#002045] text-[10px] px-2 py-0.5 rounded-full font-['Work_Sans'] font-semibold uppercase border border-[#002045]/10">
                Expert Advisor
              </span>
            </div>
            <span className="font-['Work_Sans'] text-[12px] text-green-600 flex items-center gap-1">
              <span className="w-1.5 h-1.5 bg-green-600 rounded-full inline-block" />
              Online
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {['call', 'videocam', 'more_vert'].map((icon) => (
            <button
              key={icon}
              className="p-2 hover:bg-slate-100 rounded-full transition-colors text-[#74777f]"
            >
              <span className="material-symbols-outlined">{icon}</span>
            </button>
          ))}
        </div>
      </header>

      {/* Messages */}
      <div
        className="flex-grow overflow-y-auto p-8 space-y-6 bg-[#f8fafc]"
        style={{ scrollbarWidth: 'none' }}
      >
        {/* Date separator */}
        <div className="flex justify-center">
          <span className="font-['Work_Sans'] text-[12px] text-[#74777f] bg-[#f2f4f6] px-4 py-1 rounded-full">
            Today, {new Date().toLocaleDateString('en-IN', { month: 'long', day: 'numeric' })}
          </span>
        </div>

        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            role={msg.role}
            text={msg.text}
            time={msg.time}
            initials={initials}
          />
        ))}

        {isTyping && <TypingIndicator />}

        {/* ── Proceed to Products banner ── */}
        {showProceed && (
          <div className="flex justify-center pt-2">
            <div className="bg-white border border-[#fea619]/40 rounded-2xl shadow-md px-6 py-4 flex flex-col items-center gap-3 max-w-sm w-full">
              <div className="flex items-center gap-2 text-[#002045]">
                <span
                  className="material-symbols-outlined text-[#fea619]"
                  style={{ fontVariationSettings: "'FILL' 1" }}
                >
                  check_circle
                </span>
                <span className="font-['Be_Vietnam_Pro'] font-semibold text-[15px]">
                  Consultation complete
                </span>
              </div>
              <p className="font-['Work_Sans'] text-[13px] text-[#43474e] text-center">
                Your claim context has been captured. Explore insurance products tailored to your
                profile.
              </p>
              <button
                onClick={handleProceed}
                className="w-full flex items-center justify-center gap-2 bg-[#002045] text-white py-2.5 rounded-xl font-['Work_Sans'] font-semibold text-[14px] hover:bg-[#1a365d] active:scale-95 transition-all"
              >
                Proceed to Products
                <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
              </button>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput value={input} onChange={setInput} onSend={handleSend} />
    </section>
  );
}
