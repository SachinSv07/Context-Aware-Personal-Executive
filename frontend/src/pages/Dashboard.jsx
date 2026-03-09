import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthHeaders } from '../utils/auth';

// OAuth Setup Modal
function OAuthSetupModal({ isOpen, onClose, onSave }) {
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!clientId.trim() || !clientSecret.trim()) {
      setError('Both Client ID and Client Secret are required');
      return;
    }

    setLoading(true);
    setError('');
    
    const success = await onSave({ clientId, clientSecret });
    
    if (success) {
      setClientId('');
      setClientSecret('');
      onClose();
    } else {
      setError('Failed to save OAuth credentials');
    }
    
    setLoading(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 overflow-y-auto">
      <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 p-4 sm:p-6 shadow-2xl my-8">
        <div className="mb-4 flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h2 className="text-lg sm:text-xl font-semibold text-white">Google OAuth Setup</h2>
            <p className="mt-1 text-xs sm:text-sm text-slate-400">
              Enter your Google Cloud OAuth credentials to enable Gmail integration
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 transition hover:bg-slate-800 hover:text-slate-200 flex-shrink-0"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
              {error}
            </div>
          )}

          <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 p-4 text-xs text-blue-300">
            <p className="mb-2 font-semibold">📋 Setup Instructions:</p>
            <ol className="ml-4 space-y-1 list-decimal">
              <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="underline hover:text-blue-200">Google Cloud Console</a></li>
              <li>Create project → Enable Gmail API</li>
              <li>Create OAuth credentials (Web application)</li>
              <li>Add redirect URI: <code className="rounded bg-slate-800 px-1 py-0.5">http://localhost:5000/api/auth/google/callback</code></li>
              <li>Copy Client ID and Client Secret below</li>
            </ol>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Client ID
            </label>
            <input
              type="text"
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="your-client-id.apps.googleusercontent.com"
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Client Secret
            </label>
            <input
              type="password"
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder="GOCSPX-••••••••••••••••••••"
              className="w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-xl border border-slate-700 px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-xl bg-teal-400 px-4 py-2.5 text-sm font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save & Connect'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

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

// Card for Google Drive picker
function GoogleDriveCard({ onFilesSelected }) {
  const [selectedFiles, setSelectedFiles] = useState([]);

  const openDrivePicker = () => {
    // TODO: Integrate Google Drive Picker API
    // This will open Google's file picker dialog for selecting files from Drive
    alert('Google Drive Picker will open here.\n\nImplementation requires:\n1. Google Cloud Project setup\n2. Drive API enabled\n3. OAuth 2.0 credentials\n4. Drive Picker API script loaded\n\nUser will be able to browse and select files from their Google Drive.');
    
    // Mock selection for demo
    const mockFiles = [
      { id: '1abc', name: 'Project_Plan.pdf', mimeType: 'application/pdf' }
    ];
    setSelectedFiles(mockFiles);
    onFilesSelected(mockFiles);
  };

  return (
    <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
      <h3 className="text-lg font-semibold text-slate-100">Google Drive</h3>
      <p className="mt-1 text-sm text-slate-400">
        Select files from your Google Drive for richer context.
      </p>

      <div className="mt-4">
        <button
          type="button"
          onClick={openDrivePicker}
          className="flex w-full cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-700 bg-slate-950 px-4 py-6 transition hover:border-teal-400"
        >
          <svg
            className="h-8 w-8 text-slate-500"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M7.71 3.5L1.15 15l3.58 6.5L11.29 9.5 7.71 3.5M9.73 15L6.15 21.5h14.5L24.23 15H9.73M22.28 14l-3.58-6.5-7.43 12.5 3.58 6.5L22.28 14z" />
          </svg>
          <span className="mt-2 text-sm font-medium text-teal-400">
            Select from Google Drive
          </span>
        </button>
      </div>

      {selectedFiles.length > 0 && (
        <div className="mt-4 space-y-2">
          {selectedFiles.map((file) => (
            <div
              key={file.id}
              className="flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-xs text-slate-300"
            >
              <svg className="h-4 w-4 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span className="flex-1 truncate">{file.name}</span>
            </div>
          ))}
        </div>
      )}

      <button
        type="button"
        disabled={selectedFiles.length === 0}
        className="mt-4 w-full rounded-xl bg-teal-400 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Save Selected Files
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
  const [gmailConnected, setGmailConnected] = useState(false);
  const [gmailLoading, setGmailLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [showOAuthModal, setShowOAuthModal] = useState(false);
  const [oauthConfigured, setOauthConfigured] = useState(false);
  const navigate = useNavigate();

  // Check OAuth status on mount
  useEffect(() => {
    checkGmailStatus();
    
    // Check for OAuth callback messages
    const urlParams = new URLSearchParams(window.location.search);
    const oauthStatus = urlParams.get('oauth');
    const oauthMessage = urlParams.get('message');
    
    if (oauthStatus === 'success') {
      setStatusMessage('Successfully connected to Gmail!');
      setGmailConnected(true);
      // Clear URL parameters
      window.history.replaceState({}, '', '/dashboard');
    } else if (oauthStatus === 'error') {
      setStatusMessage(`OAuth Error: ${oauthMessage || 'Unknown error'}`);
      window.history.replaceState({}, '', '/dashboard');
    }
  }, []);

  const checkGmailStatus = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/auth/google/status', {
        headers: getAuthHeaders()
      });
      const data = await response.json();
      setGmailConnected(data.connected || false);
      setOauthConfigured(data.oauth_configured || false);
    } catch (error) {
      console.error('Error checking Gmail status:', error);
    }
  };

  const handleEmailFetch = async () => {
    if (gmailConnected) {
      // Already connected, fetch emails
      await fetchGmailMessages();
    } else if (!oauthConfigured) {
      // OAuth not configured, show setup modal
      setShowOAuthModal(true);
    } else {
      // OAuth configured but not connected, initiate OAuth
      await initiateGoogleOAuth();
    }
  };

  const initiateGoogleOAuth = async () => {
    setGmailLoading(true);
    setStatusMessage('Initiating Google authentication...');
    
    try {
      const response = await fetch('http://localhost:5000/api/auth/google/initiate', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ email: email || undefined })
      });

      const data = await response.json();

      if (!response.ok) {
        setStatusMessage(data.error || 'Failed to initiate OAuth');
        if (data.setup_guide) {
          setStatusMessage(`${data.error}\n\nSee: ${data.setup_guide}`);
        }
        setGmailLoading(false);
        return;
      }

      // Open Google authorization page
      setStatusMessage('Opening Google authorization page...');
      window.location.href = data.authorization_url;

    } catch (error) {
      console.error('OAuth initiation error:', error);
      setStatusMessage('Failed to connect to server. Make sure backend is running.');
      setGmailLoading(false);
    }
  };

  const fetchGmailMessages = async () => {
    setGmailLoading(true);
    setStatusMessage('Fetching Gmail messages...');
    
    try {
      const response = await fetch('http://localhost:5000/api/gmail/fetch', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ max_results: 20 })
      });

      const data = await response.json();

      if (!response.ok) {
        if (data.auth_required) {
          // Need to authenticate first
          await initiateGoogleOAuth();
          return;
        }
        setStatusMessage(data.error || 'Failed to fetch emails');
        setGmailLoading(false);
        return;
      }

      setStatusMessage(`Successfully fetched ${data.count} emails!`);
      console.log('Gmail messages:', data.messages);
      setGmailLoading(false);

    } catch (error) {
      console.error('Gmail fetch error:', error);
      setStatusMessage('Failed to fetch emails. Please try again.');
      setGmailLoading(false);
    }
  };

  const handleNotesSave = () => {
    // TODO: Save notes to backend
    console.log('Saving notes:', notes);
  };

  const handlePdfUpload = (file) => {
    // TODO: Upload PDF to backend
    console.log('Uploading PDF:', file);
  };

  const handleDriveFilesSelected = (files) => {
    // TODO: Send Google Drive file references to backend
    console.log('Selected files from Google Drive:', files);
  };

  const handleCalendarConnect = () => {
    // TODO: Integrate with Google Calendar API
    setCalendarConnected(!calendarConnected);
    console.log('Calendar connection toggled');
  };

  const saveOAuthCredentials = async ({ clientId, clientSecret }) => {
    try {
      const response = await fetch('http://localhost:5000/api/auth/google/configure', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          client_id: clientId,
          client_secret: clientSecret,
          redirect_uri: 'http://localhost:5000/api/auth/google/callback'
        })
      });

      const data = await response.json();

      if (!response.ok) {
        setStatusMessage(`Error: ${data.error || 'Failed to save credentials'}`);
        return false;
      }

      setStatusMessage('OAuth credentials saved successfully!');
      setOauthConfigured(true);
      
      // Now initiate OAuth flow
      setTimeout(() => {
        initiateGoogleOAuth();
      }, 500);
      
      return true;
    } catch (error) {
      console.error('Error saving OAuth credentials:', error);
      setStatusMessage('Failed to save credentials. Check backend connection.');
      return false;
    }
  };

  return (
    <>
      <OAuthSetupModal 
        isOpen={showOAuthModal}
        onClose={() => setShowOAuthModal(false)}
        onSave={saveOAuthCredentials}
      />
      
      <div className="min-h-screen bg-[var(--bg-main)] px-4 py-6 sm:px-6 lg:px-8 sm:py-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6 sm:mb-8 flex flex-col gap-3 sm:gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-xs uppercase tracking-[0.2em] text-teal-300">Dashboard</p>
            <h1 className="mt-2 text-2xl sm:text-3xl font-semibold text-white">Add your data sources</h1>
            <p className="mt-2 text-sm text-slate-400">All inputs are optional. Add only what you need before starting chat.</p>
          </div>
          <button
            type="button"
            onClick={() => navigate('/chat')}
            className="rounded-xl bg-teal-400 px-5 py-3 text-sm font-semibold text-slate-900 transition hover:brightness-110 w-full sm:w-auto flex-shrink-0"
          >
            Continue to Chat
          </button>
        </div>

        {/* Status Message */}
        {statusMessage && (
          <div className={`mb-4 rounded-xl border px-4 py-3 text-sm ${
            statusMessage.includes('Success') 
              ? 'border-teal-500/30 bg-teal-500/10 text-teal-300'
              : statusMessage.includes('Error')
              ? 'border-red-500/30 bg-red-500/10 text-red-300'
              : 'border-blue-500/30 bg-blue-500/10 text-blue-300'
          }`}>
            {statusMessage}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-5 shadow-lg transition hover:border-slate-500">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-100">Gmail Account</h3>
                <p className="mt-1 text-sm text-slate-400">Connect your Gmail inbox for email context ingestion.</p>
              </div>
              {gmailConnected && (
                <span className="flex items-center gap-2 text-xs text-teal-400">
                  <span className="h-2 w-2 rounded-full bg-teal-400" />
                  Connected
                </span>
              )}
            </div>
            <div className="mt-2 rounded-lg bg-slate-900/60 px-3 py-2 text-xs text-slate-500">
              💡 User authentication via Google OAuth 2.0. Click 'Connect Gmail' to authorize access to your inbox securely.
            </div>
            {!gmailConnected && (
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-4 w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
                placeholder="Your email (optional)"
              />
            )}
            <button
              type="button"
              onClick={handleEmailFetch}
              disabled={gmailLoading}
              className="mt-4 rounded-xl bg-teal-400 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {gmailLoading ? 'Connecting...' : gmailConnected ? 'Fetch Emails' : 'Connect Gmail'}
            </button>
          </div>

          <FileUploadCard
            title="PDF Upload"
            description="Upload PDF files from your computer."
            onUpload={handlePdfUpload}
          />

          <GoogleDriveCard onFilesSelected={handleDriveFilesSelected} />

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
    </>
  );
}

export default Dashboard;
