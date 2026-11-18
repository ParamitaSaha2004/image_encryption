import React, { useState, useEffect } from 'react';
import { Settings, ShieldCheck, Database, Sliders } from 'lucide-react';
import api from '../services/api';

export default function SystemSettings() {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await api.get('/system/settings');
        setSettings(res.data);
      } catch (err) {
        console.error('Failed to load system settings:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  return (
    <div className="p-8 space-y-6 max-w-5xl mx-auto">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
          <Settings className="w-5 h-5 text-sky-400" />
          <span>Cryptographic Security Policies</span>
        </h2>
        <p className="text-xs text-slate-400">
          Governs encryption thresholds, AI anomaly parameters, and tamper verification rules
        </p>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-4">
        {loading ? (
          <p className="text-xs text-slate-500 font-mono">Loading system policies...</p>
        ) : (
          <div className="space-y-4">
            {Object.entries(settings).map(([key, value]) => (
              <div key={key} className="p-4 rounded-lg bg-slate-950/60 border border-slate-800/80 flex flex-col md:flex-row justify-between items-start md:items-center gap-2">
                <div>
                  <span className="text-xs font-mono font-bold text-slate-200">{key}</span>
                  <p className="text-[11px] text-slate-500">Security configuration parameter</p>
                </div>
                <span className="px-3 py-1 rounded bg-slate-900 border border-slate-800 text-sky-400 font-mono text-xs max-w-sm truncate">
                  {value}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
