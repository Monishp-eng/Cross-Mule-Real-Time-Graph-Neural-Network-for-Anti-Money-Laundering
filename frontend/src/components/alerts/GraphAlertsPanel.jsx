function formatPath(path) {
  return Array.isArray(path?.node_path) ? path.node_path.join(" -> ") : "-";
}

export default function GraphAlertsPanel({ pathAlerts = [], clusterAlerts = [] }) {
  return (
    <section className="grid gap-6 xl:grid-cols-2">
      <div className="card p-6 shadow-panel">
        <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Flagged Paths</h3>
        <p className="mt-2 text-sm text-muted">Multi-hop high-velocity chains from graph analytics</p>
        <div className="mt-4 space-y-4 text-base">
          {pathAlerts.length === 0 ? (
            <p className="text-slate-400">No flagged paths right now.</p>
          ) : (
            pathAlerts.slice(0, 8).map((alert) => (
              <div key={alert.alert_id} className="rounded-2xl border border-red-900/60 bg-red-500/10 p-5 shadow-sm">
                <p className="font-bold text-red-200">{alert.alert_id}</p>
                <p className="mt-1 text-sm font-medium text-slate-100">{formatPath(alert)}</p>
                <p className="mt-1 text-sm text-slate-300">{alert.reason}</p>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="card p-6 shadow-panel">
        <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Cluster Alerts</h3>
        <p className="mt-2 text-sm text-muted">High-risk mule ring groups detected from embeddings</p>
        <div className="mt-4 space-y-4 text-base">
          {clusterAlerts.length === 0 ? (
            <p className="text-slate-400">No high-risk clusters right now.</p>
          ) : (
            clusterAlerts.slice(0, 8).map((alert) => (
              <div key={alert.alert_id} className="rounded-2xl border border-amber-800/60 bg-amber-400/10 p-5 shadow-sm">
                <p className="font-bold text-amber-200">{alert.alert_id}</p>
                <p className="mt-1 text-sm font-medium text-slate-100">Members: {Array.isArray(alert.members) ? alert.members.join(", ") : "-"}</p>
                <p className="mt-1 text-sm text-slate-300">{alert.reason}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  );
}
