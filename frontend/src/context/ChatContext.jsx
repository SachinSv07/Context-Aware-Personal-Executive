import { createContext, useContext, useState, useEffect } from 'react';

const ChatContext = createContext(null);

const API_BASE_URL = 'http://localhost:5000';

const formatTitle = (text) => {
  if (!text) {
    return 'New conversation';
  }
  return text.length > 28 ? `${text.slice(0, 28)}...` : text;
};

const createChat = (id) => ({
  id: id.toString(),
  title: 'New conversation',
  messages: [],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
});

export function ChatProvider({ children }) {
  const [chatCounter, setChatCounter] = useState(2);
  const [chats, setChats] = useState([createChat(1)]);
  const [activeChatId, setActiveChatId] = useState('1');
  const [isLoading, setIsLoading] = useState(true);

  const activeChat = chats.find((chat) => chat.id === activeChatId) || chats[0];

  // Load conversations from backend on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load conversations');
      }

      const data = await response.json();
      
      if (data.success && data.conversations && data.conversations.length > 0) {
        setChats(data.conversations);
        setActiveChatId(data.conversations[0].id);
        
        // Update counter to be higher than any existing ID
        const maxId = Math.max(...data.conversations.map(c => parseInt(c.id) || 0));
        setChatCounter(maxId + 1);
      } else {
        // No conversations, start with default
        const defaultChat = createChat(1);
        setChats([defaultChat]);
        setActiveChatId('1');
      }
    } catch (error) {
      console.error('Error loading conversations:', error);
      // On error, start with default chat
      const defaultChat = createChat(1);
      setChats([defaultChat]);
      setActiveChatId('1');
    } finally {
      setIsLoading(false);
    }
  };

  const saveConversation = async (conversation) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...conversation,
          updatedAt: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save conversation');
      }

      const data = await response.json();
      return data.conversation;
    } catch (error) {
      console.error('Error saving conversation:', error);
      return null;
    }
  };

  const createNewChat = () => {
    const nextId = chatCounter.toString();
    const newChat = createChat(nextId);
    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(nextId);
    setChatCounter((prev) => prev + 1);
    
    // Save new chat to backend
    saveConversation(newChat);
  };

  const selectChat = (chatId) => {
    setActiveChatId(chatId);
  };

  const addMessage = async (chatId, message) => {
    const messageWithTimestamp = {
      ...message,
      timestamp: message.timestamp || new Date().toISOString(),
    };

    let updatedChat = null;

    setChats((prev) =>
      prev.map((chat) => {
        if (chat.id !== chatId) {
          return chat;
        }

        const nextMessages = [...chat.messages, messageWithTimestamp];
        const nextTitle =
          chat.title === 'New conversation' && message.role === 'user'
            ? formatTitle(message.content)
            : chat.title;

        updatedChat = {
          ...chat,
          title: nextTitle,
          messages: nextMessages,
          updatedAt: new Date().toISOString(),
        };

        return updatedChat;
      }),
    );

    // Save updated conversation to backend
    if (updatedChat) {
      await saveConversation(updatedChat);
    }
  };

  const clearActiveChat = async () => {
    if (!activeChat) {
      return;
    }

    const clearedChat = {
      ...activeChat,
      title: 'New conversation',
      messages: [],
      updatedAt: new Date().toISOString(),
    };

    setChats((prev) =>
      prev.map((chat) =>
        chat.id === activeChat.id ? clearedChat : chat,
      ),
    );

    // Save cleared chat to backend
    await saveConversation(clearedChat);
  };

  const deleteChat = async (chatId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${chatId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete conversation');
      }

      // Remove from local state
      setChats((prev) => {
        const filtered = prev.filter((chat) => chat.id !== chatId);
        
        // If we deleted the active chat, switch to the first available
        if (activeChatId === chatId && filtered.length > 0) {
          setActiveChatId(filtered[0].id);
        }
        
        // If no chats left, create a new one
        if (filtered.length === 0) {
          const newChat = createChat(chatCounter);
          setActiveChatId(newChat.id);
          setChatCounter((prev) => prev + 1);
          saveConversation(newChat);
          return [newChat];
        }
        
        return filtered;
      });
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const value = {
    chats,
    activeChat,
    activeChatId,
    isLoading,
    createNewChat,
    selectChat,
    addMessage,
    clearActiveChat,
    deleteChat,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used inside ChatProvider');
  }
  return context;
}

