import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ChatInput from '../components/ChatInput';
import ChatWindow from '../components/ChatWindow';
import Sidebar from '../components/Sidebar';
import { useChat } from '../context/ChatContext';
import { getAuthHeaders } from '../utils/auth';

const createTimestamp = () =>
  new Date().toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

function ChatPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const {
    chats,
    activeChat,
    activeChatId,
    createNewChat,
    selectChat,
    addMessage,
    clearActiveChat,
    reloadConversations,
  } = useChat();
  const navigate = useNavigate();

  // Reload conversations when navigating to ChatPage
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && reloadConversations) {
      console.log('ChatPage: Reloading conversations...');
      reloadConversations();
    }
  }, []); // Empty dependency array - only run once on mount

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

    // Call backend API
    fetch('http://localhost:5000/api/query', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query: text }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then((data) => {
        const aiMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.response || 'No response from server',
          timestamp: createTimestamp(),
        };
        addMessage(activeChat.id, aiMessage);
        setIsLoading(false);
      })
      .catch((error) => {
        console.error('Error calling backend:', error);
        const errorMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: 'Sorry, I encountered an error connecting to the backend. Please make sure the server is running.',
          timestamp: createTimestamp(),
        };
        addMessage(activeChat.id, errorMessage);
        setIsLoading(false);
      });
  };

  return (
    <div className="h-screen bg-[var(--bg-main)] text-slate-100">
      <div className="flex h-full flex-col md:flex-row">
        {/* Mobile Sidebar Toggle */}
        <div className="md:hidden flex items-center justify-between border-b border-slate-800 bg-[var(--surface-2)]/90 px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="rounded-lg p-2 transition hover:bg-slate-800"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h2 className="text-sm font-medium text-slate-300">{activeChat?.title || 'Conversation'}</h2>
          </div>
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 transition hover:border-teal-400 hover:text-teal-300"
          >
            Dashboard
          </button>
        </div>

        {/* Sidebar */}
        <div className={`${
          sidebarOpen ? 'fixed inset-0 z-50 md:relative' : 'hidden md:block'
        } md:h-full`}>
          {sidebarOpen && (
            <div 
              className="absolute inset-0 bg-black/50 md:hidden"
              onClick={() => setSidebarOpen(false)}
            />
          )}
          <div className={`${
            sidebarOpen ? 'relative w-72' : 'w-full md:w-72'
          } h-full`}>
            <Sidebar
              chats={chats}
              activeChatId={activeChatId}
              onSelectChat={(chatId) => {
                selectChat(chatId);
                setSidebarOpen(false);
              }}
              onNewChat={() => {
                createNewChat();
                setSidebarOpen(false);
              }}
            />
          </div>
        </div>

        <main className="flex min-h-0 flex-1 flex-col">
          <div className="hidden md:flex items-center justify-between border-b border-slate-800 px-4 py-3 sm:px-6">
            <h2 className="text-sm font-medium text-slate-300 truncate">{activeChat?.title || 'Conversation'}</h2>
            <div className="flex items-center gap-2 flex-shrink-0">
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
              <button
                type="button"
                onClick={() => navigate('/settings')}
                className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs text-slate-300 transition hover:border-slate-400"
                title="Settings & Profile"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
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
