import React, { useState, useEffect } from 'react';
import { 
  Share2, ShieldCheck, Clock, Download, Eye, Unlock, 
  AlertCircle, CheckCircle2, UserCheck, KeyRound, Ban, RefreshCw
} from 'lucide-react';
import { shareService } from '../services/shareService';
import { imageService } from '../services/imageService';
import StatusBadge from '../components/StatusBadge';

export default function SharingStudio() {
  const [activeTab, setActiveTab] = useState('share'); // 'share', 'sent', 'received'
  const [images, setImages] = useState([]);
  const [clinicians, setClinicians] = useState([]);
  const [sentShares, setSentShares] = useState([]);
  const [receivedShares, setReceivedShares] = useState([]);

  // Form states
  const [selectedImageId, setSelectedImageId] = useState('');
  const [selectedClinician, setSelectedClinician] = useState('');
  const [permissionType, setPermissionType] = useState('VIEW');
  const [expiryHours, setExpiryHours] = useState(24);
  const [masterKey, setMasterKey] = useState('HICE_CLINICAL_MASTER_KEY_2026');
  const [loadingShare, setLoadingShare] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(null);
  const [shareError, setShareError] = useState(null);

  // Decapsulated view states
  const [activeDecapsulate, setActiveDecapsulate] = useState(null);
  const [loadingAccess, setLoadingAccess] = useState(false);
  const [accessError, setAccessError] = useState(null);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      const [imgs, docs, sent, recv] = await Promise.all([
        imageService.getImages(),
        shareService.listClinicians(),
        shareService.listSentShares(),
        shareService.listReceivedShares()
      ]);
      setImages(imgs);
      if (imgs.length > 0) setSelectedImageId(imgs[0].image_id);
      setClinicians(docs);
      if (docs.length > 0) setSelectedClinician(docs[0].username);
      setSentShares(sent);
      setReceivedShares(recv);
    } catch (err) {
      console.error('Failed to load sharing studio data:', err);
    }
  };

  const handleCreateShare = async (e) => {
    e.preventDefault();
    setLoadingShare(true);
    setShareSuccess(null);
    setShareError(null);

    try {
      const formData = new FormData();
      formData.append('image_id', selectedImageId);
      formData.append('receiver_username', selectedClinician);
      formData.append('permission_type', permissionType);
      formData.append('expiry_hours', expiryHours);
      formData.append('master_key', masterKey);

      const res = await shareService.createShare(formData);
      setShareSuccess(res);
      // Refresh sent list
      const updatedSent = await shareService.listSentShares();
      setSentShares(updatedSent);
    } catch (err) {
      setShareError(err.response?.data?.detail || 'Failed to create secure share.');
    } finally {
      setLoadingShare(false);
    }
  };

  const handleRevoke = async (shareId) => {
    try {
      await shareService.revokeShare(shareId);
      const updatedSent = await shareService.listSentShares();
      setSentShares(updatedSent);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to revoke share.');
    }
  };

  const handleAccessScan = async (shareId) => {
    setLoadingAccess(true);
    setAccessError(null);
    setActiveDecapsulate(null);

    try {
      const res = await shareService.accessSharedScan(shareId);
      setActiveDecapsulate(res);
    } catch (err) {
      setAccessError(err.response?.data?.detail || 'Decapsulation and access failed.');
    } finally {
      setLoadingAccess(false);
    }
  };

  const handleDownload = async (shareId, title) => {
    try {
      const blob = await shareService.downloadSharedScan(shareId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `decrypted_${title || 'scan'}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.response?.data?.detail || 'Download failed or permission denied.');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Phase 8: Active
            </span>
            <span className="text-xs font-mono text-slate-400">NIST P-256 ECDH Key Encapsulation</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Secure Image Sharing & Granular Access Control</h1>
          <p className="text-sm text-slate-400">
            Authorized doctor-to-doctor transfer, asymmetric key encapsulation, time-limited validity, and instant revocation.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1">
          <button
            onClick={() => setActiveTab('share')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition ${
              activeTab === 'share' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Share Scan
          </button>
          <button
            onClick={() => setActiveTab('sent')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 ${
              activeTab === 'sent' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>Sent Transfers</span>
            <span className="px-1.5 py-0.2 bg-slate-800 text-[10px] rounded-full">{sentShares.length}</span>
          </button>
          <button
            onClick={() => setActiveTab('received')}
            className={`px-4 py-2 rounded-lg text-xs font-medium transition flex items-center space-x-1.5 ${
              activeTab === 'received' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>Inbound Scans</span>
            <span className="px-1.5 py-0.2 bg-slate-800 text-[10px] rounded-full">{receivedShares.length}</span>
          </button>
        </div>
      </div>

      {/* Tab 1: Share Scan Form */}
      {activeTab === 'share' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Share2 className="w-5 h-5 text-sky-400" />
              <span>Initiate Cryptographic Image Transfer</span>
            </h2>

            {shareSuccess && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 space-y-2">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                  <span className="font-semibold text-sm">{shareSuccess.message}</span>
                </div>
                <div className="text-xs text-slate-300 font-mono pl-7">
                  Share ID: {shareSuccess.share_id} | Permission: {shareSuccess.permission_type} | Expires: {new Date(shareSuccess.expires_at).toLocaleString()}
                </div>
              </div>
            )}

            {shareError && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center space-x-2 text-sm">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span>{shareError}</span>
              </div>
            )}

            <form onSubmit={handleCreateShare} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Select Medical Scan from Vault
                </label>
                <select
                  value={selectedImageId}
                  onChange={(e) => setSelectedImageId(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                >
                  {images.map((img) => (
                    <option key={img.image_id} value={img.image_id}>
                      {img.title} ({img.width}x{img.height}) - {img.modality || 'SCAN'}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                    Recipient Doctor / Clinician
                  </label>
                  <select
                    value={selectedClinician}
                    onChange={(e) => setSelectedClinician(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  >
                    {clinicians.map((c) => (
                      <option key={c.user_id} value={c.username}>
                        Dr. {c.username} ({c.email})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                    Granular Access Permission
                  </label>
                  <select
                    value={permissionType}
                    onChange={(e) => setPermissionType(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  >
                    <option value="VIEW">VIEW (Lossless Preview in Secure Viewer)</option>
                    <option value="DECRYPT">DECRYPT (Examination & Clinical Analytics)</option>
                    <option value="DOWNLOAD">DOWNLOAD (Full Export of Decrypted Raster File)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                    Validity Window (Hours)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="168"
                    value={expiryHours}
                    onChange={(e) => setExpiryHours(parseInt(e.target.value) || 24)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-sky-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                    Master Encryption Passphrase
                  </label>
                  <input
                    type="password"
                    value={masterKey}
                    onChange={(e) => setMasterKey(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-sky-500 font-mono"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loadingShare || images.length === 0}
                className="w-full py-3 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold rounded-xl transition shadow-lg shadow-sky-500/20 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {loadingShare ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <span>Encapsulating ECDH Session Key...</span>
                  </>
                ) : (
                  <>
                    <KeyRound className="w-5 h-5" />
                    <span>Encapsulate Key & Create Transfer</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Security Architecture Explainer Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>ECDH Protocol Mechanics</span>
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              When sharing, HICE generates an ephemeral NIST P-256 Elliptic Curve key pair $(d_{eph}, Q_{eph})$.
            </p>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-sky-300 space-y-1">
              <div>1. Z = d_eph · Q_recipient</div>
              <div>2. K_wrap = HKDF-SHA256(Z)</div>
              <div>3. Bundle = AES-256-GCM(K_wrap, K_master)</div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Only the recipient doctor possessing $d_{recipient}$ can invert scalar multiplication to decapsulate the master key. Zero plaintext keys are ever exposed in transit or in the database.
            </p>
          </div>
        </div>
      )}

      {/* Tab 2: Sent Transfers */}
      {activeTab === 'sent' && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex justify-between items-center">
            <h2 className="text-lg font-bold text-white">Sent Scan Transfers</h2>
            <button onClick={fetchInitialData} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition">
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
                <tr>
                  <th className="p-4">Scan Title</th>
                  <th className="p-4">Recipient Doctor</th>
                  <th className="p-4">Permission</th>
                  <th className="p-4">Expires At</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {sentShares.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="p-8 text-center text-slate-500">
                      No sent transfers recorded. Initiate a scan transfer from the "Share Scan" tab.
                    </td>
                  </tr>
                ) : (
                  sentShares.map((s) => (
                    <tr key={s.share_id} className="hover:bg-slate-800/30 transition">
                      <td className="p-4 font-semibold text-white">{s.image_title}</td>
                      <td className="p-4 text-slate-300">Dr. {s.receiver_username}</td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                          {s.permission_type}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-slate-400">
                        {s.expires_at ? new Date(s.expires_at).toLocaleString() : 'Never'}
                      </td>
                      <td className="p-4">
                        <StatusBadge status={s.status} />
                      </td>
                      <td className="p-4 text-right">
                        {!s.is_revoked && !s.is_expired && (
                          <button
                            onClick={() => handleRevoke(s.share_id)}
                            className="px-3 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-medium transition inline-flex items-center space-x-1"
                          >
                            <Ban className="w-3.5 h-3.5" />
                            <span>Revoke Access</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Inbound Received Scans */}
      {activeTab === 'received' && (
        <div className="space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center">
              <h2 className="text-lg font-bold text-white">Inbound Medical Scans Shared With You</h2>
              <button onClick={fetchInitialData} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-4">Scan Title</th>
                    <th className="p-4">Sender Doctor</th>
                    <th className="p-4">Modality</th>
                    <th className="p-4">Permission</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {receivedShares.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="p-8 text-center text-slate-500">
                        No inbound scans shared with you yet.
                      </td>
                    </tr>
                  ) : (
                    receivedShares.map((s) => (
                      <tr key={s.share_id} className="hover:bg-slate-800/30 transition">
                        <td className="p-4 font-semibold text-white">{s.image_title}</td>
                        <td className="p-4 text-slate-300">Dr. {s.sender_username}</td>
                        <td className="p-4 text-slate-400 font-mono">{s.modality}</td>
                        <td className="p-4">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {s.permission_type}
                          </span>
                        </td>
                        <td className="p-4">
                          <StatusBadge status={s.status} />
                        </td>
                        <td className="p-4 text-right space-x-2">
                          <button
                            onClick={() => handleAccessScan(s.share_id)}
                            disabled={!s.can_access || loadingAccess}
                            className="px-3 py-1 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition disabled:opacity-40 inline-flex items-center space-x-1"
                          >
                            <Unlock className="w-3.5 h-3.5" />
                            <span>Decapsulate & View</span>
                          </button>
                          {s.permission_type === 'DOWNLOAD' && (
                            <button
                              onClick={() => handleDownload(s.share_id, s.image_title)}
                              disabled={!s.can_access}
                              className="px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition disabled:opacity-40 inline-flex items-center space-x-1"
                            >
                              <Download className="w-3.5 h-3.5" />
                              <span>Download</span>
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Decapsulated View Modal / Card */}
          {activeDecapsulate && (
            <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div className="flex items-center space-x-2 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                  <h3 className="font-bold text-white">Lossless Decapsulation Succeeded</h3>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Bit-Exact Verified: {activeDecapsulate.is_bit_exact ? 'TRUE' : 'FALSE'}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex justify-center items-center bg-slate-950 rounded-xl p-4 border border-slate-800">
                  <img
                    src={activeDecapsulate.data_uri}
                    alt="Decrypted Medical Scan"
                    className="max-h-80 object-contain rounded-lg"
                  />
                </div>

                <div className="space-y-3 text-xs text-slate-300">
                  <div>
                    <span className="text-slate-400 block font-mono text-[10px]">RECONSTRUCTED SHA-256</span>
                    <span className="font-mono text-emerald-400 break-all">{activeDecapsulate.reconstructed_sha256}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-mono text-[10px]">DIMENSIONS</span>
                    <span>{activeDecapsulate.dimensions?.width} x {activeDecapsulate.dimensions?.height} ({activeDecapsulate.dimensions?.channels} Channels)</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-mono text-[10px]">DECAPSULATION SPEED</span>
                    <span>Total Decryption: {activeDecapsulate.performance?.total_decryption_ms} ms</span>
                  </div>

                  {activeDecapsulate.can_download ? (
                    <button
                      onClick={() => handleDownload(activeDecapsulate.share_id, 'medical_scan')}
                      className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl transition flex items-center justify-center space-x-2"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download Decrypted Image File</span>
                    </button>
                  ) : (
                    <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 text-slate-400 flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                      <span>Viewing permission active. Export / download of this scan is restricted by the sending clinician.</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {accessError && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center space-x-2 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{accessError}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
