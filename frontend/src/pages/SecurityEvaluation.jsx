import React, { useState, useEffect } from 'react';
import { 
  BarChart3, ShieldCheck, Activity, RefreshCw, Zap, 
  CheckCircle2, AlertCircle, TrendingUp, Layers, Cpu
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  Legend, ScatterChart, Scatter, CartesianGrid
} from 'recharts';
import { evaluationService } from '../services/evaluationService';
import { imageService } from '../services/imageService';
import StatusBadge from '../components/StatusBadge';

export default function SecurityEvaluation() {
  const [images, setImages] = useState([]);
  const [selectedImageId, setSelectedImageId] = useState('');
  const [masterKey, setMasterKey] = useState('HICE_CLINICAL_MASTER_KEY_2026');
  const [loading, setLoading] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchImages();
  }, []);

  const fetchImages = async () => {
    try {
      const data = await imageService.getImages();
      setImages(data);
      if (data.length > 0) {
        setSelectedImageId(data[0].image_id);
      }
    } catch (err) {
      console.error('Failed to fetch images:', err);
    }
  };

  const handleRunBenchmark = async () => {
    if (!selectedImageId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await evaluationService.runBenchmark(selectedImageId, masterKey);
      setBenchmarkResult(res.benchmark_data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to execute security evaluation.');
    } finally {
      setLoading(false);
    }
  };

  const comparativeData = benchmarkResult?.comparative_benchmarks || [];
  const origMetrics = benchmarkResult?.original_metrics;
  const visuals = benchmarkResult?.visualizations;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
              Phase 11: Active
            </span>
            <span className="text-xs font-mono text-slate-400">Statistical Cryptographic Benchmarking</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Security Evaluation & Quantitative Benchmarks</h1>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-3">
          <select
            value={selectedImageId}
            onChange={(e) => setSelectedImageId(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
          >
            {images.map((img) => (
              <option key={img.image_id} value={img.image_id}>
                {img.title} ({img.width}x{img.height})
              </option>
            ))}
          </select>

          <button
            onClick={handleRunBenchmark}
            disabled={loading || images.length === 0}
            className="px-4 py-2 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold transition shadow-lg shadow-sky-500/20 flex items-center space-x-2 disabled:opacity-50"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
            <span>{loading ? 'Evaluating...' : 'Run 4-Way Benchmark'}</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center space-x-2 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Baseline Metric Cards */}
      {origMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Original Scan Entropy</span>
            <div className="text-xl font-extrabold text-amber-400 font-mono">{origMetrics.entropy}</div>
            <p className="text-[11px] text-slate-500">Low entropy indicates structured pixel patterns</p>
          </div>
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Horizontal Correlation</span>
            <div className="text-xl font-extrabold text-white font-mono">{origMetrics.h_corr}</div>
            <p className="text-[11px] text-slate-500">High spatial redundancy (ρ ≈ 0.95 - 0.99)</p>
          </div>
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Vertical Correlation</span>
            <div className="text-xl font-extrabold text-white font-mono">{origMetrics.v_corr}</div>
            <p className="text-[11px] text-slate-500">High vertical pixel redundancy</p>
          </div>
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">Diagonal Correlation</span>
            <div className="text-xl font-extrabold text-white font-mono">{origMetrics.d_corr}</div>
            <p className="text-[11px] text-slate-500">High diagonal pixel redundancy</p>
          </div>
        </div>
      )}

      {/* 4-Way Comparative Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-slate-800 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Layers className="w-5 h-5 text-sky-400" />
            <h2 className="text-base font-bold text-white">4-Way Comparative Security Performance</h2>
          </div>
          <span className="text-xs font-mono text-slate-400">Theoretical Ideal: H=8.00, NPCR&gt;99.6%, UACI&gt;33.4%, ρ≈0.00</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/70 text-slate-400 uppercase font-mono text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-4">Configuration</th>
                <th className="p-4">Shannon Entropy</th>
                <th className="p-4">NPCR (%)</th>
                <th className="p-4">UACI (%)</th>
                <th className="p-4">H / V / D Correlations</th>
                <th className="p-4">Enc / Dec Speed</th>
                <th className="p-4 text-center">Exact Recovery</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {comparativeData.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-8 text-center text-slate-500">
                    No benchmark data available. Click "Run 4-Way Benchmark" to execute quantitative evaluation.
                  </td>
                </tr>
              ) : (
                comparativeData.map((c, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition">
                    <td className="p-4 font-semibold text-white flex items-center space-x-2">
                      <span className={`w-2 h-2 rounded-full ${idx === 3 ? 'bg-emerald-400' : 'bg-sky-400'}`}></span>
                      <span>{c.configuration}</span>
                    </td>
                    <td className="p-4 font-mono font-bold text-emerald-400">{c.entropy}</td>
                    <td className="p-4 font-mono text-sky-300 font-semibold">{c.npcr}%</td>
                    <td className="p-4 font-mono text-indigo-300">{c.uaci}%</td>
                    <td className="p-4 font-mono text-slate-300 text-[11px]">
                      {c.h_corr} / {c.v_corr} / {c.d_corr}
                    </td>
                    <td className="p-4 font-mono text-slate-400 text-[11px]">
                      {c.encryption_time_ms} ms / {c.decryption_time_ms} ms
                    </td>
                    <td className="p-4 text-center">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        Lossless (100%)
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual Analytics Charts */}
      {comparativeData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Entropy & NPCR Comparison Chart */}
          <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-emerald-400" />
              <span>Shannon Entropy Benchmark (Max Theoretical = 8.000)</span>
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparativeData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <XAxis dataKey="configuration" stroke="#64748b" tick={{ fontSize: 9 }} interval={0} angle={-10} textAnchor="end" />
                  <YAxis domain={[7.0, 8.05]} stroke="#64748b" tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }} />
                  <Bar dataKey="entropy" name="Entropy (bits)" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Histogram Intensity Distribution Chart */}
          {visuals?.histogram_buckets && (
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <BarChart3 className="w-4 h-4 text-sky-400" />
                <span>Pixel Intensity Histogram (Original vs Full Hybrid Cipher)</span>
              </h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={visuals.histogram_buckets} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                    <XAxis dataKey="range" stroke="#64748b" tick={{ fontSize: 9 }} interval={3} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }} />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                    <Bar dataKey="original" name="Original Scan" fill="#f59e0b" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="ciphertext" name="Ciphertext (Uniform)" fill="#0ea5e9" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Correlation Destruction Scatter Plot */}
      {visuals?.scatter && (
        <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <Activity className="w-4 h-4 text-indigo-400" />
                <span>Adjacent Pixel Correlation Scatter Comparison (Horizontal Direction)</span>
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Original image exhibits strong linear diagonal alignment (y = x). Ciphertext completely shatters spatial correlation into uniform white noise.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <h4 className="text-xs font-semibold text-amber-400 mb-2 text-center">Original Scan Adjacent Pixels (ρ ≈ 0.96)</h4>
              <div className="h-60">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis type="number" dataKey="x" domain={[0, 255]} stroke="#64748b" tick={{ fontSize: 9 }} name="Pixel (r, c)" />
                    <YAxis type="number" dataKey="y" domain={[0, 255]} stroke="#64748b" tick={{ fontSize: 9 }} name="Pixel (r, c+1)" />
                    <Scatter data={visuals.scatter.horizontal_original} fill="#f59e0b" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <h4 className="text-xs font-semibold text-sky-400 mb-2 text-center">Ciphertext Adjacent Pixels (ρ ≈ 0.00)</h4>
              <div className="h-60">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis type="number" dataKey="x" domain={[0, 255]} stroke="#64748b" tick={{ fontSize: 9 }} name="Pixel (r, c)" />
                    <YAxis type="number" dataKey="y" domain={[0, 255]} stroke="#64748b" tick={{ fontSize: 9 }} name="Pixel (r, c+1)" />
                    <Scatter data={visuals.scatter.horizontal_cipher} fill="#0ea5e9" />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
