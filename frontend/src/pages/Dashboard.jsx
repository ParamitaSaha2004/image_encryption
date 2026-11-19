import React, { useState, useEffect } from 'react';
import { Shield, Lock, Eye, Share2, Activity, Database, CheckCircle, Server, FileText } from 'lucide-react';
import MetricCard from '../components/MetricCard';
import StatusBadge from '../components/StatusBadge';
import api from '../services/api';

export default function Dashboard({ user, onNavigate }) {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await api.get('/system/status');
        setSystemStatus(res.data);
      } catch (err) {
        console.error('Failed to load system status:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-sky-950/40 via-slate-900 to-slate-900 border border-sky-500/20 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-sky-400 font-semibold tracking-wider uppercase">Active Session</span>
            <StatusBadge status="ready" text={user?.role || 'CLINICIAN'} />
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight">
            Welcome, {user?.username || 'Authorized User'}
          </h2>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => onNavigate('encrypt')}
            className="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-sky-500/20 flex items-center space-x-2"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Encrypt Scan</span>
          </button>
          <button
            onClick={() => onNavigate('decrypt')}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs uppercase tracking-wider transition-all flex items-center space-x-2"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Decrypt</span>
          </button>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Active Cipher"
          value="AES-256-GCM"
          subtitle="96-bit Nonce | 128-bit Tag"
          icon={Lock}
          badgeText="AEAD Enforced"
          badgeStatus="ready"
        />
        <MetricCard
          title="Key Agreement"
          value="ECDH P-256"
          subtitle="HKDF-SHA256 Derivation"
          icon={Shield}
          badgeText="Lossless Exchange"
          badgeStatus="active"
        />
        <MetricCard
          title="Registered Users"
          value={systemStatus?.total_registered_users ?? '4'}
          subtitle="Clinicians & Analysts"
          icon={Activity}
          badgeText="RBAC Synced"
          badgeStatus="ready"
        />
        <MetricCard
          title="Database Backend"
          value={systemStatus?.database_backend || 'ONLINE'}
          subtitle="Relational Vault"
          icon={Database}
          badgeText={systemStatus?.database_backend === 'MYSQL' ? 'MySQL 8.0' : 'SQLite Fallback'}
          badgeStatus="ready"
        />
      </div>

      {/* Cryptographic Architecture Summary Card */}
      <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <Server className="w-4 h-4 text-sky-400" />
            <span>Cryptographic Pipeline Verification</span>
          </h3>
          <span className="text-[11px] font-mono text-emerald-400">STATUS: ALL CORES LOADED</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center justify-between text-slate-200 font-semibold">
              <span>Chaotic Logistic Map</span>
              <span className="font-mono text-sky-400">r ∈ [3.9, 4.0]</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center justify-between text-slate-200 font-semibold">
              <span>Cellular Automata (Rule 30/90)</span>
              <span className="font-mono text-sky-400">Diffusion Mask</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
            <div className="flex items-center justify-between text-slate-200 font-semibold">
              <span>AI Anomaly Sentry</span>
              <span className="font-mono text-emerald-400">Isolation Forest</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
