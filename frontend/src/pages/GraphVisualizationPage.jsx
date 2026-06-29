import { apiService } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import PageHeader from "../components/common/PageHeader";
import LoadingState from "../components/common/LoadingState";
import ErrorState from "../components/common/ErrorState";
import NetworkGraph from "../components/graph/NetworkGraph";

export default function GraphVisualizationPage() {
  const { data, loading, error, execute } = useAsync(async () => apiService.getGraphData(), []);

  if (loading) return <LoadingState label="Loading network graph..." />;
  if (error) return <ErrorState error={error} onRetry={execute} />;

  const clusters = Array.isArray(data?.clusters) ? data.clusters : [];
  const explanations = Array.isArray(data?.explanations) ? data.explanations : [];
  const flaggedPaths = Array.isArray(data?.flagged_paths) ? data.flagged_paths : [];

  return (
    <div className="space-y-5">
      <PageHeader
        title="Graph Visualization"
        subtitle="Network map of users and transactions with suspicious links highlighted"
      />

      <section className="grid gap-3 md:grid-cols-3">
        <div className="card p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-muted">Clusters</p>
          <p className="mt-2 text-2xl font-bold text-ink">{clusters.length}</p>
          <p className="mt-1 text-xs text-muted">High-risk groups detected in the current graph snapshot.</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-muted">Explainable nodes</p>
          <p className="mt-2 text-2xl font-bold text-ink">{explanations.length}</p>
          <p className="mt-1 text-xs text-muted">Flagged accounts with generated reason sets.</p>
        </div>
        <div className="card p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-muted">Suspicious paths</p>
          <p className="mt-2 text-2xl font-bold text-ink">{flaggedPaths.length}</p>
          <p className="mt-1 text-xs text-muted">Rapid movement chains requiring investigation.</p>
        </div>
      </section>

      <NetworkGraph graphData={data} />

      <div className="grid gap-4 xl:grid-cols-3">
        <section className="card p-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">Mule Rings</h3>
          <p className="mt-1 text-xs text-muted">Clusters of high-risk accounts inferred from GraphSAGE embeddings</p>
          <div className="mt-3 space-y-2 text-sm">
            {clusters.length === 0 ? (
              <p className="text-slate-400">No high-risk clusters detected.</p>
            ) : (
              clusters.slice(0, 6).map((cluster) => (
                <div key={cluster.cluster_id} className="rounded-lg border border-slate-700 bg-slate-900/40 p-2">
                  <p className="font-medium text-slate-100">{cluster.cluster_id}</p>
                  <p className="text-xs text-slate-300">Average risk: {(cluster.average_risk_score ?? 0).toFixed(2)}</p>
                  <p className="text-xs text-slate-400">Accounts: {(cluster.account_ids || []).join(", ") || "-"}</p>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="card p-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">Explainability</h3>
          <p className="mt-1 text-xs text-muted">Reasons generated for flagged entities</p>
          <div className="mt-3 space-y-2 text-sm">
            {explanations.length === 0 ? (
              <p className="text-slate-400">No flagged entities yet.</p>
            ) : (
              explanations.slice(0, 8).map((row) => (
                <div key={row.node_id} className="rounded-lg border border-slate-700 bg-slate-900/40 p-2">
                  <p className="font-medium text-slate-100">{row.node_id} • Risk {(row.risk_score ?? 0).toFixed(2)}</p>
                  <p className="text-xs text-slate-300">{Array.isArray(row.reasons) ? row.reasons.join(", ") : "No reasons"}</p>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="card p-4">
          <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-slate-300">Suspicious Paths</h3>
          <p className="mt-1 text-xs text-muted">Rapid multi-hop movement with increasing cumulative risk</p>
          <div className="mt-3 space-y-2 text-sm">
            {flaggedPaths.length === 0 ? (
              <p className="text-slate-400">No suspicious paths detected.</p>
            ) : (
              flaggedPaths.slice(0, 6).map((path) => (
                <div key={path.path_id} className="rounded-lg border border-slate-700 bg-slate-900/40 p-2">
                  <p className="font-medium text-slate-100">{path.path_id} • Hops {path.hop_count}</p>
                  <p className="text-xs text-slate-300">{Array.isArray(path.node_path) ? path.node_path.join(" → ") : "-"}</p>
                  <p className="text-xs text-slate-400">
                    Cum risk {(path.cumulative_risk ?? 0).toFixed(2)} | Max gap {(path.max_gap_minutes ?? 0).toFixed(2)}m
                  </p>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
