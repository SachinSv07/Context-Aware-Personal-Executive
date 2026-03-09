import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatInput from '../components/ChatInput';
import ChatWindow from '../components/ChatWindow';
import Sidebar from '../components/Sidebar';
import { useChat } from '../context/ChatContext';

const createTimestamp = () =>
  new Date().toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

function ChatPage() {
  const [isLoading, setIsLoading] = useState(false);
  const {
    chats,
    activeChat,
    activeChatId,
    createNewChat,
    selectChat,
    addMessage,
    clearActiveChat,
  } = useChat();
  const navigate = useNavigate();

  const handleSend = (text) => {
    if (!activeChat) {
      return;
    }

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: createTimestamp(),
    };

    addMessage(activeChat.id, userMessage);
    setIsLoading(true);

    // Simulates an async AI response while backend integration is pending.
    window.setTimeout(() => {
      const aiMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `I received: "${text}". I can help summarize emails, organize notes, and draft actions from your context.`,
        timestamp: createTimestamp(),
      };
      addMessage(activeChat.id, aiMessage);
      setIsLoading(false);
    }, 950);
  };

  return (
    <div className="h-screen bg-[var(--bg-main)] text-slate-100">
      <div className="flex h-full flex-col sm:flex-row">
        <div className="h-64 sm:h-full">
          <Sidebar
            chats={chats}
            activeChatId={activeChatId}
            onSelectChat={selectChat}
            onNewChat={createNewChat}
          />
        </div>

        <main className="flex min-h-0 flex-1 flex-col">
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-3 sm:px-6">
            <h2 className="text-sm font-medium text-slate-300">{activeChat?.title || 'Conversation'}</h2>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={clearActiveChat}
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 transition hover:border-teal-400 hover:text-teal-300"
              >
                Clear Chat
              </button>
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 transition hover:border-slate-400"
              >
                Dashboard
              </button>
            </div>
          </div>

          <ChatWindow messages={activeChat?.messages || []} isLoading={isLoading} />
          <ChatInput onSend={handleSend} isLoading={isLoading} />
        </main>
      </div>
    </div>
  );
}

export default ChatPage;
