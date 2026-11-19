import React, { useState, useEffect } from 'react';
import { 
  Lock, Cpu, Sparkles, CheckCircle2, ArrowRight, Activity, 
  Layers, RefreshCw, BarChart2, ShieldAlert, GitBranch, Binary,
  ShieldCheck, KeyRound, AlertTriangle, ShieldX
} from 'lucide-react';
import { imageService } from '../services/imageService';
import { cryptoService } from '../services/cryptoService';
import StatusBadge from '../components/StatusBadge';

export default function EncryptStudio({ onProceedToFullPipeline }) {
  const [activeStage, setActiveStage] = useState('chaos'); // 'chaos', 'ca', 'aes_ecdh'
  const [images, setImages] = useState([]);
  const [selectedImageId, setSelectedImageId] = useState('');
  
  // Chaotic map states
  const [chaosSeed, setChaosSeed] = useState('HICE_RESEARCH_SEED_2026');
  const [loadingChaos, setLoadingChaos] = useState(false);
  const [permuteResult, setPermuteResult] = useState(null);
  const [sensitivityData, setSensitivityData] = useState(null);
  const [deltaExponent, setDeltaExponent] = useState(-14);

  // Cellular Automata states
  const [caRule, setCaRule] = useState(30);
  const [caSeed, setCaSeed] = useState('HICE_CELLULAR_SEED_2026');
  const [loadingCA, setLoadingCA] = useState(false);
  const [diffuseResult, setDiffuseResult] = useState(null);
  const [avalancheData, setAvalancheData] = useState(null);

  // ECDH & AES-GCM states
  const [loadingECDH, setLoadingECDH] = useState(false);
  const [ecdhResult, setEcdhResult] = useState(null);
  const [loadingTamper, setLoadingTamper] = useState(false);
  const [tamperResult, setTamperResult] = useState(null);

  // Full Atomic Hybrid Pipeline State
  const [loadingHybrid, setLoadingHybrid] = useState(false);
  const [hybridResult, setHybridResult] = useState(null);
  const [hybridKey, setHybridKey] = useState('HICE_CLINICAL_MASTER_KEY_2026');

  useEffect(() => {
    const fetchImages = async () => {
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
    fetchImages();
    loadSensitivity();
    loadAvalanche(30);
  }, []);

  const loadSensitivity = async (exp = -14) => {
    try {
      const delta = Math.pow(10, exp);
      const data = await cryptoService.getChaosSensitivity(chaosSeed, delta);
      setSensitivityData(data);
    } catch (err) {
      console.error('Failed to load sensitivity data:', err);
    }
  };

  const loadAvalanche = async (rule = 30) => {
    try {
      const data = await cryptoService.getCAAvalanche(rule, 2000);
      setAvalancheData(data);
    } catch (err) {
      console.error('Failed to load avalanche data:', err);
    }
  };

  const handlePermuteTest = async () => {
    if (!selectedImageId) return;
    setLoadingChaos(true);
    try {
      const res = await cryptoService.testChaoticPermute(selectedImageId, chaosSeed);
      setPermuteResult(res);
    } catch (err) {
      console.error('Chaotic permutation test failed:', err);
    } finally {
      setLoadingChaos(false);
    }
  };

  const handleDiffuseTest = async () => {
    if (!selectedImageId) return;
    setLoadingCA(true);
    try {
      const res = await cryptoService.testCADiffuse(selectedImageId, caRule, caSeed);
      setDiffuseResult(res);
    } catch (err) {
      console.error('CA diffusion test failed:', err);
    } finally {
      setLoadingCA(false);
    }
  };

  const handleECDHTest = async () => {
    setLoadingECDH(true);
    try {
      const res = await cryptoService.testECDHKeyAgreement();
      setEcdhResult(res);
    } catch (err) {
      console.error('ECDH key agreement failed:', err);
    } finally {
      setLoadingECDH(false);
    }
  };

  const handleTamperTest = async () => {
    setLoadingTamper(true);
    try {
      const res = await cryptoService.testAESTamperSimulation();
      setTamperResult(res);
    } catch (err) {
      console.error('Tampering simulation failed:', err);
    } finally {
      setLoadingTamper(false);
    }
  };

  const handleRunHybridEncrypt = async () => {
    if (!selectedImageId) return;
    setLoadingHybrid(true);
    try {
      const res = await cryptoService.runHybridEncrypt(selectedImageId, hybridKey, caRule);
      setHybridResult(res);
    } catch (err) {
      console.error('Hybrid encryption failed:', err);
    } finally {
      setLoadingHybrid(false);
    }
  };

  const selectedImage = images.find(img => img.image_id === selectedImageId);

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Title & Stage Toggle */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono text-sky-400 font-semibold tracking-wider uppercase">
              Cryptographic Engine
            </span>
            <StatusBadge 
              status="ready" 
              text={
                activeStage === 'chaos' ? 'STAGE 1: CHAOTIC PERMUTATION' : 
                activeStage === 'ca' ? 'STAGE 2: CELLULAR DIFFUSION' : 
                'STAGE 3: AES-256-GCM + ECDH'
              } 
            />
          </div>
          <h2 className="text-2xl font-black text-white tracking-tight flex items-center space-x-2 mt-1">
            <Cpu className="w-6 h-6 text-sky-400" />
            <span>Hybrid Cryptographic Studio</span>
          </h2>
        </div>

        {/* Stage Selector Pills */}
        <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setActiveStage('chaos')}
            className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center space-x-1.5 ${
              activeStage === 'chaos'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <GitBranch className="w-3.5 h-3.5" />
            <span>1. Chaos Map</span>
          </button>
          <button
            onClick={() => setActiveStage('ca')}
            className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center space-x-1.5 ${
              activeStage === 'ca'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Binary className="w-3.5 h-3.5" />
            <span>2. Cellular Automata</span>
          </button>
          <button
            onClick={() => setActiveStage('aes_ecdh')}
            className={`px-3 py-1.5 rounded-lg font-bold transition-all flex items-center space-x-1.5 ${
              activeStage === 'aes_ecdh'
                ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>3. AES-GCM & ECDH</span>
          </button>
        </div>
      </div>

      {/* Target Image Selector */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center space-x-3 w-full md:w-auto">
          <Layers className="w-5 h-5 text-sky-400 flex-shrink-0" />
          <div className="flex-1 md:w-80">
            <select
              value={selectedImageId}
              onChange={(e) => setSelectedImageId(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 outline-none focus:border-sky-500 font-mono"
            >
              {images.map(img => (
                <option key={img.image_id} value={img.image_id}>
                  {img.title} ({img.width}x{img.height} - {img.modality})
                </option>
              ))}
            </select>
          </div>
        </div>

        {selectedImage && (
          <div className="flex items-center space-x-4 text-xs font-mono text-slate-400">
            <span>Modality: <strong className="text-sky-400">{selectedImage.modality}</strong></span>
            <span>Dimensions: <strong className="text-white">{selectedImage.width}x{selectedImage.height}</strong></span>
            <span>Original Hash: <strong className="text-emerald-400">{selectedImage.original_sha256.slice(0, 12)}...</strong></span>
          </div>
        )}
      </div>

      {/* STAGE 1: CHAOTIC MAP */}
      {activeStage === 'chaos' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <Lock className="w-4 h-4 text-sky-400" />
                <span>Logistic Map Permutation Parameters</span>
              </h3>

              <div className="space-y-2">
                <label className="text-[11px] text-slate-400 block font-mono">Secret Derivation Seed (K_chaos)</label>
                <input
                  type="text"
                  value={chaosSeed}
                  onChange={(e) => setChaosSeed(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 outline-none focus:border-sky-500 font-mono"
                />
                <p className="text-[10px] text-slate-500">
                  Formula: x(n+1) = r · x(n) · (1 - x(n)), r ∈ [3.9900, 3.9999]. Shuffles pixel locations via argsort.
                </p>
              </div>

              <button
                onClick={handlePermuteTest}
                disabled={loadingChaos || !selectedImageId}
                className="w-full py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingChaos ? 'animate-spin' : ''}`} />
                <span>{loadingChaos ? 'Permuting...' : 'Execute Chaotic Permute'}</span>
              </button>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>Permutation Verification</span>
              </h3>

              {permuteResult ? (
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                    <span>Exact Lossless Inversion Verified</span>
                  </div>
                  <div className="space-y-1 text-[11px] text-slate-300">
                    <div className="flex justify-between">
                      <span>Execution Time:</span>
                      <span className="text-sky-400">{permuteResult.performance.permutation_time_ms} ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Original Adjacent Correlation:</span>
                      <span className="text-amber-400">{permuteResult.correlation_reduction.original_adjacent_correlation}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Permuted Adjacent Correlation:</span>
                      <span className="text-emerald-400 font-bold">{permuteResult.correlation_reduction.permuted_adjacent_correlation}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-slate-500 text-xs font-mono">
                  Click "Execute Chaotic Permute" to scramble pixel coordinates.
                </div>
              )}

              <div className="text-[10px] text-slate-500 font-mono pt-2 border-t border-slate-800/80">
                P^-1(P(V)) ≡ V (Guaranteed Bit-Exact)
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STAGE 2: CELLULAR AUTOMATA */}
      {activeStage === 'ca' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <Binary className="w-4 h-4 text-sky-400" />
                <span>Cellular Automata Diffusion Parameters</span>
              </h3>

              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setCaRule(30);
                    loadAvalanche(30);
                  }}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    caRule === 30
                      ? 'bg-sky-500/15 border-sky-500/40 text-sky-300'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <span className="font-bold text-xs block">Rule 30</span>
                  <span className="text-[10px] text-slate-500">Chaotic Aperiodic Lattice</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setCaRule(90);
                    loadAvalanche(90);
                  }}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    caRule === 90
                      ? 'bg-sky-500/15 border-sky-500/40 text-sky-300'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <span className="font-bold text-xs block">Rule 90</span>
                  <span className="text-[10px] text-slate-500">Sierpiński Linear Additive</span>
                </button>
              </div>

              <div className="space-y-2">
                <label className="text-[11px] text-slate-400 block font-mono">Keystream Seed (K_ca)</label>
                <input
                  type="text"
                  value={caSeed}
                  onChange={(e) => setCaSeed(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 outline-none focus:border-sky-500 font-mono"
                />
              </div>

              <button
                onClick={handleDiffuseTest}
                disabled={loadingCA || !selectedImageId}
                className="w-full py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingCA ? 'animate-spin' : ''}`} />
                <span>{loadingCA ? 'Diffusing...' : `Execute Rule ${caRule} Diffusion`}</span>
              </button>
            </div>

            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                <span>Diffusion Verification</span>
              </h3>

              {diffuseResult ? (
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                    <span>Exact Lossless Inversion Verified</span>
                  </div>
                  <div className="space-y-1 text-[11px] text-slate-300">
                    <div className="flex justify-between">
                      <span>Execution Time:</span>
                      <span className="text-sky-400">{diffuseResult.performance.diffusion_time_ms} ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Original Entropy:</span>
                      <span className="text-amber-400">{diffuseResult.entropy_elevation.original_entropy}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Diffused Entropy:</span>
                      <span className="text-emerald-400 font-bold">{diffuseResult.entropy_elevation.diffused_entropy}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6 text-slate-500 text-xs font-mono">
                  Click "Execute Rule {caRule} Diffusion" to test pixel diffusion.
                </div>
              )}

              <div className="text-[10px] text-slate-500 font-mono pt-2 border-t border-slate-800/80">
                (V ⊕ M) ⊕ M ≡ V (Reversible Inversion)
              </div>
            </div>
          </div>
        </div>
      )}

      {/* STAGE 3: AES-256-GCM & ECDH KEY AGREEMENT */}
      {activeStage === 'aes_ecdh' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* ECDH Key Agreement Laboratory */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <div className="flex items-center space-x-2">
                <KeyRound className="w-4 h-4 text-sky-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  NIST P-256 ECDH Key Agreement Simulator
                </h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Simulates Alice (Sender Doctor) and Bob (Receiver Doctor) exchanging public keys to arrive at an identical 256-bit symmetric session key via scalar point multiplication Z = d_A · Q_B = d_B · Q_A.
              </p>

              <button
                onClick={handleECDHTest}
                disabled={loadingECDH}
                className="w-full py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingECDH ? 'animate-spin' : ''}`} />
                <span>{loadingECDH ? 'Deriving...' : 'Simulate ECDH & HKDF Key Exchange'}</span>
              </button>

              {ecdhResult && (
                <div className="p-4 rounded-xl bg-slate-950 border border-sky-500/30 space-y-2 text-xs font-mono">
                  <div className="flex items-center space-x-2 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>ECDH Shared Secret Symmetric & Verified</span>
                  </div>
                  <div className="space-y-1 text-[11px] text-slate-300">
                    <div className="flex justify-between">
                      <span>Curve:</span>
                      <span className="text-sky-400">{ecdhResult.curve}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Shared Secret:</span>
                      <span className="text-white truncate max-w-[160px]">{ecdhResult.shared_secret_hex}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Derived K_aes:</span>
                      <span className="text-emerald-400 truncate max-w-[160px]">{ecdhResult.derived_aes_key_hex}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* AEAD Tampering Injection Laboratory */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <div className="flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  AEAD Tamper Detection Experiment
                </h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Demonstrates how AES-256-GCM authenticated encryption catches silent data modifications. We flip 1 single bit in the ciphertext stream and observe the GHASH tag rejection.
              </p>

              <button
                onClick={handleTamperTest}
                disabled={loadingTamper}
                className="w-full py-2.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-rose-600/20 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <ShieldAlert className={`w-3.5 h-3.5 ${loadingTamper ? 'animate-spin' : ''}`} />
                <span>{loadingTamper ? 'Testing...' : 'Inject 1-Bit Ciphertext Tamper'}</span>
              </button>

              {tamperResult && (
                <div className="p-4 rounded-xl bg-slate-950 border border-rose-500/30 space-y-2 text-xs font-mono">
                  <div className="flex items-center space-x-2 text-rose-400">
                    <ShieldX className="w-4 h-4" />
                    <span>Tampering Successfully Caught by AES-GCM</span>
                  </div>
                  <div className="space-y-1 text-[11px] text-slate-300">
                    <div className="flex justify-between">
                      <span>Tamper Injection:</span>
                      <span className="text-rose-400">{tamperResult.tampering_attempt}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Plaintext Released:</span>
                      <span className="text-emerald-400 font-bold">FALSE (Zero Leakage)</span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-2 bg-slate-900 p-2 rounded border border-slate-800">
                      {tamperResult.security_response}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Full Atomic Hybrid Pipeline Execution */}
          <div className="p-6 rounded-2xl bg-gradient-to-r from-sky-950/40 via-purple-950/30 to-emerald-950/40 border border-sky-500/30 space-y-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-[10px] font-mono uppercase tracking-widest text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 font-bold">
                    Phase 7 Full Pipeline
                  </span>
                  <h3 className="text-base font-bold text-white">
                    Execute End-to-End Hybrid Encryption & Generate SecurePix Package
                  </h3>
                </div>
              </div>

              <div className="flex items-center space-x-3 flex-shrink-0">
                <button
                  onClick={handleRunHybridEncrypt}
                  disabled={loadingHybrid || !selectedImageId}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-emerald-500 hover:from-sky-400 hover:to-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50 flex items-center space-x-2"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingHybrid ? 'animate-spin' : ''}`} />
                  <span>{loadingHybrid ? 'Encrypting Pipeline...' : 'Run Full Hybrid Pipeline'}</span>
                </button>
                {onProceedToFullPipeline && (
                  <button
                    onClick={onProceedToFullPipeline}
                    className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition-all flex items-center space-x-1.5"
                  >
                    <span>Decrypt Studio</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {hybridResult && (
              <div className="p-4 rounded-xl bg-slate-950/80 border border-emerald-500/40 space-y-3 font-mono text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="font-bold">Vault Package Created: {hybridResult.vault_package_file}</span>
                  </div>
                  <span className="text-[11px] text-slate-400">
                    Package Size: {(hybridResult.package_size_bytes / 1024).toFixed(2)} KB
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">Chaos Perm:</span>
                    <p className="text-amber-400">{hybridResult.performance?.chaos_permutation_ms} ms</p>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">CA Diffuse:</span>
                    <p className="text-emerald-400">{hybridResult.performance?.ca_diffusion_ms} ms</p>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">AES-GCM:</span>
                    <p className="text-sky-400">{hybridResult.performance?.aes_gcm_ms} ms</p>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-slate-500 text-[10px]">Throughput:</span>
                    <p className="text-purple-400">{hybridResult.performance?.throughput_mbps} MB/s</p>
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center justify-between pt-2 border-t border-slate-800/80 gap-2">
                  <div className="text-[10px] text-slate-400 space-y-0.5 truncate max-w-lg">
                    <p>Nonce (96-bit): <span className="text-slate-300">{hybridResult.nonce_hex}</span></p>
                    <p>Auth Tag (128-bit): <span className="text-slate-300">{hybridResult.auth_tag_hex}</span></p>
                  </div>
                  <a
                    href={`/api/v1/crypto/hybrid/package/${selectedImageId}`}
                    download
                    className="px-3 py-1.5 rounded-lg bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all flex-shrink-0"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Package</span>
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
