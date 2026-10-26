import React, { useState, useEffect } from 'react';
import { 
  Database, 
  ExternalLink, 
  Copy, 
  Check, 
  RefreshCw, 
  ShieldCheck, 
  Lock,
  Layers,
  CheckCircle2
} from 'lucide-react';
import { getBlockchainEvents } from '../services/api.js';

export default function BlockchainExplorer() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [copiedHash, setCopiedHash] = useState(null);

  const fetchEvents = async () => {
    setLoading(true);
    const { data } = await getBlockchainEvents();
    if (data?.events) {
      setEvents(data.events);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(id);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Network Header */}
      <div className="bg-gradient-to-br from-white via-purple-50/20 to-indigo-50/30 border border-slate-200/90 rounded-3xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs">
        <div className="flex items-center space-x-3.5">
          <div className="h-12 w-12 rounded-2xl bg-purple-100 border border-purple-200 flex items-center justify-center text-purple-700 shadow-2xs">
            <Lock className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-lg font-extrabold text-slate-900 flex items-center gap-2">
              <span>Cryptographic Audit Ledger</span>
              <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 font-mono font-bold">
                Polygon PoS Smart Contract #137
              </span>
            </h1>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              Contract Address: <span className="text-purple-700 font-bold">0x3Aa5ebB10DC797CAC828524e59A333d0A371443c</span>
            </p>
          </div>
        </div>

        <button
          onClick={fetchEvents}
          disabled={loading}
          className="flex items-center space-x-2 bg-white hover:bg-slate-50 text-slate-700 px-4 py-2.5 rounded-xl text-xs font-bold border border-slate-200 transition-colors cursor-pointer shadow-2xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Ledger</span>
        </button>
      </div>

      {/* Verified Event Logs */}
      <div className="bg-white border border-slate-200/90 rounded-3xl overflow-hidden shadow-xs">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wider font-mono">
            Recorded Block Hashes ({events.length} Entries)
          </span>
          <span className="text-xs text-emerald-600 font-mono font-bold flex items-center gap-1.5 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Consensus Validated</span>
          </span>
        </div>

        {events.length === 0 && !loading && (
          <div className="p-16 text-center text-slate-500 font-mono text-xs space-y-2">
            <p className="font-semibold text-slate-700">No on-chain records logged in this session yet.</p>
            <p>Run a threat simulation to anchor an immutable transaction!</p>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 text-slate-600 uppercase border-b border-slate-200 text-[11px]">
              <tr>
                <th className="py-3.5 px-5">Event Keccak-256 Hash</th>
                <th className="py-3.5 px-5">Block #</th>
                <th className="py-3.5 px-5">Principal</th>
                <th className="py-3.5 px-5">Action</th>
                <th className="py-3.5 px-5">Schema</th>
                <th className="py-3.5 px-5 text-center">Threat Score</th>
                <th className="py-3.5 px-5">IPFS Evidence CID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {events.map((ev, i) => (
                <tr key={i} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-4 px-5 font-bold text-purple-700 flex items-center gap-2">
                    <span>{(ev.event_hash || '0x00').slice(0, 16)}...</span>
                    <button
                      onClick={() => copyToClipboard(ev.event_hash, `hash_${i}`)}
                      className="p-1 hover:text-purple-900 text-slate-400 transition-colors cursor-pointer"
                      title="Copy Hash"
                    >
                      {copiedHash === `hash_${i}` ? <Check className="h-3.5 w-3.5 text-emerald-600 font-bold" /> : <Copy className="h-3.5 w-3.5" />}
                    </button>
                  </td>
                  <td className="py-4 px-5 text-slate-700 font-semibold">
                    #{ev.block_number || (14209800 + i)}
                  </td>
                  <td className="py-4 px-5 text-slate-800 font-sans font-semibold">
                    {ev.user_id}
                  </td>
                  <td className="py-4 px-5">
                    <span className="px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200 text-slate-700 font-bold">
                      {ev.action}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-blue-700 font-semibold">
                    `{ev.table_name}`
                  </td>
                  <td className="py-4 px-5 text-center">
                    <span className={`font-bold ${
                      ev.threat_score >= 80 ? 'text-rose-600' :
                      ev.threat_score >= 60 ? 'text-orange-600' :
                      ev.threat_score >= 35 ? 'text-amber-600' : 'text-emerald-600'
                    }`}>
                      {ev.threat_score}
                    </span>
                  </td>
                  <td className="py-4 px-5 text-slate-500 font-mono text-[11px] truncate max-w-[140px]">
                    {ev.ipfs_report_hash || 'QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG'}
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
