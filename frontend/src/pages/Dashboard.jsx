import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const BACKEND = 'http://localhost:5000';

/* ─── small icon helpers (inline SVG, no extra deps) ─── */
function CheckIcon() {
  return (
    <svg className="h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor">
      <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z" clipRule="evenodd" />
    </svg>
  );
}

/* ─── OAuth-style connect card ─── */
function OAuthCard({ title, description, icon, connected, onConnect, onDisconnect }) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <div>
          <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
          <p className="text-sm text-slate-400">{description}</p>
        </div>
      </div>
      <div className="mt-4">
        {connected ? (
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1.5 rounded-xl bg-teal-900/50 px-3 py-2 text-sm font-medium text-teal-300">
              <CheckIcon /> Connected
            </span>
            <button
              type="button"
              onClick={onDisconnect}
              className="rounded-xl border border-slate-600 px-3 py-2 text-sm text-slate-400 transition hover:border-red-500 hover:text-red-400"
            >
              Disconnect
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={onConnect}
            className="rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-white"
          >
            Connect {title}
          </button>
        )}
      </div>
    </div>
  );
}

/* ─── Notes card ─── */
function NotesCard({ notes, onSave }) {
  const [text, setText] = useState('');
  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
      <div className="flex items-center gap-3">
        <span className="text-2xl">📝</span>
        <div>
          <h3 className="text-lg font-semibold text-slate-100">Personal Notes</h3>
          <p className="text-sm text-slate-400">Paste notes or tasks for your assistant.</p>
        </div>
      </div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={4}
        placeholder="Paste your notes here…"
        className="mt-4 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
      />
      {notes.length > 0 && (
        <ul className="mt-2 space-y-1">
          {notes.map((n, i) => (
            <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
              <CheckIcon />
              <span className="line-clamp-1">{n}</span>
            </li>
          ))}
        </ul>
      )}
      <button
        type="button"
        onClick={() => { if (text.trim()) { onSave(text.trim()); setText(''); } }}
        className="mt-3 rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-white"
      >
        Save Note
      </button>
    </div>
  );
}

/* ─── Upload card ─── */
function UploadCard({ files, onUpload }) {
  const ref = useRef();
  const handleFiles = (e) => {
    const picked = Array.from(e.target.files).map((f) => f.name);
    onUpload(picked);
    e.target.value = '';
  };
  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
      <div className="flex items-center gap-3">
        <span className="text-2xl">📄</span>
        <div>
          <h3 className="text-lg font-semibold text-slate-100">Upload Documents</h3>
          <p className="text-sm text-slate-400">Upload PDFs for the assistant to reference.</p>
        </div>
      </div>
      <input ref={ref} type="file" accept=".pdf,.txt,.doc,.docx" multiple className="hidden" onChange={handleFiles} />
      <button
        type="button"
        onClick={() => ref.current?.click()}
        className="mt-4 rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-white"
      >
        Upload File
      </button>
      {files.length > 0 && (
        <ul className="mt-3 space-y-1">
          {files.map((f, i) => (
            <li key={i} className="flex items-center gap-1.5 text-xs text-slate-400">
              <CheckIcon /> {f}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* ─── Connected sources status panel ─── */
function ConnectedSources({ connected, toggles, onToggle }) {
  const items = [
    { key: 'gmail',    label: 'Gmail',        icon: '📧' },
    { key: 'drive',    label: 'Google Drive',  icon: '📁' },
    { key: 'calendar', label: 'Calendar',      icon: '📅' },
    { key: 'notes',    label: 'Notes',         icon: '📝' },
    { key: 'docs',     label: 'Documents',     icon: '📄' },
  ];

  const anyConnected = items.some(
    (i) => connected[i.key] || (i.key === 'notes') || (i.key === 'docs'),
  );

  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg">
      <h3 className="text-lg font-semibold text-slate-100">Connected Sources</h3>
      <p className="mt-1 text-sm text-slate-400">Toggle which sources the assistant should search.</p>
      <ul className="mt-4 space-y-3">
        {items.map(({ key, label, icon }) => {
          const isConnected = connected[key];
          const enabled = toggles[key];
          return (
            <li key={key} className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm">
                <span>{icon}</span>
                <span className={isConnected ? 'text-slate-100' : 'text-slate-500'}>{label}</span>
                {isConnected && (
                  <span className="flex items-center gap-1 text-xs text-teal-400">
                    <CheckIcon /> connected
                  </span>
                )}
              </div>
              {isConnected && (
                <button
                  type="button"
                  onClick={() => onToggle(key)}
                  className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus:outline-none ${
                    enabled ? 'bg-teal-400' : 'bg-slate-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                      enabled ? 'translate-x-4' : 'translate-x-0'
                    }`}
                  />
                </button>
              )}
            </li>
          );
        })}
      </ul>

      {anyConnected && (
        <div className="mt-4 text-xs text-slate-500">
          {Object.values(connected).filter(Boolean).length} Google service(s) connected
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════
   Dashboard
═══════════════════════════════════════════════════════════ */
function Dashboard() {
  const navigate = useNavigate();

  // OAuth connection state
  const [connected, setConnected] = useState({ gmail: false, drive: false, calendar: false });
  // Source toggles (only relevant when connected)
  const [toggles, setToggles] = useState({ gmail: true, drive: true, calendar: true, notes: true, docs: true });
  // Notes
  const [notes, setNotes] = useState([]);
  // Uploaded files
  const [uploadedFiles, setUploadedFiles] = useState([]);
  // Indexing state
  const [indexed, setIndexed] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const location = useLocation();

  // Detect ?gmail=connected redirect back from OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('gmail') === 'connected') {
      setConnected((prev) => ({ ...prev, gmail: true }));
      // Clean the query string from the URL without a full reload
      window.history.replaceState({}, '', '/dashboard');
    }
  }, [location.search]);

  useEffect(() => {
    fetch(`${BACKEND}/auth/status`)
      .then((response) => response.json())
      .then((status) => {
        if (status.gmail) {
          setConnected((prev) => ({ ...prev, gmail: true }));
        }
      })
      .catch(() => {});
  }, []);

  const handleConnect = (key) => {
    if (key === 'gmail') {
      // Real OAuth: navigate browser to backend → Google consent screen
      window.location.href = `${BACKEND}/auth/google`;
      return;
    }
    // Drive / Calendar: placeholder until their OAuth routes are wired
    setConnected((prev) => ({ ...prev, [key]: true }));
  };

  const handleDisconnect = (key) => {
    fetch(`${BACKEND}/auth/disconnect/${key}`, { method: 'POST' }).catch(() => {});
    setConnected((prev) => ({ ...prev, [key]: false }));
  };

  const handleToggle = (key) => {
    setToggles((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleIndexData = () => {
    setIndexing(true);
    // Simulate indexing delay
    setTimeout(() => { setIndexing(false); setIndexed(true); }, 2000);
  };

  return (
    <div className="min-h-screen bg-[var(--bg-main)] px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-6xl">

        {/* ── Header ── */}
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-teal-300">Dashboard</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Add your data sources</h1>
            <p className="mt-2 text-sm text-slate-400">Connect services and upload files before starting chat.</p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/chat')}
            className="rounded-xl bg-teal-400 px-5 py-3 text-sm font-semibold text-slate-900 transition hover:brightness-110"
          >
            Continue to Chat →
          </button>
        </div>

        {/* ── Main grid ── */}
        <div className="grid gap-4 md:grid-cols-2">

          {/* Gmail */}
          <OAuthCard
            title="Gmail"
            description="Connect your Gmail to allow the assistant to search emails."
            icon="📧"
            connected={connected.gmail}
            onConnect={() => handleConnect('gmail')}
            onDisconnect={() => handleDisconnect('gmail')}
          />

          {/* Google Drive */}
          <OAuthCard
            title="Google Drive"
            description="Connect your Drive to search documents and files."
            icon="📁"
            connected={connected.drive}
            onConnect={() => handleConnect('drive')}
            onDisconnect={() => handleDisconnect('drive')}
          />

          {/* Google Calendar */}
          <OAuthCard
            title="Google Calendar"
            description="Connect your Calendar to retrieve events and meetings."
            icon="📅"
            connected={connected.calendar}
            onConnect={() => handleConnect('calendar')}
            onDisconnect={() => handleDisconnect('calendar')}
          />

          {/* Personal Notes */}
          <NotesCard notes={notes} onSave={(n) => setNotes((prev) => [...prev, n])} />

          {/* Upload Documents */}
          <UploadCard
            files={uploadedFiles}
            onUpload={(names) => setUploadedFiles((prev) => [...prev, ...names])}
          />

          {/* Connected Sources + toggles */}
          <ConnectedSources connected={connected} toggles={toggles} onToggle={handleToggle} />

        </div>

        {/* ── Index Data button ── */}
        <div className="mt-8 flex flex-col items-center gap-2">
          <button
            type="button"
            onClick={handleIndexData}
            disabled={indexing}
            className="rounded-xl bg-teal-400 px-8 py-3 text-sm font-semibold text-slate-900 transition hover:brightness-110 disabled:opacity-60"
          >
            {indexing ? 'Indexing…' : '⚡ Index My Data'}
          </button>
          {indexed && (
            <p className="flex items-center gap-1.5 text-sm text-teal-300">
              <CheckIcon /> Data indexed successfully
            </p>
          )}
          <p className="text-xs text-slate-500">
            Extracts text from uploaded files and connected sources for fast search.
          </p>
        </div>

      </div>
    </div>
  );
}

export default Dashboard;
