import TopAppBar from '../components/dashboard/TopAppBar';
import ChatSidebar from '../components/chatbot/ChatSidebar';
import ChatWindow from '../components/chatbot/ChatWindow';
import ClaimContextPanel from '../components/chatbot/ClaimContextPanel';

export default function ChatbotPage() {
  return (
    <div className="flex flex-col h-screen text-[#191c1e] bg-[#f7f9fb]">
      {/* Shared top bar — identical to user dashboard */}
      <TopAppBar activePage="ChatBot" />

      {/* Main — fills remaining height */}
      <main className="flex flex-1 overflow-hidden">
        <ChatSidebar />
        <ChatWindow />
        <ClaimContextPanel />
      </main>
    </div>
  );
}
