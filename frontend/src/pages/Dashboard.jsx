import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Card for text input sources (Email, Notes)
function TextInputCard({ title, description, value, onChange, buttonText = 'Save', onAction, helpText }) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
      <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
      <p className="mt-1 text-sm text-slate-400">{description}</p>
      {helpText && (
        <div className="mt-2 rounded-lg bg-slate-900/60 px-3 py-2 text-xs text-slate-500">
          💡 {helpText}
        </div>
      )}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-4 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
        placeholder={`Add ${title.toLowerCase()} (optional)`}
      />
      <button
        type="button"
        onClick={onAction}
        className="mt-4 rounded-xl bg-teal-400 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:brightness-110"
      >
        {buttonText}
      </button>
    </div>
  );
}

// Card for file upload sources (PDF, Google Drive)
function FileUploadCard({ title, description, onUpload }) {
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      onUpload(file);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
      <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
      <p className="mt-1 text-sm text-slate-400">{description}</p>
      
      <div className="mt-4">
        <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-700 bg-slate-950 px-4 py-6 transition hover:border-teal-400">
          <svg
            className="h-8 w-8 text-slate-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <span className="mt-2 text-sm text-slate-400">
            {selectedFile ? selectedFile.name : 'Click to upload'}
          </span>
          <input
            type="file"
            className="hidden"
            onChange={handleFileChange}
            accept={title === 'PDF Upload' ? '.pdf' : '*'}
          />
        </label>
      </div>

      <button
        type="button"
        disabled={!selectedFile}
        className="mt-4 w-full rounded-xl bg-teal-400 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Upload & Save
      </button>
    </div>
  );
}

// Card for service connections (Google Calendar)
function ConnectCard({ title, description, onConnect, isConnected }) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
      <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
      <p className="mt-1 text-sm text-slate-400">{description}</p>
      
      <div className="mt-4 flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950 px-4 py-3">
        <span className="text-sm text-slate-400">
          {isConnected ? 'Connected' : 'Not connected'}
        </span>
        {isConnected && (
          <span className="h-2 w-2 rounded-full bg-teal-400" />
        )}
      </div>

      <button
        type="button"
        onClick={onConnect}
        className={`mt-4 w-full rounded-xl px-4 py-2 text-sm font-semibold transition ${
          isConnected
            ? 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            : 'bg-teal-400 text-slate-900 hover:brightness-110'
        }`}
      >
        {isConnected ? 'Disconnect' : 'Connect'}
      </button>
    </div>
  );
}

function Dashboard() {
  const [email, setEmail] = useState('');
  const [notes, setNotes] = useState('');
  const [calendarConnected, setCalendarConnected] = useState(false);
  const navigate = useNavigate();

  const handleEmailFetch = () => {
    // TODO: Integrate with Gmail API
    console.log('Fetching from Gmail:', email);
  };

  const handleNotesSave = () => {
    // TODO: Save notes to backend
    console.log('Saving notes:', notes);
  };

  const handlePdfUpload = (file) => {
    // TODO: Upload PDF to backend
    console.log('Uploading PDF:', file);
  };

  const handleDriveUpload = (file) => {
    // TODO: Upload to Google Drive or process file
    console.log('Uploading to Drive:', file);
  };

  const handleCalendarConnect = () => {
    // TODO: Integrate with Google Calendar API
    setCalendarConnected(!calendarConnected);
    console.log('Calendar connection toggled');
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
          <TextInputCard
            title="Gmail Account"
            description="Connect your Gmail inbox for email context ingestion."
            helpText="User authentication via Google OAuth 2.0. Click 'Fetch from Gmail' to authorize access to your inbox securely."
            value={email}
            onChange={setEmail}
            buttonText="Fetch from Gmail"
            onAction={handleEmailFetch}
          />

          <FileUploadCard
            title="PDF Upload"
            description="Upload PDF files you want the assistant to reference."
            onUpload={handlePdfUpload}
          />

          <FileUploadCard
            title="Google Drive Upload"
            description="Upload documents from your drive for richer context."
            onUpload={handleDriveUpload}
          />

          <ConnectCard
            title="Google Calendar"
            description="Sync your calendar events for scheduling and time management."
            onConnect={handleCalendarConnect}
            isConnected={calendarConnected}
          />

          <TextInputCard
            title="Notes Text"
            description="Add raw notes to help your assistant understand your priorities."
            value={notes}
            onChange={setNotes}
            buttonText="Save Notes"
            onAction={handleNotesSave}
          />
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
