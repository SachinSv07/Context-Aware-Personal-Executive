function MessageBubble({ role, content, timestamp }) {
  const isUser = role === 'user';

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm sm:max-w-[70%] ${
          isUser
            ? 'rounded-br-md bg-[var(--bubble-user)] text-slate-100'
            : 'rounded-bl-md bg-[var(--bubble-ai)] text-slate-200'
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-6">{content}</p>
        <div className="mt-2 text-right text-[10px] text-slate-400">{timestamp}</div>
      </div>
    </div>
  );
}

export default MessageBubble;
