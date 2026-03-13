import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

function LoadingBubble() {
  return (
    <div className="flex justify-start">
      <div className="inline-flex items-center gap-1 rounded-2xl rounded-bl-md bg-[var(--bubble-ai)] px-4 py-3">
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.2s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.1s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
      </div>
    </div>
  );
}

function ChatWindow({ messages, isLoading }) {
  const endOfMessagesRef = useRef(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (!messages.length) {
    return (
      <div className="flex flex-1 items-center justify-center px-4 sm:px-6 text-center">
        <div className="animate-fade-in max-w-md">
          <h2 className="text-xl sm:text-2xl font-semibold text-slate-100">Start a new conversation</h2>
          <p className="mt-2 text-sm text-slate-400">Ask anything and your assistant will respond with context-aware guidance.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-3 py-4 sm:px-4 sm:py-6 lg:px-6">
      <div className="mx-auto flex max-w-4xl flex-col gap-3 sm:gap-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            role={message.role}
            content={message.content}
            metadata={message.metadata}
            timestamp={message.timestamp}
          />
        ))}
        {isLoading ? <LoadingBubble /> : null}
        <div ref={endOfMessagesRef} />
      </div>
    </div>
  );
}

export default ChatWindow;
