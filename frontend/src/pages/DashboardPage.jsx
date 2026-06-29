import { useMemo } from "react";
import { Link } from "react-router-dom";
import { apiService } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import { toArray } from "../utils/formatters";
import PageHeader from "../components/common/PageHeader";
import LoadingState from "../components/common/LoadingState";
import ErrorState from "../components/common/ErrorState";
import VelocityTrendChart from "../components/charts/VelocityTrendChart";
import WorkflowPanel from "../components/dashboard/WorkflowPanel";

export default function DashboardPage() {
  const { data, loading, error, execute } = useAsync(async () => {
    const [usersRes, alertsRes, transactionsRes] = await Promise.all([
      apiService.getUsers({ limit: 500 }),
      apiService.getAlerts({ limit: 10 }),
      apiService.getTransactions(),
    ]);

    return {
      users: usersRes?.users || [],
      transactions: toArray(transactionsRes),
      alerts: toArray(alertsRes).sort((a, b) => Number(b.risk_score || 0) - Number(a.risk_score || 0)),
    };
  }, []);

  const summary = useMemo(() => {
    const users = data?.users || [];
    const alerts = data?.alerts || [];
    const transactions = data?.transactions || [];

    const activeAlerts = alerts.filter(a => String(a.status || "OPEN").toUpperCase() !== "CLOSED");
    const highRiskUsers = users.filter(u => Number(u.risk_score || 0) >= 0.75);
    
    const byMinute = transactions.reduce((acc, txn) => {
      const ts = new Date(txn.timestamp || txn.transfer_time || Date.now());
      const label = `${String(ts.getHours()).padStart(2, "0")}:${String(ts.getMinutes()).padStart(2, "0")}`;
      acc[label] = (acc[label] || 0) + 1;
      return acc;
    }, {});
    
    const velocityTrend = Object.entries(byMinute)
      .map(([label, count]) => ({ label, count }))
      .sort((a, b) => a.label.localeCompare(b.label));

    return {
      activeAlertsCount: activeAlerts.length,
      highRiskCount: highRiskUsers.length,
      monitoredCount: users.length || transactions.length,
      velocityTrend,
      topAlerts: activeAlerts.slice(0, 5)
    };
  }, [data]);

  if (loading) return <LoadingState label="Initializing Command Center..." />;
  if (error) return <ErrorState error={error} onRetry={execute} />;

  return (
    <div className="space-y-8 fade-in">
      <PageHeader 
        title="Command Center" 
        subtitle="Real-time multi-channel fraud intelligence and threat overview." 
      />

      {/* Hero Metrics */}
      <section className="grid gap-6 md:grid-cols-3">
        <div className="card p-8 flex flex-col justify-center border-t-4 border-t-red-500 shadow-panel">
          <p className="text-sm font-bold uppercase tracking-[0.15em] text-slate-400">Active Threats</p>
          <div className="mt-4 flex items-baseline gap-3">
            <span className="text-6xl font-extrabold text-red-400">{summary.activeAlertsCount}</span>
            <span className="text-lg font-medium text-red-400/70">Requiring review</span>
          </div>
        </div>

        <div className="card p-8 flex flex-col justify-center border-t-4 border-t-amber-500 shadow-panel">
          <p className="text-sm font-bold uppercase tracking-[0.15em] text-slate-400">High Risk Entities</p>
          <div className="mt-4 flex items-baseline gap-3">
            <span className="text-6xl font-extrabold text-amber-400">{summary.highRiskCount}</span>
            <span className="text-lg font-medium text-amber-400/70">Detected in graph</span>
          </div>
        </div>

        <div className="card p-8 flex flex-col justify-center border-t-4 border-t-emerald-500 shadow-panel">
          <p className="text-sm font-bold uppercase tracking-[0.15em] text-slate-400">Total Monitored</p>
          <div className="mt-4 flex items-baseline gap-3">
            <span className="text-6xl font-extrabold text-emerald-400">{summary.monitoredCount}</span>
            <span className="text-lg font-medium text-emerald-400/70">Active identities</span>
          </div>
        </div>
      </section>

      {/* Main Unified Chart */}
      <section className="card p-6 shadow-panel">
        <h3 className="text-lg font-bold text-slate-100 mb-6">Network Velocity Trend</h3>
        <VelocityTrendChart data={summary.velocityTrend || []} />
      </section>

      {/* Priority Action Items */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-100">Priority Action Items</h2>
          <Link to="/action-queue" className="btn-secondary">View All Items</Link>
        </div>
        
        <div className="grid gap-4">
          {summary.topAlerts.length === 0 ? (
            <div className="card p-8 text-center border border-dashed border-slate-700 bg-slate-900/30">
              <p className="text-lg font-bold text-slate-400">Zero active threats detected.</p>
            </div>
          ) : (
            summary.topAlerts.map(alert => (
              <Link key={alert.alert_id} to={`/users/${encodeURIComponent(alert.account_id)}`} className="card card-hover p-5 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="h-12 w-12 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
                    <span className="text-red-400 font-bold text-lg">!</span>
                  </div>
                  <div>
                    <h4 className="text-base font-bold text-slate-100">{alert.account_id}</h4>
                    <p className="text-sm text-slate-400 font-medium truncate max-w-xl">{alert.reason}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="rounded-full bg-red-500/20 px-3 py-1 text-xs font-bold text-red-300 border border-red-500/30">
                    RISK {Number(alert.risk_score || 0).toFixed(2)}
                  </span>
                  <span className="text-cyan-400 font-bold">→</span >
                </div>
              </Link>
            ))
          )}
        </div>
      </section>
      
      {/* Retain the workflow panel for model training/DB seeding */}
      <div className="mt-12">
         <WorkflowPanel onCompleted={execute} />
      </div>
    </div>
  );
}
