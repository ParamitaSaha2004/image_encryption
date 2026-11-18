import React from 'react';
import { Shield, LogOut, User as UserIcon } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function Navbar({ user, onLogout }) {
  return (
    <header className="h-16 border-b border-slate-800 px-6 flex items-center justify-between bg-[#0f172a]/70 backdrop-blur sticky top-0 z-20">
      <div className="flex items-center space-x-3">
        <StatusBadge status="ready" text="VAULT ONLINE" />
        <span className="hidden md:inline-block text-xs font-mono text-slate-500">|</span>
        <span className="hidden md:inline-block text-xs font-mono text-slate-400">
          AES-256-GCM + ECDH P-256 + LOGISTIC MAP + RULE 30/90 CA
        </span>
      </div>

      <div className="flex items-center space-x-4">
        {user ? (
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700">
              <UserIcon className="w-4 h-4 text-sky-400" />
              <div className="text-left">
                <span className="text-xs font-bold text-slate-200 block leading-tight">{user.username}</span>
                <span className="text-[10px] text-sky-400 font-mono block leading-none">{user.role}</span>
              </div>
            </div>
            <button
              onClick={onLogout}
              title="Logout"
              className="p-2 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-400 hover:text-rose-400 hover:border-rose-500/30 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <span className="text-xs font-mono text-slate-400">AUTHENTICATION REQUIRED</span>
        )}
      </div>
    </header>
  );
}
