import { useNavigate } from 'react-router-dom';

function Sidebar({ chats, activeChatId, onSelectChat, onNewChat }) {
  const navigate = useNavigate();

  return (
    <aside className="flex h-full w-full flex-col border-r border-slate-800 bg-[var(--surface-1)] p-3 sm:w-72">
      <div className="mb-4 rounded-2xl bg-slate-900/60 p-4">
        <h1 className="text-lg font-bold text-white">ContextIQ</h1>
        <p className="text-xs text-slate-400">Context-Aware Personal Executive</p>
      </div>

      <button
        type="button"
        onClick={onNewChat}
        className="mb-4 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-left text-sm font-medium text-slate-100 transition hover:border-[var(--accent)] hover:text-[var(--accent)]"
      >
        + New Chat
      </button>

      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        <p className="mb-2 px-2 text-[11px] uppercase tracking-wide text-slate-500">Recent Chats</p>
        <div className="space-y-2">
          {chats.map((chat) => (
            <button
              key={chat.id}
              type="button"
              onClick={() => onSelectChat(chat.id)}
              className={`w-full rounded-xl px-3 py-2 text-left text-sm transition ${
                chat.id === activeChatId
                  ? 'bg-slate-800 text-slate-100 ring-1 ring-[var(--accent)]'
                  : 'bg-slate-900/40 text-slate-300 hover:bg-slate-800/70'
              }`}
            >
              <p className="truncate">{chat.title}</p>
              <p className="mt-1 text-xs text-slate-500">{new Date(chat.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Settings Link at Bottom */}
      <div className="mt-4 space-y-2 border-t border-slate-800 pt-3">
        <button
          type="button"
          onClick={() => navigate('/settings')}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm text-slate-300 transition hover:bg-slate-800/70"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span>Settings & Profile</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;
