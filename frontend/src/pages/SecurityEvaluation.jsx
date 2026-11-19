import React, { useState, useEffect } from 'react';
import { 
  BarChart3, Activity, ShieldCheck, Layers, RefreshCw, Cpu, 
  TrendingUp, Award, CheckCircle2, Sliders, LineChart as ChartIcon
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  CartesianGrid, ScatterChart, Scatter, Legend, Cell
} from 'recharts';
import api from '../services/api';
import { imageService } from '../services/imageService';

export default function SecurityEvaluation() {
  const [images, setImages] = useState([]);
  const [selectedImageId, setSelectedImageId] = useState('');
  const [metricsData, setMetricsData] = useState(null);
  const [histogramData, setHistogramData] = useState([]);
  const [scatterData, setScatterData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scatterMode, setScatterMode] = useState('both'); // 'plaintext', 'ciphertext', 'both'

  useEffect(() => {
    loadImages();
  }, []);

  const loadImages = async () => {
    try {
      const data = await imageService.getImages();
      setImages(data);
      if (data.length > 0) {
        setSelectedImageId(data[0].image_id);
        fetchEvaluationData(data[0].image_id);
      }
    } catch (err) {
      console.error('Failed to load images for evaluation:', err);
    }
  };

  const fetchEvaluationData = async (imageId) => {
    if (!imageId) return;
    setLoading(true);
    try {
      const [mRes, hRes, sRes] = await Promise.all([
        api.get(`/evaluation/metrics/${imageId}`),
        api.get(`/evaluation/histograms/${imageId}`),
        api.get(`/evaluation/correlation-pairs/${imageId}?sample_count=200`)
      ]);
      setMetricsData(mRes.data);
      setHistogramData(hRes.data?.histogram || []);
      setScatterData(sRes.data);
    } catch (err) {
      console.error('Failed to fetch security evaluation:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleImageChange = (e) => {
    const id = e.target.value;
    setSelectedImageId(id);
    fetchEvaluationData(id);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <BarChart3 className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Cryptographic Security & Statistical Evaluation Laboratory
              </h1>
              <p className="text-sm text-slate-400 mt-0.5">
                Phase 11 Empirical Verification: Shannon Entropy, NPCR, UACI, Adjacent Pixel Correlation & Histograms
              </p>
            </div>
          </div>
        </div>

        {/* Scan Selector */}
        <div className="flex items-center space-x-3">
          <label className="text-xs font-medium text-slate-400">Target Scan:</label>
          <select
            value={selectedImageId}
            onChange={handleImageChange}
            className="bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-sky-500"
          >
            {images.map(img => (
              <option key={img.image_id} value={img.image_id}>
                {img.title} ({img.modality})
              </option>
            ))}
          </select>
          <button
            onClick={() => fetchEvaluationData(selectedImageId)}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 4-Way Architectural Comparative Matrix */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider flex items-center space-x-2">
            <Award className="w-4 h-4 text-sky-400" />
            <span>4-Way Cryptographic Architectural Comparison</span>
          </h3>
          <span className="text-xs text-slate-500 font-mono">Theoretical Ideal: H=8.0000 | NPCR=99.6094% | UACI=33.4635%</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {metricsData?.comparison?.map((tier, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4 relative overflow-hidden"
            >
              <div 
                className="absolute top-0 left-0 right-0 h-1" 
                style={{ backgroundColor: tier.color }}
              />

              <div className="space-y-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                  {tier.security_tier}
                </span>
                <h4 className="text-sm font-bold text-white">
                  {tier.configuration}
                </h4>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Shannon Entropy:</span>
                  <span className="font-bold" style={{ color: tier.color }}>{tier.entropy.toFixed(4)}</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">NPCR (%):</span>
                  <span className="text-slate-200">{tier.npcr.toFixed(4)}%</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">UACI (%):</span>
                  <span className="text-slate-200">{tier.uaci.toFixed(4)}%</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Adjacent Corr (H):</span>
                  <span className="text-slate-200">{tier.h_corr.toFixed(4)}</span>
                </div>
                <div className="flex justify-between p-2 rounded bg-slate-950 border border-slate-800/80">
                  <span className="text-slate-400">Throughput:</span>
                  <span className="text-slate-200">{tier.throughput_mbps} MB/s</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Visual Analytics Grid: Histograms & Correlation Scatter Plots */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Pixel Intensity Histograms (6 cols) */}
        <div className="lg:col-span-6 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
              <ChartIcon className="w-4 h-4 text-emerald-400" />
              <span>Pixel Intensity Histogram Analysis</span>
            </h3>
            <div className="flex items-center space-x-3 text-[11px] font-mono">
              <span className="flex items-center space-x-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-full bg-slate-500 inline-block" />
                <span>Plaintext Scan</span>
              </span>
              <span className="flex items-center space-x-1.5 text-emerald-400">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" />
                <span>HICE Ciphertext</span>
              </span>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            The plaintext scan displays non-uniform diagnostic peaks (bone/soft-tissue clusters). The HICE ciphertext distribution is completely flat and uniform, preventing frequency analysis attacks.
          </p>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histogramData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="intensity" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#020617', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '11px' }}
                />
                <Bar dataKey="plaintext" fill="#64748b" opacity={0.6} />
                <Bar dataKey="encrypted" fill="#10b981" opacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Adjacent Pixel Correlation Scatter Plots (6 cols) */}
        <div className="lg:col-span-6 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center space-x-2">
              <TrendingUp className="w-4 h-4 text-sky-400" />
              <span>Adjacent Pixel Pair Correlation Scatter</span>
            </h3>

            {/* Toggle Modes */}
            <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-[10px] font-mono">
              <button
                onClick={() => setScatterMode('plaintext')}
                className={`px-2 py-0.5 rounded ${scatterMode === 'plaintext' ? 'bg-slate-700 text-white' : 'text-slate-400'}`}
              >
                Plaintext (r~0.94)
              </button>
              <button
                onClick={() => setScatterMode('ciphertext')}
                className={`px-2 py-0.5 rounded ${scatterMode === 'ciphertext' ? 'bg-sky-600 text-white' : 'text-slate-400'}`}
              >
                Ciphertext (r~0.00)
              </button>
              <button
                onClick={() => setScatterMode('both')}
                className={`px-2 py-0.5 rounded ${scatterMode === 'both' ? 'bg-sky-600 text-white' : 'text-slate-400'}`}
              >
                Both
              </button>
            </div>
          </div>

          <p className="text-xs text-slate-400 leading-relaxed">
            Pairs (x_i, x_i+1) plotted on [0, 255] x [0, 255]. Plaintext pixels cling tightly along the diagonal line y = x. HICE ciphertext is completely dispersed as random white noise.
          </p>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis type="number" dataKey="x" domain={[0, 255]} stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis type="number" dataKey="y" domain={[0, 255]} stroke="#64748b" tick={{ fontSize: 10 }} />
                <Tooltip 
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{ backgroundColor: '#020617', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '11px' }}
                />
                {(scatterMode === 'both' || scatterMode === 'plaintext') && (
                  <Scatter name="Plaintext Scan" data={scatterData?.plaintext_pairs || []} fill="#94a3b8" opacity={0.65} />
                )}
                {(scatterMode === 'both' || scatterMode === 'ciphertext') && (
                  <Scatter name="HICE Cipher" data={scatterData?.ciphertext_pairs || []} fill="#38bdf8" opacity={0.75} />
                )}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
