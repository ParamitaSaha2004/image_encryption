import React, { useState } from 'react';
import { Shield, KeyRound, User, Lock, AlertCircle, ArrowLeft } from 'lucide-react';
import { authService } from '../services/authService';

export default function Login({ onLoginSuccess, onGoToRegister, onBackToLanding }) {
  const [username, setUsername] = useState('dr_alice_radiology');
  const [password, setPassword] = useState('Password123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await authService.login(username, password);
      onLoginSuccess(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const setDemoAccount = (u, p) => {
    setUsername(u);
    setPassword(p);
    setError('');
  };

  return (
    <div className="min-h-screen bg-[#0a0f1d] flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        <button
          onClick={onBackToLanding}
          className="flex items-center space-x-2 text-xs font-mono text-slate-400 hover:text-sky-400 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>BACK TO SYSTEM OVERVIEW</span>
        </button>

        <div className="p-8 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-2xl backdrop-blur space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex p-3 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400 mb-2">
              <Shield className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">Clinician Authentication</h2>
            <p className="text-xs text-slate-400">Authenticate to decrypt authorized medical records</p>
          </div>

          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 block">Username</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950/80 border border-slate-800 focus:border-sky-500 text-xs text-slate-100 placeholder-slate-600 outline-none transition-colors"
                  placeholder="Enter username"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 block">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950/80 border border-slate-800 focus:border-sky-500 text-xs text-slate-100 placeholder-slate-600 outline-none transition-colors"
                  placeholder="Enter password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50"
            >
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>
          </form>

          {/* Quick Fill Demo Roles */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <span className="text-[10px] font-mono text-slate-500 block uppercase tracking-wider text-center">
              Quick Demonstration Credentials
            </span>
            <div className="grid grid-cols-3 gap-2 text-[10px] font-mono">
              <button
                type="button"
                onClick={() => setDemoAccount('dr_alice_radiology', 'Password123!')}
                className="p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 text-center truncate"
              >
                Dr. Alice (User)
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('sec_admin', 'Password123!')}
                className="p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 text-center truncate"
              >
                Sec Admin
              </button>
              <button
                type="button"
                onClick={() => setDemoAccount('superadmin', 'Password123!')}
                className="p-1.5 rounded bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 text-center truncate"
              >
                Super Admin
              </button>
            </div>
          </div>

          <div className="text-center text-xs text-slate-500">
            Need an account?{' '}
            <button onClick={onGoToRegister} className="text-sky-400 hover:underline font-medium">
              Register as clinician
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
