import React, { useState, useEffect } from 'react';
import { 
  Database, ShieldCheck, ShieldAlert, AlertTriangle, RefreshCw, 
  CheckCircle2, ArrowRight, ShieldX, Link as LinkIcon, Key, Clock,
  FileCheck2, Search, Wrench, Bug
} from 'lucide-react';
import api from '../services/api';
import StatusBadge from '../components/StatusBadge';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [filterAction, setFilterAction] = useState('ALL');

  useEffect(() => {
    fetchLogs();
    verifyChain();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/audit/logs');
      setLogs(res.data);
      if (res.data.length > 0) {
        setSelectedBlock(res.data[res.data.length - 1]);
      }
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const verifyChain = async () => {
    setVerifying(true);
    try {
      const res = await api.get('/audit/verify-chain');
      setVerification(res.data);
    } catch (err) {
      console.error('Failed to verify audit hash chain:', err);
    } finally {
      setVerifying(false);
    }
  };

  const handleSimulateTamper = async () => {
    setActionLoading(true);
    try {
      await api.post('/audit/simulate-tamper');
      await fetchLogs();
      await verifyChain();
    } catch (err) {
      console.error('Failed to simulate tamper:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRepairChain = async () => {
    setActionLoading(true);
    try {
      await api.post('/audit/repair-chain');
      await fetchLogs();
      await verifyChain();
    } catch (err) {
      console.error('Failed to repair chain:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const filteredLogs = filterAction === 'ALL' 
    ? logs 
    : logs.filter(l => l.action.toLowerCase().includes(filterAction.toLowerCase()));

  const isIntact = verification?.chain_intact;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Cryptographic Hash-Chained Audit Ledger
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Phase 9 Tamper-Evident Security Log: Hash(n) = SHA256(Hash(n-1) || LogID || Action || Status || Timestamp)
              </p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <button
            onClick={verifyChain}
            disabled={verifying}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold rounded-xl flex items-center space-x-2 transition-all shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${verifying ? 'animate-spin' : ''}`} />
            <span>Verify Chain</span>
          </button>

          <button
            onClick={handleSimulateTamper}
            disabled={actionLoading}
            className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 text-rose-300 text-xs font-semibold rounded-xl flex items-center space-x-2 transition-all"
            title="Inject simulated bit modification into database row"
          >
            <Bug className="w-3.5 h-3.5 text-rose-400" />
            <span>Simulate Tamper</span>
          </button>

          <button
            onClick={handleRepairChain}
            disabled={actionLoading}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl flex items-center space-x-2 transition-all shadow-lg shadow-emerald-600/30"
          >
            <Wrench className="w-3.5 h-3.5" />
            <span>Repair Ledger</span>
          </button>
        </div>
      </div>

      {/* Verification Shield Banner */}
      <div className={`p-6 rounded-2xl border transition-all ${
        isIntact
          ? 'bg-emerald-950/20 border-emerald-500/40'
          : 'bg-rose-950/30 border-rose-500/50 shadow-2xl shadow-rose-900/20'
      }`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start md:items-center space-x-4">
            <div className={`p-3.5 rounded-2xl ${
              isIntact
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse'
            }`}>
              {isIntact ? <ShieldCheck className="w-8 h-8" /> : <ShieldAlert className="w-8 h-8" />}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-lg font-bold text-white">
                  {isIntact ? 'Cryptographic Hash-Chain Verified & Intact' : 'CRITICAL ALERT: Tampering Detected in Audit Chain!'}
                </h3>
                <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full font-bold ${
                  isIntact ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/30 text-rose-300'
                }`}>
                  {verification?.status || 'VALIDATING'}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {isIntact 
                  ? `All ${verification?.total_verified || logs.length} consecutive audit blocks verified with continuous SHA-256 parent linkage.`
                  : `Chain integrity failure! One or more historical database records have been modified without valid hash re-anchoring.`}
              </p>
            </div>
          </div>

          <div className="text-right font-mono text-xs space-y-1">
            <div className="text-slate-400 text-[11px]">
              Latest Block Hash: <span className="text-slate-200">{verification?.latest_block_hash?.substring(0, 16)}...</span>
            </div>
            <div className="text-slate-500 text-[10px]">
              Genesis: 0000000000000000...
            </div>
          </div>
        </div>

        {/* Tamper Warning Detail */}
        {!isIntact && verification?.tampered_records?.length > 0 && (
          <div className="mt-4 pt-4 border-t border-rose-500/30 space-y-2">
            <span className="text-xs font-bold text-rose-300 uppercase tracking-wider flex items-center space-x-1.5">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Identified Corrupted Blocks:</span>
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-mono">
              {verification.tampered_records.map((t, idx) => (
                <div key={idx} className="p-2.5 rounded-lg bg-rose-950/60 border border-rose-500/30 text-rose-200">
                  <p className="font-bold">Record #{t.log_id}: {t.reason}</p>
                  <p className="text-[10px] text-rose-400 truncate mt-1">Expected Prev: {t.expected_prev}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Block Explorer Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Chain Block Timeline (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <LinkIcon className="w-4 h-4 text-purple-400" />
              <span>Chained Audit Blocks ({filteredLogs.length})</span>
            </h3>

            {/* Filter */}
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-300 focus:outline-none"
            >
              <option value="ALL">All Events</option>
              <option value="ENCRYPT">Encryption</option>
              <option value="DECRYPT">Decryption</option>
              <option value="SHARE">Sharing</option>
              <option value="INGESTION">Ingestion</option>
            </select>
          </div>

          <div className="space-y-3 max-h-[620px] overflow-y-auto pr-2">
            {filteredLogs.map((log, index) => {
              const isSelected = selectedBlock?.log_id === log.log_id;
              const isTampered = verification?.tampered_records?.some(t => t.log_id === log.log_id);

              return (
                <div
                  key={log.log_id}
                  onClick={() => setSelectedBlock(log)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer relative ${
                    isSelected
                      ? 'bg-slate-850 border-purple-500 shadow-md shadow-purple-500/10'
                      : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                  } ${isTampered ? 'border-rose-500 bg-rose-950/20' : ''}`}
                >
                  <div className="flex items-center justify-between text-xs font-mono">
                    <div className="flex items-center space-x-2">
                      <span className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-300 font-bold flex items-center justify-center text-[10px]">
                        #{log.log_id}
                      </span>
                      <span className="font-bold text-white">{log.action}</span>
                    </div>
                    <span className="text-[11px] text-slate-400">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="mt-2 text-xs text-slate-400 flex items-center justify-between">
                    <span>Actor: <strong className="text-slate-200">{log.username}</strong></span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                      log.status === 'SUCCESS' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                    }`}>
                      {log.status}
                    </span>
                  </div>

                  {/* Hash summary pill */}
                  <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
                    <span className="truncate max-w-[200px]">Prev: {log.prev_record_hash?.substring(0, 16)}...</span>
                    <span className="truncate max-w-[200px] text-purple-400">Curr: {log.current_record_hash?.substring(0, 16)}...</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: Selected Block Deep Inspector (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <FileCheck2 className="w-4 h-4 text-purple-400" />
              <span>Cryptographic Block Inspector</span>
            </h3>

            {selectedBlock ? (
              <div className="space-y-4 font-mono text-xs">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-slate-500 text-[10px] uppercase">Record Identifier:</span>
                  <p className="text-white font-bold text-sm">Block #{selectedBlock.log_id} ({selectedBlock.action})</p>
                </div>

                <div className="space-y-2">
                  <span className="text-slate-500 text-[10px] uppercase block">Parent Link Hash (prev_record_hash):</span>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 break-all text-[11px]">
                    {selectedBlock.prev_record_hash}
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-slate-500 text-[10px] uppercase block">Block Hash (current_record_hash):</span>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-purple-500/40 text-purple-300 break-all text-[11px] font-bold">
                    {selectedBlock.current_record_hash}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 text-[10px] block">Actor ID:</span>
                    <span className="text-slate-200 truncate block">{selectedBlock.user_id || 'System'}</span>
                  </div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">
                    <span className="text-slate-500 text-[10px] block">IP Address:</span>
                    <span className="text-slate-200 truncate block">{selectedBlock.ip_address}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <span className="text-slate-500 text-[10px] uppercase block">Block Event Payload (JSON):</span>
                  <pre className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 overflow-x-auto max-h-48 leading-relaxed">
                    {JSON.stringify(selectedBlock.details || {}, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center py-12">
                Click any block on the left to inspect its cryptographic linkages.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
