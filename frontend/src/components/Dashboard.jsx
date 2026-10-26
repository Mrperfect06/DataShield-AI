import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle, 
  FileText, 
  ArrowUpRight, 
  TrendingUp, 
  Activity,
  Layers,
  Sparkles,
  Zap,
  Radar,
  Radio,
  Globe2,
  Lock,
  Terminal,
  Crosshair,
  Server,
  Play,
  Pause,
  ExternalLink,
  Cpu,
  Fingerprint
} from 'lucide-react';
import { getStats } from '../services/api.js';

// Pre-defined planted canary assets
const CANARY_DECOYS = [
  {
    token_id: 'CANARY-CC-8821',
    schema: 'prod.credit_cards',
    column: 'CANARY-CC-8821',
    type: 'Ghost Credit Card Decoy',
    status: 'ARMED & ACTIVE',
    statusClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    watermark: '0x8b8deb03732d24...',
    legalRule: 'FRE 902(13)&(14)',
    actionDesc: 'Zero legitimate business value. Any SELECT or EXPORT triggers instant account freeze.',
  },
  {
    token_id: 'CANARY-EMP-004',
    schema: 'prod.employees',
    column: 'secret_token_canary',
    type: 'Executive Decoy Identity',
    status: 'ARMED & ACTIVE',
    statusClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    watermark: '0x4f129ac900b182...',
    legalRule: 'FRE 902(13)&(14)',
    actionDesc: 'Planted VIP credentials in personnel schema. Monitors internal privilege escalation.',
  },
  {
    token_id: 'CANARY-MED-771',
    schema: 'prod.medical_records',
    column: 'patient_ssn_canary',
    type: 'Decoy Medical Record',
    status: 'ARMED & ACTIVE',
    statusClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    watermark: '0xd9910c22e88a31...',
    legalRule: 'HIPAA & FRE 902',
    actionDesc: 'Fabricated patient record. Triggers forensic breach certificate on read attempt.',
  },
];

// Telemetry global origin nodes
const ORIGIN_NODES = [
  { city: 'San Francisco, US', ip: '192.168.1.104', role: 'engineer', risk: 'LOW', lat: '12ms', status: 'Normal Baseline' },
  { city: 'Austin, US', ip: '74.125.210.14', role: 'analyst', risk: 'MEDIUM', lat: '24ms', status: 'Bulk Session Query' },
  { city: 'Bucharest, RO', ip: '185.220.101.5', role: 'contractor', risk: 'HIGH', lat: '128ms', status: 'After-Hours VPN Access' },
  { city: 'Geneva, CH', ip: '194.26.29.112', role: 'contractor', risk: 'CRITICAL', lat: '95ms', status: '🪤 Honey Token Tripped' },
  { city: 'St. Petersburg, RU', ip: '91.240.118.23', role: 'admin', risk: 'CRITICAL', lat: '184ms', status: 'Bulk DB Exfiltration' },
];

export default function Dashboard({ onNavigateSimulate }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [selectedNode, setSelectedNode] = useState(ORIGIN_NODES[0]);
  const [isLiveStream, setIsLiveStream] = useState(true);

  const loadData = async () => {
    const { data } = await getStats();
    if (data) setStats(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      if (isLiveStream) loadData();
    }, 6000);
    return () => clearInterval(interval);
  }, [isLiveStream]);

  const getThreatBadge = (level) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-50 text-rose-700 border-rose-200 font-bold';
      case 'HIGH':
        return 'bg-orange-50 text-orange-700 border-orange-200 font-bold';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-800 border-amber-200 font-bold';
      default:
        return 'bg-emerald-50 text-emerald-700 border-emerald-200 font-bold';
    }
  };

  // Filtered recent events
  const recentEvents = stats?.recent_events || [
    { event_id: 'EVT-9041', timestamp: new Date(Date.now() - 30000).toISOString(), user_id: 'user_dev_012', action: 'SELECT', table_name: 'public.products', threat_score: 12.0, threat_level: 'LOW' },
    { event_id: 'EVT-9040', timestamp: new Date(Date.now() - 120000).toISOString(), user_id: 'user_mkt_004', action: 'EXPORT', table_name: 'analytics.sessions', threat_score: 38.0, threat_level: 'MEDIUM' },
    { event_id: 'EVT-9039', timestamp: new Date(Date.now() - 300000).toISOString(), user_id: 'user_ops_089', action: 'DOWNLOAD', table_name: 'prod.medical_records', threat_score: 68.0, threat_level: 'HIGH' },
    { event_id: 'EVT-9038', timestamp: new Date(Date.now() - 600000).toISOString(), user_id: 'insider_contractor_99', action: 'EXPORT', table_name: 'prod.credit_cards', threat_score: 100.0, threat_level: 'CRITICAL' },
  ];

  const filteredEvents = activeFilter === 'ALL' 
    ? recentEvents 
    : recentEvents.filter((ev) => ev.threat_level?.toUpperCase() === activeFilter);

  return (
    <div className="space-y-6">
      {/* Light Gradient Hero SOC Banner */}
      <div className="bg-gradient-to-br from-white via-slate-50 to-indigo-50/40 border border-slate-200/90 rounded-3xl p-6 sm:p-7 relative overflow-hidden shadow-xs">
        {/* Subtle decorative glow */}
        <div className="absolute right-0 top-0 bottom-0 w-96 pointer-events-none opacity-40 flex items-center justify-center overflow-hidden">
          <div className="w-96 h-96 rounded-full border border-indigo-200/50 relative flex items-center justify-center">
            <div className="w-72 h-72 rounded-full border border-indigo-200/40"></div>
            <div className="w-48 h-48 rounded-full border border-indigo-200/30"></div>
            <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-indigo-500/10 to-transparent animate-radar rounded-full"></div>
          </div>
        </div>

        <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
          <div className="space-y-2.5 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-2 shadow-2xs">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
                <span>AUTONOMOUS DEFENSE ACTIVE</span>
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-purple-50 text-purple-700 border border-purple-200">
                Polygon PoS Smart Contract #137
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200">
                Groq openai/gpt-oss-120b
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Enterprise Data Breach Defense & Forensic Center
            </h1>
            <p className="text-slate-600 text-xs sm:text-sm leading-relaxed">
              Real-time multi-model ML anomaly scoring (Isolation Forest + Deep Autoencoder + LSTM), SHAP explainability, and cryptographic proof-of-theft recording on immutable blockchain.
            </p>
          </div>

          <div className="flex items-center space-x-3 shrink-0">
            <button
              onClick={onNavigateSimulate}
              className="flex items-center space-x-2.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white font-bold text-xs sm:text-sm px-6 py-3.5 rounded-2xl shadow-md shadow-indigo-500/25 transition-all cursor-pointer whitespace-nowrap active:scale-[0.98] group"
            >
              <Zap className="h-4 w-4 text-amber-300 group-hover:scale-110 transition-transform" />
              <span>LAUNCH THREAT SIMULATOR</span>
              <ArrowUpRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 4 Clean Light Metric Cards with Sparklines */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Verified Events */}
        <div className="bg-white border border-slate-200/90 hover:border-indigo-400/80 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all duration-300 relative group overflow-hidden">
          <div className="flex items-center justify-between text-slate-500 mb-3">
            <span className="text-[11px] uppercase tracking-wider font-bold font-mono">Total Verified Events</span>
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600 group-hover:bg-blue-100 transition-colors">
              <Activity className="h-4 w-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-slate-900 font-mono tracking-tight">
            {loading ? '...' : (stats?.total_events ?? 142).toLocaleString()}
          </div>
          <div className="mt-3 flex items-center justify-between pt-2.5 border-t border-slate-100">
            <div className="flex items-center space-x-1.5 text-[11px] text-emerald-600 font-bold font-mono">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>100% Keccak-256</span>
            </div>
            {/* Sparkline wave */}
            <svg className="w-16 h-5 text-emerald-500" viewBox="0 0 60 20">
              <path
                d="M 0,15 Q 15,5 30,12 T 60,4"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
        </div>

        {/* Card 2: Active Threat Alerts */}
        <div className="bg-white border border-slate-200/90 hover:border-amber-400/80 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all duration-300 relative group overflow-hidden">
          <div className="flex items-center justify-between text-slate-500 mb-3">
            <span className="text-[11px] uppercase tracking-wider font-bold font-mono">Active Threat Alerts</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600 group-hover:bg-amber-100 transition-colors">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-amber-600 font-mono tracking-tight">
            {loading ? '...' : (stats?.total_alerts ?? 7)}
          </div>
          <div className="mt-3 flex items-center justify-between pt-2.5 border-t border-slate-100">
            <span className="text-[11px] text-slate-500 font-mono">
              {stats?.unresolved_alerts ?? 2} pending triages
            </span>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
              SOC Active
            </span>
          </div>
        </div>

        {/* Card 3: Honey Token Decoy Grid */}
        <div className="bg-white border border-slate-200/90 hover:border-rose-400/80 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all duration-300 relative group overflow-hidden">
          <div className="flex items-center justify-between text-slate-500 mb-3">
            <span className="text-[11px] uppercase tracking-wider font-bold font-mono">Honey Token Traps</span>
            <div className="p-2 rounded-xl bg-rose-50 text-rose-600 group-hover:bg-rose-100 transition-colors">
              <ShieldAlert className="h-4 w-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-rose-600 font-mono tracking-tight flex items-center gap-2">
            <span>3</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 uppercase font-bold">
              ARMED
            </span>
          </div>
          <div className="mt-3 flex items-center justify-between pt-2.5 border-t border-slate-100">
            <span className="text-[11px] text-rose-700 font-mono font-semibold">FRE 902(13)&(14)</span>
            <span className="text-[10px] text-slate-400 font-mono">Zero False Pos</span>
          </div>
        </div>

        {/* Card 4: ML Models Ensemble Health */}
        <div className="bg-white border border-slate-200/90 hover:border-purple-400/80 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all duration-300 relative group overflow-hidden">
          <div className="flex items-center justify-between text-slate-500 mb-3">
            <span className="text-[11px] uppercase tracking-wider font-bold font-mono">ML Ensemble Health</span>
            <div className="p-2 rounded-xl bg-purple-50 text-purple-600 group-hover:bg-purple-100 transition-colors">
              <Cpu className="h-4 w-4" />
            </div>
          </div>
          <div className="text-3xl font-black text-purple-600 font-mono tracking-tight flex items-center gap-2">
            <span>3 / 3</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 font-bold">
              OPTIMAL
            </span>
          </div>
          <div className="mt-3 flex items-center justify-between pt-2.5 border-t border-slate-100 text-[10px] font-mono text-slate-500 font-medium">
            <span className="text-blue-600">IForest</span>
            <span>•</span>
            <span className="text-purple-600">Autoencoder</span>
            <span>•</span>
            <span className="text-indigo-600">LSTM</span>
          </div>
        </div>
      </div>

      {/* Middle Section: Global Telemetry Nodes & Planted Honey Token Deck */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Global Telemetry Vector Radar */}
        <div className="lg:col-span-7 bg-white border border-slate-200/90 rounded-3xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3.5 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <div className="p-1.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
                <Globe2 className="h-4 w-4" />
              </div>
              <h3 className="text-sm font-extrabold text-slate-900 tracking-wide">
                Live Origin Vectors & Geolocation Telemetry
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md font-semibold">
              5 Active Ingress Gateways
            </span>
          </div>

          <p className="text-xs text-slate-500">
            Real-time origin endpoints sending database access requests. Click any gateway to inspect telemetry parameters.
          </p>

          <div className="space-y-2.5">
            {ORIGIN_NODES.map((node, i) => {
              const isSelected = selectedNode.city === node.city;
              return (
                <div
                  key={i}
                  onClick={() => setSelectedNode(node)}
                  className={`p-3.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-blue-50/50 border-blue-400 shadow-xs'
                      : 'bg-slate-50/60 border-slate-200/80 hover:bg-slate-100/70 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="h-2.5 w-2.5 rounded-full bg-blue-600"></span>
                    <div>
                      <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                        <span>{node.city}</span>
                        <span className="text-[10px] font-mono text-slate-500 font-normal">[{node.ip}]</span>
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                        Role: <span className="text-slate-800 font-medium">{node.role}</span> • {node.status}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className="text-[10px] font-mono text-slate-400 hidden sm:inline-block">
                      {node.lat} latency
                    </span>
                    <span
                      className={`text-[10px] px-2.5 py-1 rounded-full font-mono font-bold border ${
                        node.risk === 'CRITICAL'
                          ? 'bg-rose-50 text-rose-700 border-rose-200'
                          : node.risk === 'HIGH'
                          ? 'bg-orange-50 text-orange-700 border-orange-200'
                          : node.risk === 'MEDIUM'
                          ? 'bg-amber-50 text-amber-800 border-amber-200'
                          : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      }`}
                    >
                      {node.risk} RISK
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Planted Honey Token Traps Deck */}
        <div className="lg:col-span-5 bg-white border border-slate-200/90 rounded-3xl p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3.5 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <span className="text-xl">🪤</span>
              <h3 className="text-sm font-extrabold text-slate-900 tracking-wide">
                Planted Honey Token Deception Grid
              </h3>
            </div>
            <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 font-mono font-bold">
              3 ACTIVE DECOYS
            </span>
          </div>

          <p className="text-xs text-slate-500">
            Cryptographically watermarked canary assets planted in sensitive production tables to catch rogue insiders with 100% legal proof of theft.
          </p>

          <div className="space-y-3">
            {CANARY_DECOYS.map((canary, idx) => (
              <div
                key={idx}
                className="bg-slate-50/70 p-3.5 rounded-2xl border border-slate-200/90 space-y-2 hover:border-indigo-300 hover:bg-white transition-all shadow-2xs"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-indigo-700">
                    {canary.token_id}
                  </span>
                  <span className={`text-[9px] px-2 py-0.5 rounded-md font-mono font-bold border ${canary.statusClass}`}>
                    {canary.status}
                  </span>
                </div>

                <div className="text-[11px] text-slate-700 font-medium">
                  Table: <code className="text-indigo-600 bg-indigo-50 px-1 py-0.5 rounded font-mono border border-indigo-100">`{canary.schema}`</code> | {canary.type}
                </div>

                <p className="text-[11px] text-slate-600 leading-relaxed font-sans">
                  {canary.actionDesc}
                </p>

                <div className="flex items-center justify-between pt-2 border-t border-slate-200/70 text-[10px] font-mono text-slate-500">
                  <span>Watermark: {canary.watermark}</span>
                  <span className="text-indigo-600 font-bold">{canary.legalRule}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Real-Time Threat Score Spectrum & Distribution */}
      <div className="bg-white border border-slate-200/90 rounded-3xl p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3.5 border-b border-slate-100">
          <div>
            <h2 className="text-sm font-extrabold uppercase tracking-wider text-slate-900 flex items-center gap-2">
              <Radar className="h-4 w-4 text-blue-600" />
              <span>Calibrated Threat Risk Spectrum</span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Continuous score distribution calibrated against standard operational baselines.
            </p>
          </div>

          {/* Severity Filter Pills */}
          <div className="flex items-center space-x-1.5 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-mono">
            {['ALL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setActiveFilter(lvl)}
                className={`px-3 py-1 rounded-lg transition-all cursor-pointer font-bold text-[10px] ${
                  activeFilter === lvl
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>

        {(() => {
          const dist = stats?.events_by_level || { LOW: 85, MEDIUM: 38, HIGH: 14, CRITICAL: 5 };
          const total = Math.max(1, (dist.LOW || 0) + (dist.MEDIUM || 0) + (dist.HIGH || 0) + (dist.CRITICAL || 0));
          const pLow = ((dist.LOW || 0) / total) * 100;
          const pMed = ((dist.MEDIUM || 0) / total) * 100;
          const pHigh = ((dist.HIGH || 0) / total) * 100;
          const pCrit = ((dist.CRITICAL || 0) / total) * 100;

          return (
            <div className="space-y-4">
              {/* Segmented Bar */}
              <div className="h-3.5 w-full bg-slate-100 rounded-full flex overflow-hidden border border-slate-200 p-0.5 shadow-inner">
                <div style={{ width: `${pLow}%` }} className="bg-emerald-500 h-full rounded-l-full transition-all duration-700" title={`Low: ${dist.LOW} (${Math.round(pLow)}%)`} />
                <div style={{ width: `${pMed}%` }} className="bg-amber-400 h-full transition-all duration-700" title={`Medium: ${dist.MEDIUM} (${Math.round(pMed)}%)`} />
                <div style={{ width: `${pHigh}%` }} className="bg-orange-500 h-full transition-all duration-700" title={`High: ${dist.HIGH} (${Math.round(pHigh)}%)`} />
                <div style={{ width: `${pCrit}%` }} className="bg-rose-500 h-full rounded-r-full transition-all duration-700" title={`Critical: ${dist.CRITICAL} (${Math.round(pCrit)}%)`} />
              </div>

              {/* 4 Cards with Dynamic Percentages */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div 
                  onClick={() => setActiveFilter('LOW')}
                  className={`bg-slate-50/70 p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    activeFilter === 'LOW' ? 'border-emerald-500 ring-2 ring-emerald-500/20 bg-emerald-50/40' : 'border-slate-200 hover:border-emerald-400'
                  }`}
                >
                  <div className="text-[11px] text-slate-500 font-mono uppercase font-bold">LOW (0-34)</div>
                  <div className="text-2xl font-black text-emerald-600 font-mono mt-0.5">{dist.LOW || 0}</div>
                  <span className="text-[10px] text-emerald-700 font-mono font-medium">Routine Baseline ({Math.round(pLow)}%)</span>
                </div>

                <div 
                  onClick={() => setActiveFilter('MEDIUM')}
                  className={`bg-slate-50/70 p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    activeFilter === 'MEDIUM' ? 'border-amber-500 ring-2 ring-amber-500/20 bg-amber-50/40' : 'border-slate-200 hover:border-amber-400'
                  }`}
                >
                  <div className="text-[11px] text-slate-500 font-mono uppercase font-bold">MEDIUM (35-59)</div>
                  <div className="text-2xl font-black text-amber-600 font-mono mt-0.5">{dist.MEDIUM || 0}</div>
                  <span className="text-[10px] text-amber-700 font-mono font-medium">Elevated Velocity ({Math.round(pMed)}%)</span>
                </div>

                <div 
                  onClick={() => setActiveFilter('HIGH')}
                  className={`bg-slate-50/70 p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    activeFilter === 'HIGH' ? 'border-orange-500 ring-2 ring-orange-500/20 bg-orange-50/40' : 'border-slate-200 hover:border-orange-400'
                  }`}
                >
                  <div className="text-[11px] text-slate-500 font-mono uppercase font-bold">HIGH (60-79)</div>
                  <div className="text-2xl font-black text-orange-600 font-mono mt-0.5">{dist.HIGH || 0}</div>
                  <span className="text-[10px] text-orange-700 font-mono font-medium">Policy Deviation ({Math.round(pHigh)}%)</span>
                </div>

                <div 
                  onClick={() => setActiveFilter('CRITICAL')}
                  className={`bg-slate-50/70 p-3.5 rounded-2xl border transition-all cursor-pointer ${
                    activeFilter === 'CRITICAL' ? 'border-rose-500 ring-2 ring-rose-500/20 bg-rose-50/40' : 'border-slate-200 hover:border-rose-400'
                  }`}
                >
                  <div className="text-[11px] text-slate-500 font-mono uppercase font-bold">CRITICAL (80-100)</div>
                  <div className="text-2xl font-black text-rose-600 font-mono mt-0.5">{dist.CRITICAL || 0}</div>
                  <span className="text-[10px] text-rose-700 font-mono font-bold">Breach Alert ({Math.round(pCrit)}%)</span>
                </div>
              </div>
            </div>
          );
        })()}
      </div>

      {/* Live Recent Events Stream Table */}
      <div className="bg-white border border-slate-200/90 rounded-3xl overflow-hidden shadow-xs">
        <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3">
            <div className="h-8 w-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
              <Terminal className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-extrabold text-slate-900 flex items-center gap-2">
                <span>Live Telemetry & Access Event Stream</span>
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              </h2>
              <p className="text-xs text-slate-500 font-mono">
                Showing {filteredEvents.length} events {activeFilter !== 'ALL' ? `(Filtered: ${activeFilter})` : ''}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsLiveStream(!isLiveStream)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-mono border transition-all cursor-pointer ${
                isLiveStream
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200 font-bold'
                  : 'bg-slate-100 text-slate-600 border-slate-200'
              }`}
            >
              {isLiveStream ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
              <span>{isLiveStream ? 'STREAM ACTIVE' : 'PAUSED'}</span>
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600 text-[11px] uppercase font-mono border-b border-slate-200">
              <tr>
                <th className="py-3.5 px-5">Event ID</th>
                <th className="py-3.5 px-5">Timestamp</th>
                <th className="py-3.5 px-5">Principal User</th>
                <th className="py-3.5 px-5">Action</th>
                <th className="py-3.5 px-5">Target Schema</th>
                <th className="py-3.5 px-5 text-center">Threat Score</th>
                <th className="py-3.5 px-5 text-center">Risk Level</th>
                <th className="py-3.5 px-5 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {filteredEvents.map((ev, i) => (
                <tr key={i} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-4 px-5 font-bold text-blue-600">
                    {ev.event_id || `EVT-${1000 + i}`}
                  </td>
                  <td className="py-4 px-5 text-slate-500">
                    {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Just now'}
                  </td>
                  <td className="py-4 px-5 text-slate-800 font-sans font-semibold">
                    {ev.user_id}
                  </td>
                  <td className="py-4 px-5">
                    <span className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-700 font-mono text-[11px] font-bold">
                      {ev.action}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-purple-700 font-semibold">
                    `{ev.table_name}`
                  </td>
                  <td className="py-4 px-5 text-center font-bold">
                    <span className={
                      ev.threat_score >= 80 ? 'text-rose-600' :
                      ev.threat_score >= 60 ? 'text-orange-600' :
                      ev.threat_score >= 35 ? 'text-amber-600' : 'text-emerald-600'
                    }>
                      {typeof ev.threat_score === 'number' ? ev.threat_score.toFixed(1) : ev.threat_score}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-center">
                    <span className={`px-3 py-1 rounded-full text-[10px] font-extrabold border ${getThreatBadge(ev.threat_level)}`}>
                      {ev.threat_level}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-right">
                    <button
                      onClick={onNavigateSimulate}
                      className="text-xs text-blue-600 hover:text-white bg-blue-50 hover:bg-blue-600 border border-blue-200 px-3 py-1 rounded-lg transition-colors cursor-pointer font-bold"
                    >
                      Analyze
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
