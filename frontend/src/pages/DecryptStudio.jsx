import React, { useState, useEffect } from 'react';
import { 
  Eye, Unlock, CheckCircle2, AlertTriangle, ShieldCheck, ShieldAlert,
  ArrowRight, Download, RefreshCw, KeyRound, Layers, Cpu, Binary,
  FileCheck2, Database, Upload, FileCode
} from 'lucide-react';
import { imageService } from '../services/imageService';
import { cryptoService } from '../services/cryptoService';
import StatusBadge from '../components/StatusBadge';

export default function DecryptStudio() {
  const [mode, setMode] = useState('vault'); // 'vault' or 'file'
  const [images, setImages] = useState([]);
  const [selectedImageId, setSelectedImageId] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  
  // Decryption configuration
  const [masterKey, setMasterKey] = useState('HICE_CLINICAL_MASTER_KEY_2026');
  const [verifyBitExact, setVerifyBitExact] = useState(true);
  const [loading, setLoading] = useState(false);
  const [decryptResult, setDecryptResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  // Auto-load encrypted images from vault
  useEffect(() => {
    loadVaultImages();
  }, []);

  const loadVaultImages = async () => {
    try {
      const data = await imageService.getImages();
      setImages(data);
      if (data.length > 0) {
        setSelectedImageId(data[0].image_id);
      }
    } catch (err) {
      console.error('Failed to load clinician images:', err);
    }
  };

  const handleDecrypt = async () => {
    setLoading(true);
    setErrorMsg('');
    setDecryptResult(null);

    try {
      if (mode === 'vault') {
        if (!selectedImageId) {
          throw new Error('Please select an encrypted scan from the vault.');
        }
        const res = await cryptoService.runHybridDecrypt(
          selectedImageId,
          masterKey,
          verifyBitExact
        );
        setDecryptResult(res);
      } else {
        if (!uploadedFile) {
          throw new Error('Please select or upload an encrypted package from your disk.');
        }
        const res = await cryptoService.directDecryptFile(uploadedFile, masterKey);
        setDecryptResult(res);
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Decryption failed.';
      setErrorMsg(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadDecrypted = () => {
    if (!decryptResult?.data_uri) return;
    const link = document.createElement('a');
    link.href = decryptResult.data_uri;
    const filename = decryptResult.metadata?.original_filename || 'reconstructed_scan.png';
    link.download = `decrypted_${filename}`;
    link.click();
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
              <Eye className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Hybrid Decryption & Bit-Exact Verification Studio
              </h1>
            </div>
          </div>
        </div>

        {/* Source Mode Selector */}
        <div className="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-xl">
          <button
            onClick={() => { setMode('vault'); setDecryptResult(null); setErrorMsg(''); }}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all ${
              mode === 'vault'
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Vault Asset</span>
          </button>
          <button
            onClick={() => { setMode('file'); setDecryptResult(null); setErrorMsg(''); }}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-2 transition-all ${
              mode === 'file'
                ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Package</span>
          </button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Controls Column (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Target Selection Card */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <FileCode className="w-4 h-4 text-emerald-400" />
              <span>1. Target Encrypted Package</span>
            </h3>

            {mode === 'vault' ? (
              <div className="space-y-3">
                <label className="text-xs font-medium text-slate-400">
                  Select Encrypted Medical Scan in Vault
                </label>
                <select
                  value={selectedImageId}
                  onChange={(e) => { setSelectedImageId(e.target.value); setDecryptResult(null); setErrorMsg(''); }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
                >
                  {images.map((img) => (
                    <option key={img.image_id} value={img.image_id}>
                      {img.title} ({img.modality} - {img.width}x{img.height})
                    </option>
                  ))}
                </select>
                {images.length === 0 && (
                  <p className="text-xs text-amber-400">
                    No images found. Ingest or encrypt a sample image first in Upload / Encrypt Studio.
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <label className="text-xs font-medium text-slate-400">
                  Select Binary Container from Disk
                </label>
                <input
                  type="file"
                  accept=".hice,.enc,.bin"
                  onChange={(e) => { setUploadedFile(e.target.files[0] || null); setDecryptResult(null); setErrorMsg(''); }}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-slate-400 file:mr-4 file:py-1 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-emerald-500/10 file:text-emerald-400 hover:file:bg-emerald-500/20"
                />
              </div>
            )}
          </div>

          {/* Key Management & Parameters */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-5">
            <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
              <KeyRound className="w-4 h-4 text-emerald-400" />
              <span>2. Decryption Key & Security Check</span>
            </h3>

            <div className="space-y-3">
              <label className="text-xs font-medium text-slate-400">
                Authorized Master Key / Passphrase
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={masterKey}
                  onChange={(e) => setMasterKey(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-mono text-emerald-400 focus:outline-none focus:border-emerald-500 pr-10"
                  placeholder="Enter 256-bit passphrase or secret..."
                />
                <button
                  type="button"
                  onClick={() => setMasterKey('HICE_CLINICAL_MASTER_KEY_2026')}
                  title="Reset to default key"
                  className="absolute right-3 top-2.5 text-slate-500 hover:text-slate-300 text-xs"
                >
                  Reset
                </button>
              </div>
              <p className="text-[11px] text-slate-500">
                HKDF-SHA256 expands this secret into subkeys: K_aes, K_chaos, and K_ca.
              </p>
            </div>

            <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
              <div className="space-y-0.5">
                <span className="text-xs font-medium text-slate-300">Enforce Bit-Exact Verification</span>
                <p className="text-[11px] text-slate-500">Verify reconstructed pixel SHA-256 against AAD digest</p>
              </div>
              <input
                type="checkbox"
                checked={verifyBitExact}
                onChange={(e) => setVerifyBitExact(e.target.checked)}
                className="w-4 h-4 text-emerald-600 bg-slate-950 border-slate-700 rounded focus:ring-emerald-500"
              />
            </div>

            <button
              onClick={handleDecrypt}
              disabled={loading || (mode === 'vault' && !selectedImageId) || (mode === 'file' && !uploadedFile)}
              className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-sm rounded-xl shadow-lg shadow-emerald-600/30 flex items-center justify-center space-x-2 transition-all"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Authenticating & Inverting Pipeline...</span>
                </>
              ) : (
                <>
                  <Unlock className="w-4 h-4" />
                  <span>Execute Reverse Pipeline</span>
                </>
              )}
            </button>
          </div>

          {/* Reverse Pipeline Flow Indicator */}
          <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-5 space-y-3">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Cryptographic Inversion Order
            </h4>
            <div className="space-y-2 text-xs">
              <div className="flex items-center space-x-2 p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                <span className="w-5 h-5 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center font-mono text-[10px]">1</span>
                <span>Unpack Container & Extract AAD</span>
              </div>
              <div className="flex items-center space-x-2 p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-mono text-[10px]">2</span>
                <span>AES-256-GCM AEAD Decryption & Tag Verification</span>
              </div>
              <div className="flex items-center space-x-2 p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-mono text-[10px]">3</span>
                <span>Cellular Automata Inverse Diffusion (Rule 30/90)</span>
              </div>
              <div className="flex items-center space-x-2 p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-mono text-[10px]">4</span>
                <span>Chaotic Logistic Map Inverse Permutation</span>
              </div>
              <div className="flex items-center space-x-2 p-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300">
                <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-mono text-[10px]">5</span>
                <span>SHA-256 Integrity Match & Bit-Exact Reconstruction</span>
              </div>
            </div>
          </div>
        </div>

        {/* Display & Results Column (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {errorMsg && (
            <div className="p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-2">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0" />
                <h4 className="text-sm font-bold text-white">Cryptographic Decryption Failure</h4>
              </div>
              <p className="text-xs leading-relaxed font-mono">
                {errorMsg}
              </p>
              <p className="text-[11px] text-slate-400 pt-1">
                Zero partial plaintext released. If the key is incorrect or any single bit was modified in the ciphertext or metadata, AES-GCM tags strictly reject the operation.
              </p>
            </div>
          )}

          {decryptResult ? (
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-6">
              {/* Verification Header Badge */}
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <ShieldCheck className="w-7 h-7 text-emerald-400 flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-bold text-white">
                      Bit-Exact Lossless Reconstruction Verified
                    </h4>
                    <p className="text-xs text-emerald-300 font-mono mt-0.5">
                      SHA-256: {decryptResult.reconstructed_sha256?.substring(0, 32)}...
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleDownloadDecrypted}
                  className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-md shadow-emerald-600/30"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Scan</span>
                </button>
              </div>

              {/* Reconstructed Visual Preview */}
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Reconstructed Diagnostic Scan
                </span>
                <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950 flex items-center justify-center p-4">
                  <img
                    src={decryptResult.data_uri}
                    alt="Decrypted Medical Scan"
                    className="max-h-[380px] object-contain rounded-lg shadow-2xl"
                  />
                </div>
              </div>

              {/* Performance Metrics Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">AES-GCM Auth</span>
                  <p className="text-base font-bold text-sky-400 font-mono mt-0.5">
                    {decryptResult.performance?.aes_gcm_ms} ms
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">CA Inverse</span>
                  <p className="text-base font-bold text-emerald-400 font-mono mt-0.5">
                    {decryptResult.performance?.ca_inverse_ms} ms
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">Chaos Inverse</span>
                  <p className="text-base font-bold text-amber-400 font-mono mt-0.5">
                    {decryptResult.performance?.chaos_inverse_ms} ms
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider font-mono">Throughput</span>
                  <p className="text-base font-bold text-purple-400 font-mono mt-0.5">
                    {decryptResult.performance?.throughput_mbps} MB/s
                  </p>
                </div>
              </div>

              {/* Authenticated Clinical Metadata (AAD) */}
              <div className="space-y-3 pt-2 border-t border-slate-800">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-2">
                  <FileCheck2 className="w-4 h-4 text-emerald-400" />
                  <span>Authenticated Associated Clinical Metadata (AAD)</span>
                </span>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                    <span className="text-slate-500 text-[11px]">Patient Pseudonym:</span>
                    <p className="font-mono text-slate-200 font-medium">
                      {decryptResult.metadata?.clinical?.patient_pseudonym || 'PT-ANONYMOUS'}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                    <span className="text-slate-500 text-[11px]">Imaging Modality:</span>
                    <p className="font-mono text-slate-200 font-medium">
                      {decryptResult.metadata?.clinical?.modality || 'GENERAL'}
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                    <span className="text-slate-500 text-[11px]">Dimensions:</span>
                    <p className="font-mono text-slate-200 font-medium">
                      {decryptResult.dimensions?.width} x {decryptResult.dimensions?.height} ({decryptResult.dimensions?.channels}ch)
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1">
                    <span className="text-slate-500 text-[11px]">CA Diffusion Rule:</span>
                    <p className="font-mono text-slate-200 font-medium">
                      Rule {decryptResult.metadata?.ca_rule || 30}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full min-h-[460px] rounded-2xl bg-slate-900/40 border border-slate-800/80 border-dashed flex flex-col items-center justify-center p-8 text-center space-y-3">
              <div className="p-3 rounded-2xl bg-slate-800/50 text-slate-500">
                <Eye className="w-8 h-8" />
              </div>
              <h4 className="text-sm font-semibold text-slate-300">
                Awaiting Decryption Command
              </h4>
              <p className="text-xs text-slate-500 max-w-sm">
                Select an encrypted scan from the vault or upload a package and click "Execute Reverse Pipeline" to recover the lossless scan.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
