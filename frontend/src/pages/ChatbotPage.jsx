import { useState, useRef } from 'react';
import TopAppBar from '../components/dashboard/TopAppBar';
import ChatSidebar from '../components/chatbot/ChatSidebar';
import ChatWindow from '../components/chatbot/ChatWindow';
import ClaimContextPanel from '../components/chatbot/ClaimContextPanel';

export default function ChatbotPage() {
  /**
   * sessionId is lifted here so ChatWindow (writes it), ChatSidebar (can reset it),
   * and ClaimContextPanel (reads + can clear it) all share the same value.
   */
  const [sessionId, setSessionId] = useState(null);

  // Ref to expose ChatWindow's reset function to the sidebar's "New Conversation" button
  const resetChat = () => {
    setSessionId(null);
    // ChatWindow listens to sessionId changes and will reset itself
    // We also dispatch a custom event so ChatWindow can clear its local message state
    window.dispatchEvent(new CustomEvent('claimflow:new-conversation'));
  };

  return (
    <div className="flex flex-col h-screen text-[#191c1e] bg-[#f7f9fb]">
      {/* Shared top bar */}
      <TopAppBar activePage="ChatBot" />

      {/* Main — fills remaining height */}
      <main className="flex flex-1 overflow-hidden">
        <ChatSidebar onNewConversation={resetChat} />
        <ChatWindow sessionId={sessionId} onSessionIdChange={setSessionId} />
        <ClaimContextPanel
          sessionId={sessionId}
          onSessionCleared={() => setSessionId(null)}
        />
      </main>
    </div>
  );
}
