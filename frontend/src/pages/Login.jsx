import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function Login({ onAuthSuccess }) {
  const [isSignup, setIsSignup] = useState(false);
  const [formData, setFormData] = useState({ email: '', password: '', name: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const endpoint = isSignup ? '/api/auth/signup' : '/api/auth/login';
      const body = isSignup 
        ? { email: formData.email, password: formData.password, name: formData.name }
        : { email: formData.email, password: formData.password };

      const response = await fetch(`http://localhost:5000${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (!response.ok) {
        // Show specific error from backend
        setError(data.error || 'Authentication failed');
        setLoading(false);
        return;
      }

      // Store token and user data
      localStorage.setItem('token', data.token);
      localStorage.setItem('user', JSON.stringify(data.user));

      // Mark user as authenticated
      onAuthSuccess(data.user.email);

      // Navigate to dashboard
      navigate('/dashboard');

    } catch (err) {
      setError('Failed to connect to server. Make sure backend is running.');
      setLoading(false);
    }
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

        {/* Error Message */}
        {error && (
          <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="mt-6 space-y-4">
          {/* Name field (only for signup) */}
          {isSignup && (
            <label className="block text-sm text-slate-300">
              Full Name
              <input
                type="text"
                required
                value={formData.name}
                onChange={(event) => setFormData((prev) => ({ ...prev, name: event.target.value }))}
                className="mt-1 w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-slate-100 placeholder:text-slate-500 focus:border-teal-400 focus:outline-none"
                placeholder="John Doe"
              />
            </label>
          )}

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

        {/* Password Requirements (only for signup) */}
        {isSignup && (
          <div className="mt-4 rounded-xl border border-slate-700/50 bg-slate-800/50 px-4 py-3">
            <p className="text-xs font-semibold text-slate-300 mb-2">Password must contain:</p>
            <ul className="text-xs text-slate-400 space-y-1">
              <li>• At least 8 characters</li>
              <li>• One uppercase letter (A-Z)</li>
              <li>• One lowercase letter (a-z)</li>
              <li>• One digit (0-9)</li>
              <li>• One special character (!@#$%^&*)</li>
            </ul>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full rounded-xl bg-teal-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Please wait...' : (isSignup ? 'Sign up' : 'Login')}
        </button>

        <button
          type="button"
          onClick={() => {
            setIsSignup((prev) => !prev);
            setError('');
            setFormData({ email: '', password: '', name: '' });
          }}
          className="mt-4 w-full text-sm text-slate-400 transition hover:text-slate-200"
        >
          {isSignup ? 'Already have an account? Login' : "Don't have an account? Sign up"}
        </button>
      </form>
    </div>
  );
}

export default Login;
