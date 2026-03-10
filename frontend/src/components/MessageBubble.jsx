import ReactMarkdown from 'react-markdown';

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
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-6">{content}</p>
        ) : (
          <div className="text-sm leading-6 space-y-1">
            <ReactMarkdown
              components={{
                h2: ({ children }) => (
                  <h2 className="text-base font-bold mt-4 mb-1 text-slate-100 border-b border-slate-600 pb-1">{children}</h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-sm font-semibold mt-3 mb-1 text-indigo-300">{children}</h3>
                ),
                p: ({ children }) => (
                  <p className="text-sm leading-6 mb-2 text-slate-200">{children}</p>
                ),
                ul: ({ children }) => (
                  <ul className="space-y-1 mb-2 pl-1">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside space-y-1 mb-2 pl-1">{children}</ol>
                ),
                li: ({ children }) => (
                  <li className="flex gap-2 text-sm leading-6 text-slate-200">
                    <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-indigo-400" />
                    <span>{children}</span>
                  </li>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-slate-100">{children}</strong>
                ),
                em: ({ children }) => (
                  <em className="italic text-slate-400">{children}</em>
                ),
                hr: () => (
                  <hr className="border-slate-600 my-3" />
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-2 border-indigo-500 pl-3 italic text-slate-400 my-2">{children}</blockquote>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
        <div className="mt-2 text-right text-[10px] text-slate-400">{timestamp}</div>
      </div>
    </div>
  );
}

export default MessageBubble;
