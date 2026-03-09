import { createContext, useContext, useState } from 'react';

const ChatContext = createContext(null);

const formatTitle = (text) => {
  if (!text) {
    return 'New conversation';
  }
  return text.length > 28 ? `${text.slice(0, 28)}...` : text;
};

const createChat = (id) => ({
  id,
  title: 'New conversation',
  messages: [],
  createdAt: Date.now(),
});

export function ChatProvider({ children }) {
  const [chatCounter, setChatCounter] = useState(2);
  const [chats, setChats] = useState([createChat(1)]);
  const [activeChatId, setActiveChatId] = useState(1);

  const activeChat = chats.find((chat) => chat.id === activeChatId) || chats[0];

  const createNewChat = () => {
    const nextId = chatCounter;
    const newChat = createChat(nextId);
    setChats((prev) => [newChat, ...prev]);
    setActiveChatId(nextId);
    setChatCounter((prev) => prev + 1);
  };

  const selectChat = (chatId) => {
    setActiveChatId(chatId);
  };

  const addMessage = (chatId, message) => {
    setChats((prev) =>
      prev.map((chat) => {
        if (chat.id !== chatId) {
          return chat;
        }

        const nextMessages = [...chat.messages, message];
        const nextTitle =
          chat.title === 'New conversation' && message.role === 'user'
            ? formatTitle(message.content)
            : chat.title;

        return {
          ...chat,
          title: nextTitle,
          messages: nextMessages,
        };
      }),
    );
  };

  const clearActiveChat = () => {
    if (!activeChat) {
      return;
    }

    setChats((prev) =>
      prev.map((chat) =>
        chat.id === activeChat.id
          ? {
              ...chat,
              title: 'New conversation',
              messages: [],
            }
          : chat,
      ),
    );
  };

  const value = {
    chats,
    activeChat,
    activeChatId,
    createNewChat,
    selectChat,
    addMessage,
    clearActiveChat,
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
