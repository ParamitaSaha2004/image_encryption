import React from 'react';
import { Shield, Lock, Eye, Share2, Activity, Cpu, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function Landing({ onGetStarted }) {
  return (
    <div className="min-h-screen bg-[#0a0f1d] text-slate-100 flex flex-col justify-between">
      {/* Top Banner */}
      <header className="border-b border-slate-800/80 px-8 py-5 flex items-center justify-between bg-[#0f172a]/40 backdrop-blur">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-wider text-white">SecurePix</h1>
          </div>
        </div>
        <button
          onClick={onGetStarted}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-sky-500/20"
        >
          <span>Access Vault</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </header>

      {/* Hero Section */}
      <main className="max-w-6xl mx-auto px-8 py-16 space-y-12">
        <div className="text-center space-y-6 max-w-3xl mx-auto">
          <h2 className="text-5xl md:text-6xl font-black text-white tracking-tight leading-tight">
            SecurePix
          </h2>

          <div className="pt-2 flex items-center justify-center space-x-4">
            <button
              onClick={onGetStarted}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-slate-950 font-bold text-sm tracking-wide shadow-xl shadow-sky-500/25 transition-all"
            >
              Launch Clinician Portal
            </button>
          </div>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { title: "Spatial Randomization", icon: Cpu },
            { title: "Provable Authenticity", icon: Lock },
            { title: "AI Behavioral Sentry", icon: Activity }
          ].map((card, i) => {
            const Icon = card.icon;
            return (
              <div key={i} className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-sky-500/30 transition-all space-y-3">
                <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-base text-white">{card.title}</h3>
              </div>
            );
          })}
        </div>

        {/* Medical Workflow Preview */}
        <div className="p-8 rounded-2xl bg-gradient-to-b from-slate-900/80 to-slate-950 border border-slate-800 space-y-6">
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span>Clinical Security Pipeline</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
              <span className="text-sky-400 font-bold">STAGE 1</span>
              <p className="text-slate-200 font-sans">Diagnostic Scan Ingestion</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
              <span className="text-sky-400 font-bold">STAGE 2</span>
              <p className="text-slate-200 font-sans">Hybrid Chaos + CA Scramble</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
              <span className="text-sky-400 font-bold">STAGE 3</span>
              <p className="text-sky-400 font-sans">AES-256-GCM Vault Locking</p>
            </div>
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
              <span className="text-emerald-400 font-bold">STAGE 4</span>
              <p className="text-slate-200 font-sans">ECDH Recipient Exchange</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500 font-mono">
        SecurePix
      </footer>
    </div>
  );
}
