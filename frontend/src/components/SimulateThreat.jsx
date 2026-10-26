import React, { useState } from 'react';
import { 
  Zap, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  AlertOctagon, 
  FileText, 
  Database, 
  ExternalLink, 
  Sparkles,
  Lock,
  Compass,
  Sliders,
  Volume2,
  VolumeX,
  Radio,
  Crosshair,
  Radar,
  AlertTriangle,
  Play,
  Printer,
  Download,
  FileDown
} from 'lucide-react';
import { analyzeEvent } from '../services/api.js';
import FormattedReport from './FormattedReport.jsx';
import { printReportPDF, downloadReportDoc } from '../services/exportReport.js';

// Audio Synthesizer using Web Audio API (Zero external assets required)
function playTone(type = 'ping') {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    if (type === 'alarm') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, now);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.15);
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.3);
      osc.frequency.exponentialRampToValueAtTime(440, now + 0.45);
      gain.gain.setValueAtTime(0.15, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.5);
    } else {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(1400, now);
      osc.frequency.exponentialRampToValueAtTime(700, now + 0.12);
      gain.gain.setValueAtTime(0.08, now);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.12);
    }
  } catch (e) {
    // Browser gesture handling
  }
}

const PRESETS = {
  normal: {
    title: 'Safe Dev Query',
    badge: 'LOW RISK',
    badgeClass: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    icon: '🌱',
    user_id: 'user_dev_012',
    user_email: 'sarah.chen@cloudcorp.internal',
    user_role: 'engineer',
    department: 'Core Infra',
    action: 'SELECT',
    table_name: 'public.products',
    columns_accessed: ['id', 'name', 'status', 'created_at'],
    num_rows_affected: 45,
    source_ip: '192.168.1.104',
    geo_location: 'San Francisco, US',
    session_duration_seconds: 300,
    is_vpn: false,
    is_after_hours: false,
  },
  suspicious_download: {
    title: 'Marketing Export',
    badge: 'MEDIUM',
    badgeClass: 'bg-amber-50 text-amber-800 border-amber-200',
    icon: '📊',
    user_id: 'user_mkt_004',
    user_email: 'mark.taylor@cloudcorp.internal',
    user_role: 'analyst',
    department: 'Marketing',
    action: 'EXPORT',
    table_name: 'analytics.sessions',
    columns_accessed: ['id', 'user_id', 'ip_address', 'country'],
    num_rows_affected: 8500,
    source_ip: '74.125.210.14',
    geo_location: 'Austin, US',
    session_duration_seconds: 1800,
    is_vpn: false,
    is_after_hours: false,
  },
  after_hours_pii: {
    title: 'After-Hours PII',
    badge: 'HIGH RISK',
    badgeClass: 'bg-orange-50 text-orange-800 border-orange-200',
    icon: '🕵️',
    user_id: 'user_ops_089',
    user_email: 'alex.rivas@cloudcorp.internal',
    user_role: 'contractor',
    department: 'Data Operations',
    action: 'DOWNLOAD',
    table_name: 'prod.medical_records',
    columns_accessed: ['patient_id', 'ssn', 'diagnosis', 'dob', 'address'],
    num_rows_affected: 12500,
    source_ip: '185.220.101.5',
    geo_location: 'Bucharest, RO',
    session_duration_seconds: 45,
    is_vpn: true,
    is_after_hours: true,
  },
  exfiltration: {
    title: 'Bulk DB Dump',
    badge: 'CRITICAL',
    badgeClass: 'bg-rose-50 text-rose-700 border-rose-200 font-bold',
    icon: '🧨',
    user_id: 'user_corp_007',
    user_email: 'david.miller@cloudcorp.internal',
    user_role: 'admin',
    department: 'IT Systems',
    action: 'EXPORT',
    table_name: 'prod.credit_cards',
    columns_accessed: ['credit_card', 'cvv', 'cardholder_name', 'billing_address', 'phone'],
    num_rows_affected: 142000,
    source_ip: '91.240.118.23',
    geo_location: 'St. Petersburg, RU',
    session_duration_seconds: 60,
    is_vpn: true,
    is_after_hours: true,
  },
  honey_trap: {
    title: 'Honey Token Trap',
    badge: 'TRAP SPRUNG',
    badgeClass: 'bg-rose-100 text-rose-800 border-rose-300 font-extrabold',
    icon: '🪤',
    user_id: 'insider_contractor_99',
    user_email: 'viktor.k@corp-partners.io',
    user_role: 'contractor',
    department: 'Data Pipeline',
    action: 'EXPORT',
    table_name: 'prod.credit_cards',
    columns_accessed: ['cardholder_name', 'credit_card', 'cvv', 'CANARY-CC-8821'],
    num_rows_affected: 2500,
    source_ip: '194.26.29.112',
    geo_location: 'Geneva, CH',
    session_duration_seconds: 30,
    is_vpn: true,
    is_after_hours: false,
  },
};

const SUGGESTED_COLUMNS = [
  { name: 'id', isPii: false, isHoney: false },
  { name: 'name', isPii: false, isHoney: false },
  { name: 'status', isPii: false, isHoney: false },
  { name: 'created_at', isPii: false, isHoney: false },
  { name: 'email', isPii: true, isHoney: false },
  { name: 'ssn', isPii: true, isHoney: false },
  { name: 'credit_card', isPii: true, isHoney: false },
  { name: 'cvv', isPii: true, isHoney: false },
  { name: 'CANARY-CC-8821', isPii: true, isHoney: true },
];

export default function SimulateThreat({ onNavigateLedger }) {
  const [formData, setFormData] = useState(PRESETS.normal);
  const [columnsInput, setColumnsInput] = useState(PRESETS.normal.columns_accessed.join(', '));
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [activePresetKey, setActivePresetKey] = useState('normal');

  const applyPreset = (presetKey) => {
    setActivePresetKey(presetKey);
    const selected = PRESETS[presetKey];
    setFormData(selected);
    setColumnsInput(selected.columns_accessed.join(', '));
    if (soundEnabled) playTone('ping');
  };

  const toggleColumnChip = (colName) => {
    const currentCols = columnsInput
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean);

    let nextCols;
    if (currentCols.includes(colName)) {
      nextCols = currentCols.filter((c) => c !== colName);
    } else {
      nextCols = [...currentCols, colName];
    }
    setColumnsInput(nextCols.join(', '));
    setFormData((prev) => ({ ...prev, columns_accessed: nextCols }));
    if (soundEnabled) playTone('ping');
  };

  const handleSliderChange = (e) => {
    const val = parseInt(e.target.value, 10);
    setFormData((prev) => ({ ...prev, num_rows_affected: val }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const payload = {
      ...formData,
      num_rows_affected: parseInt(formData.num_rows_affected, 10) || 0,
      columns_accessed: columnsInput
        .split(',')
        .map((c) => c.trim())
        .filter(Boolean),
    };

    try {
      const resp = await analyzeEvent(payload);
      if (resp.error) {
        setError(resp.error);
      } else {
        setResult(resp.data);
        if (soundEnabled) {
          if (resp.data.event?.honey_token_tripped || resp.data.threat_score >= 80) {
            playTone('alarm');
          } else {
            playTone('ping');
          }
        }
      }
    } catch (err) {
      setError(err.message || 'Error executing threat analysis');
    } finally {
      setLoading(false);
    }
  };

  // Color theme derivations
  const score = result ? (result.event?.threat_score ?? result.threat_score ?? 12) : 12;
  const threatLevel = result ? (result.event?.threat_level ?? result.threat_level ?? 'LOW') : 'LOW';
  const factors = result ? (result.event?.contributing_factors ?? result.contributing_factors ?? []) : [];
  const rawScores = result ? (result.event?.raw_scores ?? result.raw_scores ?? {}) : {};
  const isHoneyTripped = result?.event?.honey_token_tripped;

  const getScoreColor = (val) => {
    if (val >= 80) return { text: 'text-rose-700', stroke: '#e11d48', border: 'border-rose-200', bg: 'bg-rose-50/70', pill: 'bg-rose-100 text-rose-800' };
    if (val >= 60) return { text: 'text-orange-700', stroke: '#ea580c', border: 'border-orange-200', bg: 'bg-orange-50/70', pill: 'bg-orange-100 text-orange-800' };
    if (val >= 35) return { text: 'text-amber-800', stroke: '#d97706', border: 'border-amber-200', bg: 'bg-amber-50/70', pill: 'bg-amber-100 text-amber-800' };
    return { text: 'text-emerald-700', stroke: '#059669', border: 'border-emerald-200', bg: 'bg-emerald-50/70', pill: 'bg-emerald-100 text-emerald-800' };
  };

  const scoreTheme = getScoreColor(score);
  const strokeDashoffset = 301.6 * (1 - Math.min(score, 100) / 100);

  return (
    <div className={`space-y-6 ${isHoneyTripped ? 'p-2 rounded-3xl animate-alert-light' : ''}`}>
      {/* Light Gradient Hero Control Bar */}
      <div className="bg-gradient-to-br from-white via-slate-50 to-indigo-50/40 border border-slate-200/90 rounded-3xl p-6 shadow-xs relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="flex items-center space-x-2.5">
              <span className="p-2 rounded-xl bg-blue-50 text-blue-600 border border-blue-200 shadow-2xs">
                <Radar className="h-5 w-5" />
              </span>
              <div>
                <h2 className="text-lg font-black text-slate-900 tracking-tight flex items-center gap-2">
                  <span>LIVE THREAT SIMULATOR & HONEY TRAP LAB</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-bold bg-blue-50 text-blue-700 border border-blue-200">
                    REAL-TIME ML + RAG
                  </span>
                </h2>
                <p className="text-xs text-slate-500 font-medium">
                  Inject live data access vectors, trigger honey token canary traps, and inspect Groq LLM forensic reports.
                </p>
              </div>
            </div>
          </div>

          {/* Sound Toggle */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setSoundEnabled(!soundEnabled)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-mono border transition-all cursor-pointer ${
                soundEnabled
                  ? 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
                  : 'bg-slate-100 text-slate-500 border-slate-200 hover:text-slate-700'
              }`}
              title="Toggle Cyber Sound Effects"
            >
              {soundEnabled ? <Volume2 className="h-3.5 w-3.5 text-blue-600" /> : <VolumeX className="h-3.5 w-3.5" />}
              <span>SFX {soundEnabled ? 'ON' : 'OFF'}</span>
            </button>
          </div>
        </div>

        {/* Quick Scenario Preset Selector Pills */}
        <div className="mt-5 pt-4 border-t border-slate-200">
          <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block mb-2 font-bold">
            ⚡ Quick-Test Scenarios (Instant Setup):
          </span>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
            {Object.entries(PRESETS).map(([key, p]) => {
              const isActive = activePresetKey === key;
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => applyPreset(key)}
                  className={`text-left p-3 rounded-2xl border transition-all duration-200 cursor-pointer flex flex-col justify-between ${
                    isActive
                      ? 'bg-white border-blue-500 shadow-md ring-2 ring-blue-500/20'
                      : 'bg-slate-50/80 border-slate-200 hover:bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="text-base">{p.icon}</span>
                    <span className={`text-[9px] px-1.5 py-0.5 rounded-md font-mono font-bold border ${p.badgeClass}`}>
                      {p.badge}
                    </span>
                  </div>
                  <span className={`text-xs font-bold truncate ${isActive ? 'text-slate-900' : 'text-slate-700'}`}>
                    {p.title}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono truncate">
                    {p.num_rows_affected.toLocaleString()} rows • {p.table_name.split('.')[1]}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Event Form */}
        <div className="lg:col-span-5 space-y-5">
          <form
            onSubmit={handleSubmit}
            className="bg-white border border-slate-200/90 rounded-3xl p-6 shadow-xs space-y-4"
          >
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <Sliders className="h-4 w-4 text-blue-600" />
                <span>Access Vector Parameters</span>
              </span>
              <span className="text-[11px] font-mono text-slate-400">Live JSON Payload</span>
            </div>

            {/* Principal Identity */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">User Identifier</label>
                <input
                  type="text"
                  value={formData.user_id}
                  onChange={(e) => setFormData({ ...formData, user_id: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 font-mono focus:bg-white focus:border-indigo-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">User Role</label>
                <select
                  value={formData.user_role}
                  onChange={(e) => setFormData({ ...formData, user_role: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-800 font-mono focus:bg-white focus:border-indigo-500 focus:outline-none cursor-pointer"
                >
                  <option value="engineer">engineer</option>
                  <option value="analyst">analyst</option>
                  <option value="contractor">contractor (High Risk)</option>
                  <option value="admin">admin</option>
                  <option value="intern">intern</option>
                </select>
              </div>
            </div>

            {/* Target Table & Action */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">Target Table</label>
                <select
                  value={formData.table_name}
                  onChange={(e) => setFormData({ ...formData, table_name: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-800 font-mono focus:bg-white focus:border-indigo-500 focus:outline-none cursor-pointer"
                >
                  <option value="public.products">public.products (Benign)</option>
                  <option value="analytics.sessions">analytics.sessions</option>
                  <option value="prod.medical_records">prod.medical_records (HIPAA)</option>
                  <option value="prod.credit_cards">prod.credit_cards (PCI-DSS)</option>
                  <option value="auth.tokens">auth.tokens (Sensitive)</option>
                </select>
              </div>
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">Operation</label>
                <select
                  value={formData.action}
                  onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-2 text-xs text-slate-800 font-mono focus:bg-white focus:border-indigo-500 focus:outline-none cursor-pointer"
                >
                  <option value="SELECT">SELECT</option>
                  <option value="EXPORT">EXPORT (Bulk)</option>
                  <option value="DOWNLOAD">DOWNLOAD</option>
                  <option value="DELETE">DELETE</option>
                </select>
              </div>
            </div>

            {/* Interactive Live Volume Slider */}
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-700 flex items-center gap-1.5">
                  <span>Volume:</span>
                  <span className="font-mono font-extrabold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-md">
                    {parseInt(formData.num_rows_affected, 10).toLocaleString()} rows
                  </span>
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-md border ${
                    formData.num_rows_affected > 50000
                      ? 'bg-rose-50 text-rose-700 border-rose-200'
                      : formData.num_rows_affected > 5000
                      ? 'bg-orange-50 text-orange-700 border-orange-200'
                      : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  }`}
                >
                  {formData.num_rows_affected > 50000
                    ? 'MASS EXFILTRATION'
                    : formData.num_rows_affected > 5000
                    ? 'ELEVATED VOLUME'
                    : 'NORMAL BASELINE'}
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="200000"
                step="50"
                value={formData.num_rows_affected}
                onChange={handleSliderChange}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500 font-medium">
                <span>1 row (Safe)</span>
                <span>10,000</span>
                <span>200,000 rows (Critical)</span>
              </div>
            </div>

            {/* Columns Accessed & Quick Toggles */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-[11px] font-bold text-slate-600">Columns Accessed</label>
                <span className="text-[10px] text-slate-500 font-medium">Click chips to toggle</span>
              </div>
              <input
                type="text"
                value={columnsInput}
                onChange={(e) => setColumnsInput(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 font-mono focus:bg-white focus:border-indigo-500 focus:outline-none mb-2"
                placeholder="col1, col2, col3..."
                required
              />
              {/* Quick column chips */}
              <div className="flex flex-wrap gap-1.5">
                {SUGGESTED_COLUMNS.map((col) => {
                  const isSelected = columnsInput.toLowerCase().includes(col.name.toLowerCase());
                  return (
                    <button
                      key={col.name}
                      type="button"
                      onClick={() => toggleColumnChip(col.name)}
                      className={`text-[10px] px-2.5 py-1 rounded-lg font-mono border transition-all cursor-pointer flex items-center gap-1 font-medium ${
                        isSelected
                          ? col.isHoney
                            ? 'bg-rose-100 text-rose-800 border-rose-300 font-bold'
                            : col.isPii
                            ? 'bg-orange-100 text-orange-800 border-orange-300 font-bold'
                            : 'bg-blue-100 text-blue-800 border-blue-300 font-bold'
                          : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      {col.isHoney && <span>🪤</span>}
                      <span>{col.name}</span>
                      {col.isPii && !col.isHoney && <span className="text-[8px] opacity-75">[PII]</span>}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Network Origin & Security Flags */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">Origin IP Address</label>
                <input
                  type="text"
                  value={formData.source_ip}
                  onChange={(e) => setFormData({ ...formData, source_ip: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 font-mono focus:bg-white focus:border-indigo-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="text-[11px] font-bold text-slate-600 block mb-1">Geo Location</label>
                <input
                  type="text"
                  value={formData.geo_location}
                  onChange={(e) => setFormData({ ...formData, geo_location: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 font-mono focus:bg-white focus:border-indigo-500 focus:outline-none"
                />
              </div>
            </div>

            {/* Flags */}
            <div className="flex items-center space-x-6 pt-1 text-xs font-medium">
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_vpn}
                  onChange={(e) => setFormData({ ...formData, is_vpn: e.target.checked })}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-slate-700">Masked VPN / Proxy Gateway</span>
              </label>
              <label className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_after_hours}
                  onChange={(e) => setFormData({ ...formData, is_after_hours: e.target.checked })}
                  className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-slate-700">After-Hours Operation</span>
              </label>
            </div>

            {/* Execute Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3.5 rounded-2xl font-bold text-sm tracking-wide transition-all shadow-md flex items-center justify-center space-x-2 cursor-pointer ${
                loading
                  ? 'bg-slate-300 text-slate-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white shadow-indigo-500/25 active:scale-[0.99]'
              }`}
            >
              {loading ? (
                <>
                  <div className="h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></div>
                  <span>Running ML Ensemble & Groq Explainer...</span>
                </>
              ) : (
                <>
                  <Zap className="h-4 w-4 text-amber-300" />
                  <span>ANALYZE ACCESS & LOG TO BLOCKCHAIN</span>
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="bg-rose-50 border border-rose-200 p-4 rounded-2xl text-xs text-rose-800 flex items-start space-x-2.5">
              <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Execution Error: </span>
                {error}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Live Telemetry, Speedometer Gauge & Formatted Forensic Report */}
        <div className="lg:col-span-7 space-y-5">
          {!result && !loading && (
            <div className="bg-white border border-dashed border-slate-300 rounded-3xl p-12 text-center space-y-3 shadow-xs">
              <div className="h-16 w-16 mx-auto rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
                <Compass className="h-8 w-8 animate-spin" style={{ animationDuration: '20s' }} />
              </div>
              <h3 className="text-base font-bold text-slate-800">Awaiting Telemetry Stream</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Choose a scenario preset or tweak custom parameters on the left, then click{' '}
                <strong className="text-slate-800">ANALYZE ACCESS</strong> to run the ML ensemble.
              </p>
            </div>
          )}

          {result && (
            <div className="space-y-5">
              {/* Post-Run Export Action Station */}
              <div className="bg-white border border-slate-200/90 rounded-3xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2.5 rounded-2xl bg-indigo-50 text-indigo-600 border border-indigo-100 shadow-2xs">
                    <FileDown className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-xs font-black text-slate-900 tracking-tight flex items-center gap-2">
                      <span>Forensic Audit Dossier Ready</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono font-bold">
                        100% VERIFIED
                      </span>
                    </h4>
                    <p className="text-[11px] text-slate-500 font-medium">
                      Export full analysis with identical formatting, coloring, honey token proofs & blockchain hashes.
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => printReportPDF(result, formData)}
                    className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-bold bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 shadow-2xs transition-all cursor-pointer active:scale-95"
                    title="Print or Save as Color PDF Document"
                  >
                    <Printer className="h-3.5 w-3.5 text-blue-600" />
                    <span>Export PDF</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => downloadReportDoc(result, formData)}
                    className="flex items-center space-x-1.5 px-4 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-600 hover:from-blue-700 hover:to-violet-700 text-white shadow-xs transition-all cursor-pointer active:scale-95"
                    title="Download Styled Microsoft Word .doc Document"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Download .DOC</span>
                  </button>
                </div>
              </div>

              {/* Score Banner with Light Speedometer Gauge */}
              <div
                className={`border rounded-3xl p-6 shadow-xs relative overflow-hidden transition-all ${scoreTheme.bg} ${scoreTheme.border}`}
              >
                <div className="flex flex-col sm:flex-row items-center justify-between gap-5">
                  {/* Circular Speedometer Gauge */}
                  <div className="flex items-center space-x-4">
                    <div className="relative w-24 h-24 shrink-0 flex items-center justify-center">
                      <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
                        {/* Light background track */}
                        <circle
                          cx="60"
                          cy="60"
                          r="48"
                          stroke="#e2e8f0"
                          strokeWidth="10"
                          fill="transparent"
                        />
                        {/* Dynamic Score Arc */}
                        <circle
                          cx="60"
                          cy="60"
                          r="48"
                          stroke={scoreTheme.stroke}
                          strokeWidth="10"
                          strokeDasharray="301.6"
                          strokeDashoffset={strokeDashoffset}
                          strokeLinecap="round"
                          fill="transparent"
                          className="transition-all duration-1000 ease-out"
                        />
                      </svg>
                      {/* Inner Score Label */}
                      <div className="absolute flex flex-col items-center justify-center">
                        <span className={`text-2xl font-black font-mono leading-none ${scoreTheme.text}`}>
                          {Math.round(score)}
                        </span>
                        <span className="text-[9px] text-slate-500 font-mono uppercase mt-0.5">/ 100</span>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs font-mono font-extrabold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${scoreTheme.border} ${scoreTheme.pill}`}>
                          {threatLevel} PRIORITY
                        </span>
                        {isHoneyTripped && (
                          <span className="text-[10px] px-2.5 py-0.5 rounded-full font-mono font-bold bg-rose-600 text-white">
                            🪤 HONEY TRAP
                          </span>
                        )}
                      </div>
                      <h3 className="text-base font-extrabold text-slate-900 mt-1.5">
                        {score >= 80
                          ? '🚨 Critical Threat Vector Identified'
                          : score >= 60
                          ? '⚠️ High Risk Anomaly Pattern'
                          : score >= 35
                          ? '🟡 Medium Risk Access Deviation'
                          : '🟢 Authorized Routine Access Verified'}
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5 font-mono">
                        Event Hash: {result.event?.event_id || 'Keccak-256'}
                      </p>
                    </div>
                  </div>

                  {/* Sub-Model Ensemble Breakdown */}
                  <div className="grid grid-cols-3 gap-2 text-center w-full sm:w-auto">
                    <div className="bg-white/90 p-2.5 rounded-xl border border-slate-200 shadow-2xs">
                      <span className="text-[10px] text-slate-500 uppercase block font-mono font-bold">Isolation</span>
                      <span className="text-xs font-bold font-mono text-blue-700">
                        {rawScores?.isolation_forest !== null && rawScores?.isolation_forest !== undefined
                          ? Number(rawScores.isolation_forest).toFixed(2)
                          : '0.05'}
                      </span>
                    </div>
                    <div className="bg-white/90 p-2.5 rounded-xl border border-slate-200 shadow-2xs">
                      <span className="text-[10px] text-slate-500 uppercase block font-mono font-bold">Autoencoder</span>
                      <span className="text-xs font-bold font-mono text-purple-700">
                        {rawScores?.autoencoder !== null && rawScores?.autoencoder !== undefined
                          ? Number(rawScores.autoencoder).toFixed(2)
                          : '0.00'}
                      </span>
                    </div>
                    <div className="bg-white/90 p-2.5 rounded-xl border border-slate-200 shadow-2xs">
                      <span className="text-[10px] text-slate-500 uppercase block font-mono font-bold">LSTM Prob</span>
                      <span className="text-xs font-bold font-mono text-indigo-700">
                        {rawScores?.lstm !== null && rawScores?.lstm !== undefined
                          ? Number(rawScores.lstm).toFixed(2)
                          : '0.00'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Contributing factors badges */}
                <div className="mt-4 pt-3.5 border-t border-slate-200/80">
                  <span className="text-[11px] font-mono text-slate-500 uppercase tracking-wider block mb-2 font-bold">
                    Key Telemetry Factors:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {factors.map((f, i) => (
                      <span
                        key={i}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-700 font-medium shadow-2xs"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Honey Token Proof-of-Theft Certificate */}
              {result.event?.proof_of_theft && (
                <div className="bg-gradient-to-br from-rose-50/90 via-purple-50/50 to-white border-2 border-rose-300 rounded-3xl p-6 shadow-sm space-y-3.5">
                  <div className="flex items-center justify-between pb-3 border-b border-rose-200">
                    <div className="flex items-center space-x-2.5">
                      <span className="text-2xl">🪤</span>
                      <div>
                        <h4 className="text-sm font-extrabold text-rose-950 uppercase tracking-wider flex items-center gap-2">
                          <span>Physical Proof of Theft Certified</span>
                          <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-rose-600 text-white font-mono font-bold">
                            100% MATCH
                          </span>
                        </h4>
                        <p className="text-[11px] text-rose-700 font-mono font-medium">
                          Certificate ID: {result.event.proof_of_theft.certificate_id}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-rose-800 font-mono border border-rose-200 px-3 py-1 rounded-xl bg-white font-bold shadow-2xs">
                      FRE Rule 902(13)&(14)
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                    <div className="bg-white p-3 rounded-2xl border border-rose-150 shadow-2xs">
                      <span className="text-slate-500 block text-[10px] uppercase font-bold">Attributed Suspect</span>
                      <span className="text-rose-700 font-bold text-sm">
                        {result.event.proof_of_theft.suspect_identity}
                      </span>
                    </div>
                    <div className="bg-white p-3 rounded-2xl border border-rose-150 shadow-2xs">
                      <span className="text-slate-500 block text-[10px] uppercase font-bold">Canary Decoy Asset</span>
                      <span className="text-purple-700 font-bold text-sm">
                        {result.event.proof_of_theft.canary_token_id}
                      </span>
                    </div>
                  </div>

                  <div className="bg-white p-3.5 rounded-2xl border border-rose-150 text-xs font-mono space-y-1.5 shadow-2xs">
                    <div className="text-[11px] text-slate-600 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <span className="text-slate-500">Watermark Digest (HMAC-SHA256):</span>
                      <span className="text-purple-700 break-all font-bold">
                        {result.event.proof_of_theft.watermark_hash}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-600 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                      <span className="text-slate-500">Theft Signature:</span>
                      <span className="text-emerald-700 break-all font-bold">
                        {result.event.proof_of_theft.cryptographic_proof_signature}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-rose-900 italic bg-white p-3 rounded-2xl border border-rose-150 leading-relaxed shadow-2xs font-medium">
                    "{result.event.proof_of_theft.forensic_summary}"
                  </p>
                </div>
              )}

              {/* Blockchain Immutable Receipt Banner */}
              {result.blockchain_log && (
                <div className="bg-gradient-to-r from-purple-50/70 via-indigo-50/50 to-white border border-purple-200 rounded-3xl p-4.5 flex items-center justify-between shadow-xs">
                  <div className="flex items-center space-x-3.5">
                    <div className="p-2.5 rounded-2xl bg-purple-100 text-purple-700 border border-purple-200 shadow-2xs">
                      <Database className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-xs font-extrabold text-slate-900 flex items-center gap-2">
                        <span>Tamper-Proof Receipt Anchored on Polygon PoS</span>
                        <CheckCircle2 className="h-3.5 w-3.5 text-purple-600" />
                      </div>
                      <div className="text-[11px] font-mono text-purple-800 mt-0.5">
                        Tx Hash: {result.blockchain_log.tx_hash.slice(0, 22)}... | Block #{result.blockchain_log.block_number}
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={onNavigateLedger}
                    className="text-xs text-purple-700 hover:text-purple-900 bg-white hover:bg-purple-50 px-3.5 py-2 rounded-xl border border-purple-200 transition-all flex items-center gap-1.5 cursor-pointer font-bold shadow-2xs"
                  >
                    <span>Verify Ledger</span>
                    <ExternalLink className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}

              {/* GenAI Forensic Report Card with FormattedReport */}
              <div className="bg-white border border-slate-200/90 rounded-3xl p-6 space-y-4 shadow-xs">
                <div className="flex items-center justify-between pb-3.5 border-b border-slate-100">
                  <div className="flex items-center space-x-2">
                    <Sparkles className="h-4 w-4 text-blue-600" />
                    <h3 className="text-sm font-extrabold text-slate-900 tracking-wide">
                      GenAI Threat Forensic Report
                    </h3>
                  </div>
                  <div className="flex items-center space-x-2 text-[11px] font-mono">
                    <span className="px-2.5 py-0.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-700">
                      Engine: {result.report?.generator || 'Groq (openai/gpt-oss-120b)'}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                      Confidence: {Math.round((result.report?.confidence || 0.95) * 100)}%
                    </span>
                  </div>
                </div>

                {/* Executive Briefing Callout */}
                <div className="bg-blue-50/70 p-4 rounded-2xl border border-blue-100">
                  <span className="text-[11px] font-mono font-bold text-blue-800 uppercase tracking-wider block mb-1.5">
                    📌 CISO & Leadership Executive Summary
                  </span>
                  <p className="text-xs text-slate-800 leading-relaxed font-sans font-medium">
                    {result.report?.executive_summary}
                  </p>
                </div>

                {/* Formatted Markdown Forensic Narrative */}
                <div className="bg-slate-50/70 p-5 rounded-2xl border border-slate-200 max-h-96 overflow-y-auto shadow-inner">
                  <FormattedReport content={result.report?.full_report} />
                </div>

                {/* Action Recommendations */}
                {result.report?.recommended_actions?.length > 0 && (
                  <div>
                    <span className="text-xs font-bold text-slate-700 uppercase tracking-wider block mb-2 font-mono">
                      Prioritized Containment Protocols:
                    </span>
                    <div className="space-y-2">
                      {result.report.recommended_actions.map((act, i) => (
                        <div
                          key={i}
                          className="text-xs bg-slate-50 p-3 rounded-2xl border border-slate-200 flex items-start gap-2.5"
                        >
                          <span className="h-4 w-4 rounded-full bg-blue-100 text-blue-700 font-mono text-[10px] flex items-center justify-center shrink-0 mt-0.5 font-bold">
                            {i + 1}
                          </span>
                          <span className="text-slate-800 leading-relaxed font-medium">{act}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Compliance Notes */}
                {result.report?.compliance_notes?.length > 0 && (
                  <div className="bg-amber-50/80 border border-amber-200 rounded-2xl p-4 text-xs text-amber-900 space-y-1.5">
                    <span className="font-bold block uppercase tracking-wider text-[10px] font-mono text-amber-800">
                      Regulatory & Compliance Mandates:
                    </span>
                    {result.report.compliance_notes.map((n, i) => (
                      <div key={i} className="flex items-start gap-2 font-medium">
                        <span className="text-amber-600 font-bold">•</span>
                        <span>{n}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
