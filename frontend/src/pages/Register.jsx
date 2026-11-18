import React, { useState } from 'react';
import { Shield, User, Mail, Lock, AlertCircle, ArrowLeft } from 'lucide-react';
import { authService } from '../services/authService';

export default function Register({ onRegisterSuccess, onGoToLogin }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [roleName, setRoleName] = useState('USER');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await authService.register(username, email, password, roleName);
      onRegisterSuccess(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please check inputs.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0f1d] flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        <button
          onClick={onGoToLogin}
          className="flex items-center space-x-2 text-xs font-mono text-slate-400 hover:text-sky-400 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>BACK TO SIGN IN</span>
        </button>

        <div className="p-8 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-2xl backdrop-blur space-y-6">
          <div className="text-center space-y-2">
            <div className="inline-flex p-3 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400 mb-2">
              <Shield className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight">Clinician Enrollment</h2>
            <p className="text-xs text-slate-400">Generate NIST P-256 Keypair & register secure identity</p>
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
                  placeholder="e.g. dr_smith"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 block">Work Email</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950/80 border border-slate-800 focus:border-sky-500 text-xs text-slate-100 placeholder-slate-600 outline-none transition-colors"
                  placeholder="doctor@hospital.org"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 block">Password (min 8 chars)</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-slate-950/80 border border-slate-800 focus:border-sky-500 text-xs text-slate-100 placeholder-slate-600 outline-none transition-colors"
                  placeholder="Create master password"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300 block">Account Role</label>
              <select
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-slate-950/80 border border-slate-800 focus:border-sky-500 text-xs text-slate-100 outline-none transition-colors"
              >
                <option value="USER">Clinician / Researcher (USER)</option>
                <option value="ADMIN">Security Administrator (ADMIN)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50"
            >
              {loading ? 'Registering & Generating Keys...' : 'Enroll Account'}
            </button>
          </form>

          <div className="text-center text-xs text-slate-500">
            Already enrolled?{' '}
            <button onClick={onGoToLogin} className="text-sky-400 hover:underline font-medium">
              Sign In
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
