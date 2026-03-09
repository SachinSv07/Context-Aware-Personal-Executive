import { useState } from 'react';

function ChatInput({ onSend, isLoading }) {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    const trimmed = message.trim();
    if (!trimmed || isLoading) {
      return;
    }
    onSend(trimmed);
    setMessage('');
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-slate-800 bg-[var(--surface-2)]/90 px-3 py-3 backdrop-blur sm:px-4 sm:py-4 lg:px-6">
      <div className="mx-auto flex max-w-4xl items-end gap-2 sm:gap-3 rounded-xl sm:rounded-2xl border border-slate-700 bg-[var(--surface-1)] px-2 sm:px-3 py-2 shadow-lg">
        <textarea
          rows={1}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message ContextIQ"
          className="max-h-36 min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={isLoading}
          className="rounded-lg sm:rounded-xl bg-[var(--accent)] px-3 sm:px-4 py-2 text-xs sm:text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40 flex-shrink-0"
        >
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInput;
