import React from 'react';
import { 
  Shield, Activity, Lock, Eye, Share2, 
  BarChart3, AlertTriangle, Database, Users, Settings, FolderInput
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, userRole = 'USER' }) {
  const navItems = [
    { id: 'dashboard', label: 'Security Dashboard', icon: Activity, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'upload', label: 'Image Ingestion', icon: FolderInput, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'encrypt', label: 'Hybrid Encryption', icon: Lock, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'decrypt', label: 'Decryption & Verify', icon: Eye, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'shares', label: 'Secure Image Sharing', icon: Share2, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'evaluation', label: 'Security Evaluation', icon: BarChart3, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'monitoring', label: 'AI Anomaly Sentry', icon: AlertTriangle, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'audit', label: 'Audit Hash Chain', icon: Database, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'users', label: 'Clinician Directory', icon: Users, roles: ['USER', 'ADMIN', 'SUPER_ADMIN'] },
    { id: 'settings', label: 'System Policies', icon: Settings, roles: ['SUPER_ADMIN'] },
  ];

  const filteredNav = navItems.filter(item => item.roles.includes(userRole));

  return (
    <aside className="w-64 border-r border-slate-800 bg-[#0a0f1d]/90 backdrop-blur flex flex-col justify-between h-full">
      <div>
        <div className="p-6 border-b border-slate-800 flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-gradient-to-br from-sky-500/20 to-blue-600/10 border border-sky-500/30 text-sky-400 shadow-inner">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-extrabold text-base tracking-wider text-white">HICE</h1>
            <p className="text-[10px] text-sky-400 font-mono tracking-widest uppercase">Hybrid Platform</p>
          </div>
        </div>

        <nav className="p-4 space-y-1">
          {filteredNav.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-sky-500/15 text-sky-300 border border-sky-500/30 shadow-sm shadow-sky-500/10'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="p-4 border-t border-slate-800">
        <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
          <div className="flex justify-between items-center text-slate-300">
            <span>Research Edition</span>
            <span className="font-mono text-[10px] text-sky-400">v1.0</span>
          </div>
          <p className="text-[10px] text-slate-500">IND-CCA2 Authenticated Cipher</p>
        </div>
      </div>
    </aside>
  );
}
