import { useState } from "react";
import { Link } from "react-router-dom";
import { apiService } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import { toArray } from "../utils/formatters";
import PageHeader from "../components/common/PageHeader";
import LoadingState from "../components/common/LoadingState";
import ErrorState from "../components/common/ErrorState";

function riskBadge(score) {
  const value = Number(score || 0);
  if (value >= 0.75) return <span className="rounded-full bg-red-500/20 px-3 py-1 text-xs font-bold text-red-300 border border-red-500/30">CRITICAL</span>;
  if (value >= 0.45) return <span className="rounded-full bg-amber-500/20 px-3 py-1 text-xs font-bold text-amber-300 border border-amber-500/30">ELEVATED</span>;
  return <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-bold text-emerald-300 border border-emerald-500/30">MONITORING</span>;
}

export default function ActionQueuePage() {
  const [filter, setFilter] = useState("ALL");

  const { data, loading, error, execute } = useAsync(async () => {
    const [alertsRes, txRes] = await Promise.all([
      apiService.getAlerts({ limit: 100 }),
      apiService.getTransactions()
    ]);
    return {
      alerts: toArray(alertsRes).sort((a, b) => Number(b.risk_score || 0) - Number(a.risk_score || 0)),
      transactions: toArray(txRes)
    };
  }, []);

  const handleAction = async (alertId, decision) => {
    try {
      await apiService.actionAlert(alertId, decision);
      execute();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) return <LoadingState label="Loading Action Queue..." />;
  if (error) return <ErrorState error={error} onRetry={execute} />;

  const alerts = data?.alerts || [];
  const displayAlerts = filter === "ALL" ? alerts : alerts.filter(a => String(a.status || "OPEN").toUpperCase() === filter);

  return (
    <div className="space-y-8 fade-in">
      <PageHeader 
        title="Action Queue" 
        subtitle="Review prioritized alerts, resolve false positives, and block active threats." 
        action={
          <div className="flex gap-2 bg-slate-900/60 p-1 rounded-xl border border-slate-700/50 backdrop-blur-md">
            {["ALL", "OPEN", "CLOSED"].map(f => (
              <button 
                key={f}
                className={`px-4 py-2 rounded-lg text-sm font-semibold transition ${filter === f ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-glow' : 'text-slate-400 hover:text-slate-200'}`}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
        }
      />

      <div className="grid gap-6">
        {displayAlerts.length === 0 ? (
          <div className="card p-12 text-center shadow-panel">
            <p className="text-xl font-bold text-slate-300">No alerts require action.</p>
            <p className="mt-2 text-slate-500">Your queue is clear.</p>
          </div>
        ) : (
          displayAlerts.map(alert => (
            <div key={alert.alert_id} className="card card-hover p-6">
              <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-6">
                
                {/* Left: Identity & Badges */}
                <div className="flex items-center gap-5 min-w-[250px]">
                  <div className="flex-shrink-0">
                    <div className="h-14 w-14 rounded-full bg-slate-800/80 border border-slate-700/60 flex items-center justify-center shadow-sm">
                      <span className="text-xl font-bold text-slate-300">
                        {String(alert.account_id || "?").charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-slate-100">{alert.account_id || "Unknown Account"}</h3>
                    <div className="mt-2 flex items-center gap-2">
                      {riskBadge(alert.risk_score)}
                      <span className="text-sm text-slate-400 font-medium ml-1">{new Date(alert.timestamp).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                {/* Middle: Reasoning */}
                <div className="flex-1 max-w-3xl px-0 xl:px-8 border-l-0 xl:border-l border-slate-700/50">
                  <p className="text-sm font-bold uppercase tracking-[0.15em] text-cyan-400 mb-2">
                    {String(alert.alert_type || "SUSPICIOUS ACTIVITY").replace(/_/g, " ")}
                  </p>
                  <p className="text-base text-slate-300 leading-relaxed font-medium">
                    {alert.reason || "Detected unusual behavioral topology associated with mule networks."}
                  </p>
                </div>

                {/* Right: Actions */}
                <div className="flex flex-wrap items-center gap-3 justify-end min-w-[280px]">
                  <Link to={`/users/${encodeURIComponent(alert.account_id)}`} className="btn-secondary">
                    Investigate
                  </Link>
                  
                  {String(alert.status || "OPEN").toUpperCase() !== "CLOSED" ? (
                    <>
                      <button onClick={() => handleAction(alert.alert_id, "ALLOW")} className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-5 py-2 text-sm font-semibold text-emerald-300 transition hover:bg-emerald-500/20 hover:shadow-glow">
                        Safe
                      </button>
                      <button onClick={() => handleAction(alert.alert_id, "BLOCK")} className="rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-2 text-sm font-semibold text-red-300 transition hover:bg-red-500/20 hover:shadow-glow">
                        Block
                      </button>
                    </>
                  ) : (
                    <span className="px-5 py-2 text-sm font-bold text-slate-500 border border-slate-700/50 rounded-xl bg-slate-800/30">RESOLVED</span>
                  )}
                </div>

              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
