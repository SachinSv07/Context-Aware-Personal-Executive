function Sidebar({ chats, activeChatId, onSelectChat, onNewChat }) {
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
    </aside>
  );
}

export default Sidebar;
