import React from 'react';

export default function MetricCard({ title, value, subtitle, icon: Icon, badgeText, badgeStatus = 'ready' }) {
  return (
    <div className="p-5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-all shadow-lg flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</span>
        {Icon && (
          <div className="p-2 rounded-lg bg-sky-500/10 border border-sky-500/20 text-sky-400">
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="my-3">
        <div className="text-2xl font-bold font-mono text-white tracking-tight">{value}</div>
        {subtitle && <p className="text-xs text-slate-400 mt-1 font-mono">{subtitle}</p>}
      </div>

      {badgeText && (
        <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
          <span className="text-[11px] text-slate-500">Status</span>
          <span className="text-xs font-mono text-sky-400">{badgeText}</span>
        </div>
      )}
    </div>
  );
}
