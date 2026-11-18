import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import UserManagement from './pages/UserManagement';
import SystemSettings from './pages/SystemSettings';
import UploadImage from './pages/UploadImage';
import EncryptStudio from './pages/EncryptStudio';
import DecryptStudio from './pages/DecryptStudio';
import { authService } from './services/authService';
import { Lock, Eye, Share2, BarChart3, AlertTriangle, Database, FolderInput, Clock } from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [viewState, setViewState] = useState('landing'); // 'landing', 'login', 'register', 'app'
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    const user = authService.getCurrentUser();
    if (user && authService.isAuthenticated()) {
      setCurrentUser(user);
      setViewState('app');
    }
  }, []);

  const handleLoginSuccess = (userData) => {
    const userObj = {
      userId: userData.user_id,
      username: userData.username,
      role: userData.role
    };
    setCurrentUser(userObj);
    setViewState('app');
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    authService.logout();
    setCurrentUser(null);
    setViewState('landing');
  };

  // Render Landing Page
  if (viewState === 'landing') {
    return <Landing onGetStarted={() => setViewState('login')} />;
  }

  // Render Login Page
  if (viewState === 'login') {
    return (
      <Login
        onLoginSuccess={handleLoginSuccess}
        onGoToRegister={() => setViewState('register')}
        onBackToLanding={() => setViewState('landing')}
      />
    );
  }

  // Render Register Page
  if (viewState === 'register') {
    return (
      <Register
        onRegisterSuccess={handleLoginSuccess}
        onGoToLogin={() => setViewState('login')}
      />
    );
  }

  // Render Main Authenticated Application
  return (
    <div className="flex h-screen bg-[#0a0f1d] text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        userRole={currentUser?.role || 'USER'}
      />

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        <Navbar user={currentUser} onLogout={handleLogout} />

        <main className="flex-1 overflow-y-auto">
          {activeTab === 'dashboard' && (
            <Dashboard user={currentUser} onNavigate={setActiveTab} />
          )}

          {activeTab === 'users' && <UserManagement />}

          {activeTab === 'settings' && <SystemSettings />}

          {activeTab === 'upload' && (
            <UploadImage onProceedToEncrypt={() => setActiveTab('encrypt')} />
          )}

          {activeTab === 'encrypt' && (
            <EncryptStudio onProceedToFullPipeline={() => setActiveTab('decrypt')} />
          )}

          {activeTab === 'decrypt' && <DecryptStudio />}

          {activeTab === 'shares' && (
            <PhasePlaceholder
              phaseNumber={8}
              title="Secure Image Sharing & ECDH Key Wrapping"
              icon={Share2}
              description="NIST P-256 Elliptic Curve Diffie-Hellman key agreement for authorized doctor-to-doctor transfer, with time-limited expirations and future revocation."
            />
          )}

          {activeTab === 'evaluation' && (
            <PhasePlaceholder
              phaseNumber={11}
              title="Security Evaluation Dashboard"
              icon={BarChart3}
              description="Comparative statistical evaluation: Shannon Entropy, NPCR, UACI, Horizontal/Vertical/Diagonal correlation scatterplots, and 4-way benchmark comparisons."
            />
          )}

          {activeTab === 'monitoring' && (
            <PhasePlaceholder
              phaseNumber={10}
              title="AI Anomaly Detection Sentry"
              icon={AlertTriangle}
              description="Scikit-learn Isolation Forest unsupervised model combined with heuristic rule engines to monitor access spikes, nocturnal requests, and decryption failures."
            />
          )}

          {activeTab === 'audit' && (
            <PhasePlaceholder
              phaseNumber={9}
              title="Cryptographic Hash-Chained Audit Trail"
              icon={Database}
              description="Tamper-evident audit logging where every operational event is mathematically chained with SHA-256 digests: Hash(n) = SHA256(Hash(n-1) || LogData)."
            />
          )}
        </main>
      </div>
    </div>
  );
}

function PhasePlaceholder({ phaseNumber, title, icon: Icon, description }) {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-4">
        <div className="inline-flex p-3 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
          <Icon className="w-8 h-8" />
        </div>
        <div>
          <span className="text-xs font-mono text-sky-400 tracking-widest uppercase">
            Scheduled for Phase {phaseNumber}
          </span>
          <h2 className="text-xl font-bold text-white mt-1">{title}</h2>
        </div>
        <p className="text-xs text-slate-400 max-w-xl mx-auto leading-relaxed">
          {description}
        </p>
        <div className="pt-2 flex items-center justify-center space-x-2 text-xs font-mono text-slate-500">
          <Clock className="w-3.5 h-3.5" />
          <span>Core backend models and REST endpoints active. Engine modules ready for sequential implementation.</span>
        </div>
      </div>
    </div>
  );
}
