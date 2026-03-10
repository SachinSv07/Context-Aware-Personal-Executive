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
          <div className="prose prose-sm prose-invert max-w-none text-slate-200 leading-6">
            <ReactMarkdown
              components={{
                h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1 text-slate-100">{children}</h1>,
                h2: ({ children }) => <h2 className="text-sm font-bold mt-3 mb-1 text-slate-100">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1 text-slate-200">{children}</h3>,
                p:  ({ children }) => <p className="text-sm leading-6 mb-2">{children}</p>,
                ul: ({ children }) => <ul className="list-disc list-inside text-sm space-y-1 mb-2 pl-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside text-sm space-y-1 mb-2 pl-2">{children}</ol>,
                li: ({ children }) => <li className="text-sm leading-6">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold text-slate-100">{children}</strong>,
                em: ({ children }) => <em className="italic text-slate-300">{children}</em>,
                code: ({ children }) => <code className="bg-slate-700 rounded px-1 py-0.5 text-xs font-mono text-slate-200">{children}</code>,
                blockquote: ({ children }) => <blockquote className="border-l-2 border-slate-500 pl-3 italic text-slate-400 my-2">{children}</blockquote>,
                hr: () => <hr className="border-slate-600 my-2" />,
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
