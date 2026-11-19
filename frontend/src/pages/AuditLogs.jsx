import React, { useState, useEffect } from 'react';
import { 
  Database, ShieldCheck, ShieldAlert, RefreshCw, AlertTriangle, 
  Link, CheckCircle2, Lock, Flame, ArrowRight, Activity
} from 'lucide-react';
import { auditService } from '../services/auditService';
import StatusBadge from '../components/StatusBadge';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [tampering, setTampering] = useState(false);
  const [tamperMessage, setTamperMessage] = useState(null);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await auditService.getLogs({ limit: 50 });
      setLogs(data.logs || []);
    } catch (err) {
      console.error('Failed to fetch audit ledger:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyIntegrity = async () => {
    setVerifying(true);
    setTamperMessage(null);
    try {
      const result = await auditService.verifyIntegrity();
      setVerificationResult(result);
    } catch (err) {
      alert('Verification request failed.');
    } finally {
      setVerifying(false);
    }
  };

  const handleSimulateTamper = async () => {
    if (!window.confirm('Simulate malicious retroactive modification of historical audit record?')) return;
    setTampering(true);
    try {
      const res = await auditService.simulateTampering();
      setTamperMessage(res.message);
      await fetchLogs();
      // Automatically re-verify to show live detection!
      const verifyRes = await auditService.verifyIntegrity();
      setVerificationResult(verifyRes);
    } catch (err) {
      alert('Failed to simulate tampering.');
    } finally {
      setTampering(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
              Phase 9: Active
            </span>
            <span className="text-xs font-mono text-slate-400">Cryptographic Hash-Chained Audit Ledger</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Tamper-Evident SHA-256 Audit Trail</h1>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleSimulateTamper}
            disabled={tampering}
            className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-xl text-xs font-semibold transition flex items-center space-x-2"
          >
            <Flame className="w-4 h-4" />
            <span>{tampering ? 'Tampering...' : 'Simulate Malicious Tampering'}</span>
          </button>

          <button
            onClick={handleVerifyIntegrity}
            disabled={verifying}
            className="px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white rounded-xl text-xs font-semibold transition shadow-lg shadow-emerald-500/20 flex items-center space-x-2"
          >
            {verifying ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <ShieldCheck className="w-4 h-4" />
            )}
            <span>Verify Ledger Integrity</span>
          </button>
        </div>
      </div>

      {/* Verification Shield Banner */}
      {verificationResult && (
        <div
          className={`p-6 rounded-2xl border transition-all ${
            verificationResult.is_valid
              ? 'bg-emerald-950/20 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-950/20 border-rose-500/40 text-rose-300'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              {verificationResult.is_valid ? (
                <div className="p-3 bg-emerald-500/20 rounded-xl text-emerald-400">
                  <ShieldCheck className="w-8 h-8" />
                </div>
              ) : (
                <div className="p-3 bg-rose-500/20 rounded-xl text-rose-400 animate-pulse">
                  <ShieldAlert className="w-8 h-8" />
                </div>
              )}
              <div>
                <h3 className="text-base font-bold text-white">
                  {verificationResult.is_valid
                    ? 'Cryptographic Hash-Chain Intact & Untampered'
                    : 'CRITICAL ALERT: Audit Ledger Tampering Detected!'}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {verificationResult.message || verificationResult.reason}
                </p>
              </div>
            </div>

            <div className="text-right text-xs font-mono space-y-1">
              <div>Total Records Verified: <span className="text-white font-bold">{verificationResult.verified_count} / {verificationResult.total_records}</span></div>
              {!verificationResult.is_valid && (
                <div className="text-rose-400 font-bold">
                  Broken at Block #{verificationResult.broken_at_id} (Index: {verificationResult.broken_at_index})
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-4 text-[11px] font-mono">
            <div className="truncate">
              <span className="text-slate-500">GENESIS HASH: </span>
              <span className="text-slate-300">{verificationResult.genesis_hash}</span>
            </div>
            <div className="truncate text-right">
              <span className="text-slate-500">HEAD HASH: </span>
              <span className="text-sky-400">{verificationResult.head_hash || 'RECALCULATION_ABORTED'}</span>
            </div>
          </div>
        </div>
      )}

      {tamperMessage && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{tamperMessage} - Notice that the cryptographic verification immediately flagged the alteration!</span>
        </div>
      )}

      {/* Ledger Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-slate-800 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-white">Immutable Event Blocks</h2>
          </div>
          <button onClick={fetchLogs} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-4">Block #</th>
                <th className="p-4">Timestamp (UTC)</th>
                <th className="p-4">Action</th>
                <th className="p-4">Resource</th>
                <th className="p-4">Status</th>
                <th className="p-4">Previous Hash</th>
                <th className="p-4">Current Block Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-500">
                    No audit records registered yet. Perform an upload, encryption, or share action to begin the chain.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const isCorrupted = verificationResult && !verificationResult.is_valid && verificationResult.broken_at_id === log.log_id;
                  return (
                    <tr
                      key={log.log_id}
                      className={`transition ${
                        isCorrupted ? 'bg-rose-950/40 border-l-4 border-l-rose-500' : 'hover:bg-slate-800/30'
                      }`}
                    >
                      <td className="p-4 font-mono font-bold text-white">#{log.log_id}</td>
                      <td className="p-4 font-mono text-slate-400 text-[11px]">
                        {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'N/A'}
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20">
                          {log.action}
                        </span>
                      </td>
                      <td className="p-4 text-slate-300 font-mono text-[11px]">
                        {log.target_resource_type || 'SYSTEM'}
                      </td>
                      <td className="p-4">
                        <StatusBadge status={log.status} />
                      </td>
                      <td className="p-4 font-mono text-[10px] text-slate-400 max-w-[120px] truncate" title={log.prev_record_hash}>
                        {log.prev_record_hash ? log.prev_record_hash.substring(0, 14) + '...' : '0000000000...'}
                      </td>
                      <td className="p-4 font-mono text-[10px] text-emerald-400 max-w-[120px] truncate" title={log.current_record_hash}>
                        {log.current_record_hash ? log.current_record_hash.substring(0, 14) + '...' : 'PENDING'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
