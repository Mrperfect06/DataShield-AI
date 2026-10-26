import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  Activity, 
  Zap, 
  Database, 
  Bell, 
  CheckCircle2, 
  AlertTriangle,
  RefreshCw,
  ExternalLink,
  ShieldCheck,
  Lock
} from 'lucide-react';

import Dashboard from './components/Dashboard.jsx';
import SimulateThreat from './components/SimulateThreat.jsx';
import BlockchainExplorer from './components/BlockchainExplorer.jsx';
import AlertsPanel from './components/AlertsPanel.jsx';
import { getHealth } from './services/api.js';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [health, setHealth] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchHealthStatus = async () => {
    setIsRefreshing(true);
    const { data } = await getHealth();
    if (data) setHealth(data);
    setIsRefreshing(false);
  };

  useEffect(() => {
    fetchHealthStatus();
    const interval = setInterval(fetchHealthStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen light-mesh text-slate-800 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <header className="border-b border-slate-200/80 bg-white/85 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-xs">
        <div className="flex items-center space-x-3.5">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/25">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-900 bg-clip-text text-transparent">
                DataShield AI
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-indigo-50 text-indigo-700 border border-indigo-200/80">
                v1.0-LIVE
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium hidden sm:block">
              Explainable • Threat-Proof • Traceable Breach Defense
            </p>
          </div>
        </div>

        {/* Live System Health Indicators */}
        <div className="flex items-center space-x-3">
          <div className="hidden md:flex items-center space-x-2.5 text-xs font-mono bg-white border border-slate-200/90 rounded-xl px-3.5 py-1.5 shadow-xs">
            <div className="flex items-center space-x-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-slate-500">ML:</span>
              <span className="text-emerald-700 font-bold">Active</span>
            </div>
            <span className="text-slate-300">|</span>
            <div className="flex items-center space-x-1.5">
              <span className="h-2 w-2 rounded-full bg-blue-500"></span>
              <span className="text-slate-500">GenAI:</span>
              <span className="text-blue-700 font-bold">RAG+Groq</span>
            </div>
            <span className="text-slate-300">|</span>
            <div className="flex items-center space-x-1.5">
              <span className="h-2 w-2 rounded-full bg-purple-500"></span>
              <span className="text-slate-500">Chain:</span>
              <span className="text-purple-700 font-bold">Polygon PoS</span>
            </div>
          </div>

          <button
            onClick={fetchHealthStatus}
            disabled={isRefreshing}
            className="p-2 rounded-xl bg-slate-100/80 hover:bg-slate-200/80 border border-slate-200 text-slate-600 transition-colors shadow-xs cursor-pointer"
            title="Refresh System Status"
          >
            <RefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="border-b border-slate-200/80 bg-white/70 backdrop-blur-md px-6 sticky top-[61px] z-40">
        <div className="flex space-x-1.5 overflow-x-auto py-2.5 max-w-7xl mx-auto">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              activeTab === 'dashboard'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/25'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/90'
            }`}
          >
            <Activity className="h-4 w-4" />
            <span>Operations Center</span>
          </button>

          <button
            onClick={() => setActiveTab('simulate')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              activeTab === 'simulate'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/25'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/90'
            }`}
          >
            <Zap className={`h-4 w-4 ${activeTab === 'simulate' ? 'text-amber-200' : 'text-amber-500'}`} />
            <span>Threat Simulator</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-md font-mono ${
              activeTab === 'simulate' ? 'bg-white/20 text-white' : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
            }`}>
              ML+Groq
            </span>
          </button>

          <button
            onClick={() => setActiveTab('blockchain')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              activeTab === 'blockchain'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/25'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/90'
            }`}
          >
            <Database className="h-4 w-4 text-purple-500" />
            <span>Immutable Ledger</span>
            <span className={`text-[10px] px-1.5 py-0.2 rounded-md font-mono ${
              activeTab === 'blockchain' ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600 border border-slate-200'
            }`}>
              Polygon
            </span>
          </button>

          <button
            onClick={() => setActiveTab('alerts')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
              activeTab === 'alerts'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md shadow-blue-500/25'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/90'
            }`}
          >
            <Bell className="h-4 w-4 text-rose-500" />
            <span>Active Alerts</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-rose-500 text-white font-mono font-bold shadow-xs">
              7
            </span>
          </button>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {activeTab === 'dashboard' && <Dashboard onNavigateSimulate={() => setActiveTab('simulate')} />}
        {activeTab === 'simulate' && <SimulateThreat onNavigateLedger={() => setActiveTab('blockchain')} />}
        {activeTab === 'blockchain' && <BlockchainExplorer />}
        {activeTab === 'alerts' && <AlertsPanel />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/90 bg-white/80 py-4 px-6 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between">
        <div className="font-medium text-slate-600">
          DataShield AI © 2026 — Zero-Trust Enterprise Data Breach Defense Platform
        </div>
        <div className="flex items-center space-x-4 mt-2 sm:mt-0 font-mono text-[11px] text-slate-500">
          <span>GDPR Art. 33 Verified</span>
          <span>•</span>
          <span>FRE 902 Proof-of-Theft</span>
          <span>•</span>
          <span>SHAP Feature Attribution</span>
        </div>
      </footer>
    </div>
  );
}
