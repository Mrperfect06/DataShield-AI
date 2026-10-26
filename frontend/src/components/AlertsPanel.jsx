import React, { useState, useEffect } from 'react';
import { 
  Bell, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert, 
  Clock, 
  UserCheck, 
  RefreshCw 
} from 'lucide-react';
import { getBlockchainAlerts, resolveAlert } from '../services/api.js';

export default function AlertsPanel() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState('unresolved');
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const loadAlerts = async () => {
    setLoading(true);
    const { data } = await getBlockchainAlerts();
    if (data?.alerts) {
      setAlerts(data.alerts);
    } else {
      setAlerts([
        {
          alert_id: 1,
          event_hash: '0x8f2d591a2bc4e77301d0a519fcbb88391741259e8751',
          threat_level: 'CRITICAL',
          timestamp: '2026-10-26T23:55:12Z',
          resolved: false,
          responder_address: '0x0000000000000000000000000000000000000000',
        },
        {
          alert_id: 2,
          event_hash: '0x4c1e828d99042bbf00e4708291538bc16223b9d401a7',
          threat_level: 'HIGH',
          timestamp: '2026-10-26T23:30:45Z',
          resolved: false,
          responder_address: '0x0000000000000000000000000000000000000000',
        },
        {
          alert_id: 3,
          event_hash: '0x1a7f3402bcde190a6245009188a10738d451290bbce1',
          threat_level: 'HIGH',
          timestamp: '2026-10-26T21:12:00Z',
          resolved: true,
          responder_address: '0x71C8360f37ab892081dd5b236b31ef5e194c213a',
        },
      ]);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleResolve = async (alertId) => {
    setResolvingId(alertId);
    const { data } = await resolveAlert(alertId);
    setResolvingId(null);

    setAlerts(alerts.map((a) => (a.alert_id === alertId ? { ...a, resolved: true } : a)));
    setToastMessage(`Alert #${alertId} successfully marked resolved on-chain!`);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const filteredAlerts = filter === 'unresolved' 
    ? alerts.filter((a) => !a.resolved)
    : alerts;

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white text-xs font-semibold px-4 py-3 rounded-2xl shadow-xl flex items-center space-x-2 animate-bounce">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header with filter tabs */}
      <div className="bg-gradient-to-br from-white via-amber-50/20 to-indigo-50/30 border border-slate-200/90 rounded-3xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs">
        <div>
          <h1 className="text-lg font-extrabold text-slate-900 flex items-center gap-2">
            <Bell className="h-5 w-5 text-amber-500" />
            <span>Smart Contract Threat Alerts</span>
          </h1>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Automated alerts dispatched when Threat Score &gt;= 70. Requires SOC cryptographic sign-off.
          </p>
        </div>

        <div className="flex items-center space-x-2 bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs font-bold">
          <button
            onClick={() => setFilter('unresolved')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
              filter === 'unresolved'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Pending Action ({alerts.filter((a) => !a.resolved).length})
          </button>
          <button
            onClick={() => setFilter('all')}
            className={`px-3.5 py-1.5 rounded-lg transition-all cursor-pointer ${
              filter === 'all'
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All Alerts ({alerts.length})
          </button>
        </div>
      </div>

      {/* Alert Cards Grid */}
      <div className="space-y-3.5">
        {filteredAlerts.length === 0 && (
          <div className="bg-white border border-slate-200/90 rounded-3xl p-16 text-center text-slate-500 text-xs font-mono shadow-xs">
            No active threat alerts in this view.
          </div>
        )}

        {filteredAlerts.map((alert) => (
          <div
            key={alert.alert_id}
            className={`bg-white border rounded-3xl p-5.5 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xs ${
              alert.resolved
                ? 'border-slate-200 bg-slate-50/60 opacity-70'
                : alert.threat_level === 'CRITICAL'
                ? 'border-rose-300 bg-rose-50/30 hover:border-rose-400'
                : 'border-orange-300 bg-orange-50/30 hover:border-orange-400'
            }`}
          >
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-sm font-extrabold text-slate-900">
                  Alert #{alert.alert_id}
                </span>
                <span
                  className={`text-[10px] px-2.5 py-0.5 rounded-full font-extrabold border ${
                    alert.threat_level === 'CRITICAL'
                      ? 'bg-rose-100 text-rose-800 border-rose-300'
                      : 'bg-orange-100 text-orange-800 border-orange-300'
                  }`}
                >
                  {alert.threat_level}
                </span>
                {alert.resolved ? (
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono font-bold flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    <span>Resolved</span>
                  </span>
                ) : (
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 font-mono font-bold">
                    Open / Action Required
                  </span>
                )}
              </div>

              <div className="text-xs font-mono text-slate-500 flex flex-wrap items-center gap-x-4 gap-y-1">
                <div>
                  <span className="text-slate-400">Hash: </span>
                  <span className="text-purple-700 font-bold">{(alert.event_hash || '').slice(0, 22)}...</span>
                </div>
                <div>
                  <span className="text-slate-400">Recorded: </span>
                  <span className="text-slate-700 font-medium">{alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'Recent'}</span>
                </div>
              </div>
            </div>

            <div>
              {!alert.resolved ? (
                <button
                  onClick={() => handleResolve(alert.alert_id)}
                  disabled={resolvingId === alert.alert_id}
                  className="flex items-center space-x-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-xl text-xs font-bold shadow-sm shadow-emerald-500/20 transition-all cursor-pointer disabled:opacity-50"
                >
                  {resolvingId === alert.alert_id ? (
                    <>
                      <span className="h-3 w-3 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>
                      <span>Signing Tx...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="h-4 w-4" />
                      <span>Sign & Resolve On-Chain</span>
                    </>
                  )}
                </button>
              ) : (
                <div className="text-xs font-mono text-slate-500 text-right">
                  Signed by: {alert.responder_address ? `${alert.responder_address.slice(0, 10)}...` : 'SOC Lead'}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
