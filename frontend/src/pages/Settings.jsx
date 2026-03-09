import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Settings() {
  const navigate = useNavigate();
  
  // Mock data - replace with actual data from backend/context
  const [userInfo] = useState({
    email: 'user@example.com',
    connectedServices: {
      gmail: { connected: true, email: 'user@gmail.com' },
      calendar: { connected: true },
      drive: { connected: true, filesCount: 3 },
    },
    uploadedFiles: {
      pdfs: ['Resume.pdf', 'Project_Plan.pdf'],
    },
    notes: 'Meeting notes from last week...',
  });

  return (
    <div className="min-h-screen bg-[var(--bg-main)] text-slate-100">
      {/* Header */}
      <div className="border-b border-slate-800 bg-[var(--surface-2)]/90 px-4 py-4 sm:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => navigate('/chat')}
              className="rounded-lg p-2 transition hover:bg-slate-800"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h1 className="text-xl font-semibold">Settings & Profile</h1>
              <p className="text-sm text-slate-400">Manage your account and data sources</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-8 sm:px-8">
        <div className="mx-auto max-w-4xl space-y-6">
          {/* Profile Section */}
          <section className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-6">
            <div className="mb-4 flex items-center gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-teal-400/20">
                <svg className="h-8 w-8 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-slate-100">Profile</h2>
                <p className="text-sm text-slate-400">{userInfo.email}</p>
              </div>
            </div>
          </section>

          {/* Connected Services */}
          <section className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-6">
            <h2 className="mb-4 text-lg font-semibold text-slate-100">Connected Services</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950 px-4 py-3">
                <div className="flex items-center gap-3">
                  <svg className="h-5 w-5 text-teal-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-slate-200">Gmail</p>
                    <p className="text-xs text-slate-500">{userInfo.connectedServices.gmail.email}</p>
                  </div>
                </div>
                <span className="flex items-center gap-2 text-xs text-teal-400">
                  <span className="h-2 w-2 rounded-full bg-teal-400" />
                  Connected
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950 px-4 py-3">
                <div className="flex items-center gap-3">
                  <svg className="h-5 w-5 text-teal-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M7.71 3.5L1.15 15l3.58 6.5L11.29 9.5 7.71 3.5M9.73 15L6.15 21.5h14.5L24.23 15H9.73M22.28 14l-3.58-6.5-7.43 12.5 3.58 6.5L22.28 14z" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-slate-200">Google Drive</p>
                    <p className="text-xs text-slate-500">{userInfo.connectedServices.drive.filesCount} files selected</p>
                  </div>
                </div>
                <span className="flex items-center gap-2 text-xs text-teal-400">
                  <span className="h-2 w-2 rounded-full bg-teal-400" />
                  Connected
                </span>
              </div>

              <div className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950 px-4 py-3">
                <div className="flex items-center gap-3">
                  <svg className="h-5 w-5 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <div>
                    <p className="text-sm font-medium text-slate-200">Google Calendar</p>
                    <p className="text-xs text-slate-500">Events synced</p>
                  </div>
                </div>
                <span className="flex items-center gap-2 text-xs text-teal-400">
                  <span className="h-2 w-2 rounded-full bg-teal-400" />
                  Connected
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="mt-4 w-full rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-teal-400 hover:text-teal-300"
            >
              Manage Data Sources
            </button>
          </section>

          {/* Uploaded Files */}
          <section className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-6">
            <h2 className="mb-4 text-lg font-semibold text-slate-100">Uploaded Files</h2>
            <div className="space-y-2">
              {userInfo.uploadedFiles.pdfs.map((filename, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between rounded-xl border border-slate-700 bg-slate-950 px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    <span className="text-sm text-slate-200">{filename}</span>
                  </div>
                  <button className="text-xs text-slate-500 hover:text-red-400">Remove</button>
                </div>
              ))}
            </div>
          </section>

          {/* Notes Preview */}
          <section className="rounded-2xl border border-slate-700 bg-[var(--surface-1)] p-6">
            <h2 className="mb-4 text-lg font-semibold text-slate-100">Saved Notes</h2>
            <div className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-3">
              <p className="text-sm text-slate-300">{userInfo.notes}</p>
            </div>
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="mt-4 rounded-xl border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-teal-400 hover:text-teal-300"
            >
              Edit Notes
            </button>
          </section>

          {/* Danger Zone */}
          <section className="rounded-2xl border border-red-900/50 bg-red-950/20 p-6">
            <h2 className="mb-2 text-lg font-semibold text-red-400">Danger Zone</h2>
            <p className="mb-4 text-sm text-slate-400">Irreversible actions</p>
            <button
              type="button"
              className="rounded-xl border border-red-800 bg-red-950/50 px-4 py-2 text-sm font-medium text-red-400 transition hover:bg-red-900/50"
            >
              Clear All Data
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}

export default Settings;
