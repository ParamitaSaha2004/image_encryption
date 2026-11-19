import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, Shield, Activity, Flame, ShieldAlert, CheckCircle2, 
  RefreshCw, Zap, Radio, UserX, Clock, Server, ArrowUpRight
} from 'lucide-react';
import api from '../services/api';

export default function AiMonitoring() {
  const [threatData, setThreatData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [selectedAttack, setSelectedAttack] = useState('BRUTE_FORCE');

  useEffect(() => {
    fetchTelemetry();
  }, []);

  const fetchTelemetry = async () => {
    setLoading(true);
    try {
      const [threatRes, alertsRes] = await Promise.all([
        api.get('/ai/threat-level'),
        api.get('/ai/alerts')
      ]);
      setThreatData(threatRes.data);
      setAlerts(alertsRes.data);
    } catch (err) {
      console.error('Failed to fetch AI telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateAttack = async (type) => {
    setSimulating(true);
    try {
      await api.post(`/ai/simulate-attack?attack_type=${type}`);
      await fetchTelemetry();
    } catch (err) {
      console.error('Failed to simulate attack:', err);
    } finally {
      setSimulating(false);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await api.post(`/ai/resolve-alert/${alertId}`);
      await fetchTelemetry();
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const score = threatData?.risk_score || 12.5;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                AI Threat Sentry & Behavioral Anomaly Detection
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Phase 10 Intelligence Layer: Scikit-learn Isolation Forest (unsupervised) + Heuristic Hard-Rule Sentry
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={fetchTelemetry}
          disabled={loading}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold rounded-xl flex items-center space-x-2 transition-all self-start md:self-auto shadow-sm"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Top Threat Gauge & Key Indicators */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Threat Level Dial Card (5 cols) */}
        <div className="lg:col-span-5 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
            <Radio className="w-4 h-4 text-amber-400 animate-pulse" />
            <span>Real-Time Clinical Threat Level</span>
          </h3>

          <div className="flex flex-col items-center justify-center p-6 space-y-4">
            {/* Visual Gauge Representation */}
            <div className="relative w-44 h-44 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90">
                <circle
                  cx="88"
                  cy="88"
                  r="74"
                  stroke="#1e293b"
                  strokeWidth="14"
                  fill="transparent"
                />
                <circle
                  cx="88"
                  cy="88"
                  r="74"
                  stroke={
                    score >= 75 ? '#f43f5e' : score >= 50 ? '#f59e0b' : score >= 25 ? '#38bdf8' : '#10b981'
                  }
                  strokeWidth="14"
                  strokeDasharray={465}
                  strokeDashoffset={465 - (465 * score) / 100}
                  strokeLinecap="round"
                  fill="transparent"
                  className="transition-all duration-1000 ease-out"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="text-3xl font-extrabold text-white font-mono tracking-tight">
                  {score.toFixed(1)}%
                </span>
                <span className={`text-[10px] font-mono uppercase font-bold tracking-widest mt-0.5 ${
                  threatData?.threat_level === 'CRITICAL' ? 'text-rose-400' :
                  threatData?.threat_level === 'HIGH' ? 'text-amber-400' :
                  threatData?.threat_level === 'MEDIUM' ? 'text-sky-400' : 'text-emerald-400'
                }`}>
                  {threatData?.threat_level || 'LOW'} TIER
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-300 text-center leading-relaxed max-w-xs">
              {threatData?.status_text || 'All behavioral dimensions within normal operating limits.'}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono pt-2 border-t border-slate-800">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
              <span className="text-slate-500 text-[10px] uppercase">Unresolved Alerts:</span>
              <p className="text-base font-bold text-amber-400 mt-0.5">
                {threatData?.active_alerts_count || 0}
              </p>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
              <span className="text-slate-500 text-[10px] uppercase">Recent Failed Logins:</span>
              <p className="text-base font-bold text-rose-400 mt-0.5">
                {threatData?.recent_login_failures || 0}
              </p>
            </div>
          </div>
        </div>

        {/* Live Attack Simulation Triggers (7 cols) */}
        <div className="lg:col-span-7 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>Simulated Adversary Attack Triggers</span>
            </h3>
            <span className="text-[10px] font-mono text-slate-500">Live Stress Testing</span>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Trigger real-world cybersecurity threat patterns to evaluate how the Isolation Forest pipeline and hard heuristic rules adjust the threat score and log forensic telemetry.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => handleSimulateAttack('BRUTE_FORCE')}
              disabled={simulating}
              className="p-4 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 hover:border-rose-500/40 text-left transition-all space-y-1.5 group"
            >
              <div className="flex items-center justify-between text-xs font-bold text-white group-hover:text-rose-400">
                <span>Brute-Force Credential Stuffing</span>
                <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-rose-400" />
              </div>
              <p className="text-[11px] text-slate-500">
                Fires 8 rapid consecutive failed authentication bursts against clinician accounts.
              </p>
            </button>

            <button
              onClick={() => handleSimulateAttack('ANOMALOUS_ACCESS')}
              disabled={simulating}
              className="p-4 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 hover:border-amber-500/40 text-left transition-all space-y-1.5 group"
            >
              <div className="flex items-center justify-between text-xs font-bold text-white group-hover:text-amber-400">
                <span>Nocturnal IP Drift Anomaly</span>
                <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-amber-400" />
              </div>
              <p className="text-[11px] text-slate-500">
                Simulates access at 03:22 AM UTC via unmapped foreign proxy tunnel.
              </p>
            </button>

            <button
              onClick={() => handleSimulateAttack('DECRYPTION_FAILURES')}
              disabled={simulating}
              className="p-4 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 hover:border-purple-500/40 text-left transition-all space-y-1.5 group"
            >
              <div className="flex items-center justify-between text-xs font-bold text-white group-hover:text-purple-400">
                <span>AEAD Tampering Burst</span>
                <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-purple-400" />
              </div>
              <p className="text-[11px] text-slate-500">
                Consecutive GHASH tag verification rejections indicating active cipher alteration.
              </p>
            </button>

            <button
              onClick={() => handleSimulateAttack('HIGH_VELOCITY_SCRAPING')}
              disabled={simulating}
              className="p-4 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 hover:border-sky-500/40 text-left transition-all space-y-1.5 group"
            >
              <div className="flex items-center justify-between text-xs font-bold text-white group-hover:text-sky-400">
                <span>Mass Exfiltration Spike</span>
                <ArrowUpRight className="w-4 h-4 text-slate-500 group-hover:text-sky-400" />
              </div>
              <p className="text-[11px] text-slate-500">
                Download velocity 4.2x above baseline (52 patient scans extracted in 10 minutes).
              </p>
            </button>
          </div>
        </div>
      </div>

      {/* Security Alert Feed */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>Forensic Incident & Anomaly Alert Feed ({alerts.length})</span>
          </h3>
          <span className="text-xs text-slate-500 font-mono">Sorted by severity & risk score</span>
        </div>

        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.alert_id}
              className={`p-4 rounded-xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                alert.is_resolved
                  ? 'bg-slate-950/40 border-slate-800/60 opacity-60'
                  : alert.severity === 'CRITICAL'
                  ? 'bg-rose-950/20 border-rose-500/40'
                  : alert.severity === 'HIGH'
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-slate-950 border-slate-800'
              }`}
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center space-x-2.5">
                  <span className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-full ${
                    alert.severity === 'CRITICAL' ? 'bg-rose-500/20 text-rose-400' :
                    alert.severity === 'HIGH' ? 'bg-amber-500/20 text-amber-400' :
                    alert.severity === 'MEDIUM' ? 'bg-sky-500/20 text-sky-400' : 'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {alert.severity} ({alert.risk_score} pts)
                  </span>
                  <span className="text-xs font-bold text-white font-mono">{alert.alert_type}</span>
                  <span className="text-[10px] text-slate-500 font-mono">via {alert.detection_source}</span>
                </div>
                <p className="text-xs text-slate-300">
                  {alert.reason}
                </p>
                <div className="text-[11px] text-slate-500 font-mono">
                  Target Subject: <span className="text-slate-300">{alert.username}</span>
                </div>
              </div>

              <div className="flex items-center space-x-3 flex-shrink-0">
                {alert.is_resolved ? (
                  <span className="text-xs font-mono text-emerald-400 flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Mitigated</span>
                  </span>
                ) : (
                  <button
                    onClick={() => handleResolveAlert(alert.alert_id)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all border border-slate-700"
                  >
                    Mark Resolved
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
