import React, { useState, useEffect } from 'react';
import { 
  FolderInput, Upload, FileImage, CheckCircle, AlertCircle, 
  ArrowRight, Shield, Sparkles, FileText, Lock
} from 'lucide-react';
import { imageService } from '../services/imageService';
import StatusBadge from '../components/StatusBadge';

export default function UploadImage({ onProceedToEncrypt }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [title, setTitle] = useState('');
  const [modality, setModality] = useState('X-RAY');
  const [bodyPart, setBodyPart] = useState('CHEST');
  const [patientPseudonym, setPatientPseudonym] = useState('');
  const [clinicalNotes, setClinicalNotes] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [ingestionReceipt, setIngestionReceipt] = useState(null);
  const [samples, setSamples] = useState([]);

  useEffect(() => {
    const fetchSamples = async () => {
      try {
        const data = await imageService.getSampleScans();
        setSamples(data);
      } catch (err) {
        console.error('Failed to load sample scans:', err);
      }
    };
    fetchSamples();
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      setTitle(file.name.replace(/\.[^/.]+$/, '').replace(/_/g, ' '));
      setPreviewUrl(URL.createObjectURL(file));
      setError('');
      setIngestionReceipt(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select an image file to upload.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', title);
      formData.append('modality', modality);
      formData.append('body_part', bodyPart);
      formData.append('patient_pseudonym', patientPseudonym || `PT-ANON-${Math.floor(1000 + Math.random() * 9000)}`);
      formData.append('clinical_notes', clinicalNotes);

      const receipt = await imageService.uploadImage(formData);
      setIngestionReceipt(receipt);
    } catch (err) {
      setError(err.response?.data?.detail || 'Image validation or ingestion failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async (sampleFilename) => {
    setLoading(true);
    setError('');
    try {
      const receipt = await imageService.loadSampleScan(sampleFilename);
      setIngestionReceipt(receipt);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load synthetic medical scan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
          <FolderInput className="w-5 h-5 text-sky-400" />
          <span>Diagnostic Scan Ingestion & Preprocessing</span>
        </h2>
      </div>

      {/* Synthetic Demonstration Scan Selector */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-sky-950/30 to-slate-900 border border-sky-500/20 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Research Demonstration: 1-Click Synthetic Medical Scans
            </span>
          </div>
          <span className="text-[11px] font-mono text-slate-400">NON-IDENTIFIABLE TEST DATA</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              id: 'synthetic_chest_xray.png',
              title: 'PA Chest Radiograph',
              mod: 'X-RAY',
              desc: '512x512 Grayscale X-ray with rib cage and cardiac silhouette',
              size: '512 x 512'
            },
            {
              id: 'synthetic_brain_mri.png',
              title: 'Axial T2 Brain MRI',
              mod: 'MRI',
              desc: '512x512 Grayscale MRI slice with ventricular anatomy',
              size: '512 x 512'
            },
            {
              id: 'sample_histology.bmp',
              title: 'Histology Cell Stain',
              mod: 'BMP',
              desc: '256x256 RGB Histology sample in uncompressed BMP format',
              size: '256 x 256'
            }
          ].map((sample) => (
            <button
              key={sample.id}
              onClick={() => handleLoadSample(sample.id)}
              disabled={loading}
              className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-sky-500/40 text-left transition-all space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <StatusBadge status="active" text={sample.mod} />
                <span className="text-[10px] font-mono text-slate-500">{sample.size}</span>
              </div>
              <p className="text-xs font-bold text-white group-hover:text-sky-300 transition-colors">
                {sample.title}
              </p>
              <div className="pt-2 text-[10px] font-mono text-sky-400 flex items-center space-x-1">
                <span>Ingest Sample</span>
                <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Ingestion Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Form */}
        <div className="lg:col-span-2 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-6">
          <form onSubmit={handleUpload} className="space-y-4">
            {/* File Dropzone */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-300 block">Select Image File</label>
              <div className="border-2 border-dashed border-slate-700 hover:border-sky-500/50 rounded-xl p-6 text-center transition-colors bg-slate-950/40 cursor-pointer relative">
                <input
                  type="file"
                  accept="image/png, image/jpeg, image/bmp"
                  onChange={handleFileChange}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <div className="space-y-2">
                  <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mx-auto">
                    <Upload className="w-5 h-5" />
                  </div>
                  <p className="text-xs font-semibold text-slate-300">
                    {selectedFile ? selectedFile.name : 'Click or drag and drop image here'}
                  </p>
                  <p className="text-[11px] font-mono text-slate-500">
                    Supports PNG, JPEG, JPG, BMP (Up to 50 MB)
                  </p>
                </div>
              </div>
            </div>

            {/* Metadata Fields */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Scan Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Chest X-Ray Baseline"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-600 outline-none focus:border-sky-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Modality</label>
                <select
                  value={modality}
                  onChange={(e) => setModality(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-100 outline-none focus:border-sky-500"
                >
                  <option value="X-RAY">X-Ray (Radiography)</option>
                  <option value="MRI">MRI (Magnetic Resonance)</option>
                  <option value="CT">CT (Computed Tomography)</option>
                  <option value="GENERAL">General / Document</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Anatomical Region</label>
                <input
                  type="text"
                  value={bodyPart}
                  onChange={(e) => setBodyPart(e.target.value)}
                  placeholder="e.g. CHEST, BRAIN, SPINE"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-600 outline-none focus:border-sky-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-300">Patient Pseudonym</label>
                <input
                  type="text"
                  value={patientPseudonym}
                  onChange={(e) => setPatientPseudonym(e.target.value)}
                  placeholder="e.g. PT-ANON-9012"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-600 outline-none focus:border-sky-500"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-300">Clinical / Diagnostic Notes</label>
              <textarea
                rows={2}
                value={clinicalNotes}
                onChange={(e) => setClinicalNotes(e.target.value)}
                placeholder="Optional diagnostic observations..."
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-100 placeholder-slate-600 outline-none focus:border-sky-500"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !selectedFile}
              className="w-full py-2.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all shadow-lg shadow-sky-500/20 disabled:opacity-50"
            >
              {loading ? 'Validating Magic Bytes & Normalizing...' : 'Validate & Ingest Image'}
            </button>
          </form>
        </div>

        {/* Ingestion Status & Preview Sidebar */}
        <div className="space-y-6">
          {previewUrl && (
            <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
              <span className="text-xs font-semibold text-slate-300 block">Ingestion Preview</span>
              <div className="rounded-xl overflow-hidden bg-black flex items-center justify-center max-h-56 border border-slate-800">
                <img src={previewUrl} alt="Preview" className="max-h-56 object-contain" />
              </div>
            </div>
          )}

          {ingestionReceipt && (
            <div className="p-6 rounded-2xl bg-slate-900 border border-emerald-500/30 space-y-4 shadow-xl">
              <div className="flex items-center space-x-2 text-emerald-400">
                <CheckCircle className="w-5 h-5" />
                <span className="text-xs font-bold uppercase tracking-wider">Ingestion Verified</span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between py-1 border-b border-slate-800 text-slate-400">
                  <span>Image ID</span>
                  <span className="text-white truncate max-w-[140px]">{ingestionReceipt.image_id}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800 text-slate-400">
                  <span>Dimensions</span>
                  <span className="text-sky-400">
                    {ingestionReceipt.dimensions.width} x {ingestionReceipt.dimensions.height} x {ingestionReceipt.dimensions.channels}
                  </span>
                </div>
                <div className="py-1 border-b border-slate-800 text-slate-400">
                  <span className="block mb-1">Original Pixel SHA-256</span>
                  <span className="text-[10px] text-emerald-400 break-all bg-slate-950 p-1.5 rounded block">
                    {ingestionReceipt.original_sha256}
                  </span>
                </div>
              </div>

              <button
                onClick={onProceedToEncrypt}
                className="w-full py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all flex items-center justify-center space-x-2 shadow-lg shadow-emerald-500/20"
              >
                <Lock className="w-4 h-4" />
                <span>Proceed to Hybrid Encryption</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
