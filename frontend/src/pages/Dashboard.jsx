import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const initialSources = {
  email: '',
  notes: '',
  pdf: '',
  docs: '',
};

function SourceCard({ title, description, name, value, onChange }) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
      <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
      <p className="mt-1 text-sm text-slate-400">{description}</p>
      <input
        value={value}
        onChange={(event) => onChange(name, event.target.value)}
        className="mt-4 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
        placeholder={`Add ${title.toLowerCase()} (optional)`}
      />
      <button
        type="button"
        className="mt-4 rounded-xl bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-white"
      >
        Save
      </button>
    </div>
  );
}

function Dashboard() {
  const [sources, setSources] = useState(initialSources);
  const navigate = useNavigate();

  const cards = useMemo(
    () => [
      {
        key: 'email',
        title: 'Email Account',
        description: 'Connect your inbox or paste account details for context ingestion.',
      },
      {
        key: 'notes',
        title: 'Notes Text',
        description: 'Add raw notes to help your assistant understand your priorities.',
      },
      {
        key: 'pdf',
        title: 'PDF Links',
        description: 'Provide URLs to PDF files you want the assistant to reference.',
      },
      {
        key: 'docs',
        title: 'Document Links',
        description: 'Add links to docs, wikis, or files for richer responses.',
      },
    ],
    [],
  );

  const handleChange = (name, value) => {
    setSources((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="min-h-screen bg-[var(--bg-main)] px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-teal-300">Dashboard</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Add your data sources</h1>
            <p className="mt-2 text-sm text-slate-400">All inputs are optional. Add only what you need before starting chat.</p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/chat')}
            className="rounded-xl bg-teal-400 px-5 py-3 text-sm font-semibold text-slate-900 transition hover:brightness-110"
          >
            Continue to Chat
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {cards.map((card) => (
            <SourceCard
              key={card.key}
              name={card.key}
              title={card.title}
              description={card.description}
              value={sources[card.key]}
              onChange={handleChange}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
