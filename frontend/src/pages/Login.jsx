import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Login({ onAuthSuccess }) {
  const [isSignup, setIsSignup] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const navigate = useNavigate();

  const handleSubmit = (event) => {
    event.preventDefault();
    // For this UI-only flow, we mark user authenticated after form submit.
    onAuthSuccess(formData.email || 'user@contextiq.ai');
    navigate('/dashboard');
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[radial-gradient(circle_at_top,_#1f2937,_#020617_55%)] px-4">
      <div className="pointer-events-none absolute inset-0 bg-[conic-gradient(from_180deg_at_50%_50%,rgba(20,184,166,0.18),transparent_35%,rgba(56,189,248,0.12),transparent_70%)]" />

      <form
        onSubmit={handleSubmit}
        className="relative z-10 w-full max-w-md rounded-3xl border border-slate-700/60 bg-slate-900/80 p-8 shadow-2xl backdrop-blur"
      >
        <p className="text-xs uppercase tracking-[0.2em] text-teal-300">ContextIQ</p>
        <h1 className="mt-3 text-3xl font-semibold text-white">
          {isSignup ? 'Create account' : 'Welcome back'}
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          {isSignup
            ? 'Build your context-aware executive workspace.'
            : 'Sign in to continue your conversations.'}
        </p>

        <div className="mt-8 space-y-4">
          <label className="block text-sm text-slate-300">
            Email
            <input
              type="email"
              required
              value={formData.email}
              onChange={(event) => setFormData((prev) => ({ ...prev, email: event.target.value }))}
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
              placeholder="you@company.com"
            />
          </label>

          <label className="block text-sm text-slate-300">
            Password
            <input
              type="password"
              required
              value={formData.password}
              onChange={(event) => setFormData((prev) => ({ ...prev, password: event.target.value }))}
              className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
              placeholder="••••••••"
            />
          </label>
        </div>

        <button
          type="submit"
          className="mt-6 w-full rounded-xl bg-teal-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110"
        >
          {isSignup ? 'Sign up' : 'Login'}
        </button>

        <button
          type="button"
          onClick={() => setIsSignup((prev) => !prev)}
          className="mt-4 w-full text-sm text-slate-400 transition hover:text-slate-200"
        >
          {isSignup ? 'Already have an account? Login' : "Don't have an account? Sign up"}
        </button>
      </form>
    </div>
  );
}

export default Login;
