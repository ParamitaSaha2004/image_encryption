import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, ShieldAlert, Activity, CheckCircle2, 
  RefreshCw, Flame, Zap, ShieldCheck, Clock, UserX, Key
} from 'lucide-react';
import { monitoringService } from '../services/monitoringService';
import StatusBadge from '../components/StatusBadge';

export default function AiMonitoring() {
  const [stats, setStats] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [simMessage, setSimMessage] = useState(null);

  useEffect(() => {
    fetchMonitoringData();
  }, []);

  const fetchMonitoringData = async () => {
    setLoading(true);
    try {
      const [statsData, alertsData] = await Promise.all([
        monitoringService.getStats(),
        monitoringService.getAlerts()
      ]);
      setStats(statsData);
      setAlerts(alertsData.alerts || []);
    } catch (err) {
      console.error('Failed to fetch AI monitoring data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateAttack = async (type) => {
    setSimulating(true);
    setSimMessage(null);
    try {
      const res = await monitoringService.simulateAttack(type);
      setSimMessage({
        type,
        detail: res.detection_result?.reason || 'Attack simulated successfully.',
        risk: res.detection_result?.risk_score,
        severity: res.detection_result?.severity
      });
      await fetchMonitoringData();
    } catch (err) {
      alert('Failed to simulate attack.');
    } finally {
      setSimulating(false);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await monitoringService.resolveAlert(alertId);
      await fetchMonitoringData();
    } catch (err) {
      alert('Failed to resolve alert.');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              Phase 10: Active
            </span>
            <span className="text-xs font-mono text-slate-400">Unsupervised Scikit-Learn Isolation Forest</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">AI Suspicious Activity Monitoring Sentry</h1>
        </div>

        <button
          onClick={fetchMonitoringData}
          className="px-4 py-2 bg-slate-900 border border-slate-800 text-slate-300 hover:text-white rounded-xl text-xs font-medium transition flex items-center space-x-2"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Telemetry</span>
        </button>
      </div>

      {/* Threat Posture Gauge Banner */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Threat Posture</span>
            <div className="flex items-center space-x-2">
              <span className={`text-xl font-extrabold ${
                stats.overall_threat_level === 'CRITICAL' ? 'text-rose-400' :
                stats.overall_threat_level === 'ELEVATED' ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {stats.overall_threat_level}
              </span>
            </div>
            <p className="text-[11px] text-slate-500">Live system threat index</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Avg Risk Score</span>
            <div className="text-xl font-extrabold text-white font-mono">
              {stats.average_unresolved_risk_score} <span className="text-xs text-slate-500">/ 100</span>
            </div>
            <p className="text-[11px] text-slate-500">Based on unresolved anomalies</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Active Unresolved</span>
            <div className="text-xl font-extrabold text-rose-400 font-mono">
              {stats.active_unresolved_alerts}
            </div>
            <p className="text-[11px] text-slate-500">Total flags requiring review</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Critical Incidents</span>
            <div className="text-xl font-extrabold text-red-500 font-mono">
              {stats.severity_breakdown?.CRITICAL || 0}
            </div>
            <p className="text-[11px] text-slate-500">Nocturnal or exfiltration alerts</p>
          </div>
        </div>
      )}

      {/* Attack Simulation Station */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 to-indigo-950/40 border border-indigo-500/20 space-y-4">
        <div className="flex items-center space-x-2">
          <Zap className="w-5 h-5 text-amber-400" />
          <h2 className="text-base font-bold text-white">Live Adversary Simulation Station (Demonstration Testbed)</h2>
        </div>
        <p className="text-xs text-slate-400 max-w-3xl">
          Trigger simulated cyber threat patterns to demonstrate real-time AI anomaly classification, risk scoring, and alert generation.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
          <button
            onClick={() => handleSimulateAttack('NOCTURNAL_BULK_DOWNLOAD')}
            disabled={simulating}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-rose-500/40 text-left transition space-y-1 group"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-rose-400">
              <span>Nocturnal Bulk Exfiltration</span>
              <Clock className="w-4 h-4 text-slate-500 group-hover:text-rose-400" />
            </div>
            <p className="text-[11px] text-slate-400">Simulates anomalous 03:00 UTC rapid scan downloads.</p>
          </button>

          <button
            onClick={() => handleSimulateAttack('BRUTE_FORCE_DECRYPTION')}
            disabled={simulating}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-amber-500/40 text-left transition space-y-1 group"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-amber-400">
              <span>Decryption Brute-Force</span>
              <Key className="w-4 h-4 text-slate-500 group-hover:text-amber-400" />
            </div>
            <p className="text-[11px] text-slate-400">Simulates repeated key-guessing decryption failures.</p>
          </button>

          <button
            onClick={() => handleSimulateAttack('CREDENTIAL_STUFFING')}
            disabled={simulating}
            className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-sky-500/40 text-left transition space-y-1 group"
          >
            <div className="flex items-center justify-between text-xs font-semibold text-sky-400">
              <span>Credential Stuffing Spray</span>
              <UserX className="w-4 h-4 text-slate-500 group-hover:text-sky-400" />
            </div>
            <p className="text-[11px] text-slate-400">Simulates rapid authentication password spray.</p>
          </button>
        </div>

        {simMessage && (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 flex items-start space-x-3 mt-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-white">
                Anomaly Detected by Sentry [{simMessage.severity}] - Risk Score: {simMessage.risk} / 100
              </div>
              <div className="text-slate-400 text-[11px] mt-0.5">{simMessage.detail}</div>
            </div>
          </div>
        )}
      </div>

      {/* Security Alerts Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-slate-800 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <h2 className="text-base font-bold text-white">Real-Time Security Threat Intelligence Feed</h2>
          </div>
          <span className="text-xs font-mono text-slate-400">{alerts.length} Total Alerts</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-4">Alert Type</th>
                <th className="p-4">Severity</th>
                <th className="p-4">Risk Score</th>
                <th className="p-4">Detection Engine</th>
                <th className="p-4">Reason / Heuristic Details</th>
                <th className="p-4">Timestamp</th>
                <th className="p-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-500">
                    No suspicious anomalies detected. System operating within normal behavioral baseline.
                  </td>
                </tr>
              ) : (
                alerts.map((a) => (
                  <tr key={a.alert_id} className="hover:bg-slate-800/30 transition">
                    <td className="p-4 font-semibold text-white">{a.alert_type}</td>
                    <td className="p-4">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                          a.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                          a.severity === 'HIGH' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                          a.severity === 'MEDIUM' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                          'bg-sky-500/10 text-sky-400 border-sky-500/20'
                        }`}
                      >
                        {a.severity}
                      </span>
                    </td>
                    <td className="p-4 font-mono font-bold text-white">{a.risk_score}</td>
                    <td className="p-4 font-mono text-slate-400 text-[10px]">{a.detection_source}</td>
                    <td className="p-4 text-slate-300 max-w-sm truncate" title={a.reason}>{a.reason}</td>
                    <td className="p-4 font-mono text-slate-400 text-[11px]">
                      {a.created_at ? new Date(a.created_at).toLocaleTimeString() : 'N/A'}
                    </td>
                    <td className="p-4 text-right">
                      {!a.is_resolved ? (
                        <button
                          onClick={() => handleResolveAlert(a.alert_id)}
                          className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium transition"
                        >
                          Resolve
                        </button>
                      ) : (
                        <span className="text-emerald-400 text-xs font-medium inline-flex items-center space-x-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Resolved</span>
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
