import React from 'react';

export default function StatusBadge({ status, text }) {
  const styles = {
    ready: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    active: 'bg-sky-500/10 text-sky-400 border-sky-500/30',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    neutral: 'bg-slate-800 text-slate-300 border-slate-700'
  };

  const currentStyle = styles[status.toLowerCase()] || styles.neutral;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${currentStyle}`}>
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current animate-pulse"></span>
      {text || status.toUpperCase()}
    </span>
  );
}
