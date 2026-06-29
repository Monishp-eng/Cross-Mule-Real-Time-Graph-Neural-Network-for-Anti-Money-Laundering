import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import { apiService } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import PageHeader from "../components/common/PageHeader";
import LoadingState from "../components/common/LoadingState";
import ErrorState from "../components/common/ErrorState";
import NetworkGraph from "../components/graph/NetworkGraph";

function riskTone(score) {
  const value = Number(score || 0);
  if (value >= 0.75) return "text-red-300";
  if (value >= 0.45) return "text-amber-300";
  return "text-emerald-300";
}

export default function UserRiskProfilePage() {
  const { userId = "" } = useParams();

  const { data, loading, error, execute } = useAsync(async () => {
    if (!userId) return null;
    return apiService.getUserProfile(userId);
  }, [userId]);

  const history = useMemo(() => data?.transaction_history || [], [data]);
  const breakdown = data?.risk_breakdown || {};
  const graphLinks = data?.graph?.links || [];
  const graphWidgetData = useMemo(() => {
    const baseNodes = Array.isArray(data?.graph?.nodes) ? [...data.graph.nodes] : [];
    const links = Array.isArray(data?.graph?.links) ? data.graph.links : [];
    const nodeIds = new Set(baseNodes.map((node) => String(node?.id)));

    for (const link of links) {
      const source = String(link?.source || "");
      const target = String(link?.target || "");
      if (source && !nodeIds.has(source)) {
        baseNodes.push({ id: source, label: source, type: "linked", risk_score: Number(link?.risk_score || 0) });
        nodeIds.add(source);
      }
      if (target && !nodeIds.has(target)) {
        baseNodes.push({ id: target, label: target, type: "linked", risk_score: Number(link?.risk_score || 0) });
        nodeIds.add(target);
      }
    }

    return { nodes: baseNodes, links };
  }, [data]);
  const patterns = data?.pattern_indicators || {};
  const jurisdictions = data?.jurisdiction_indicators || [];
  const fundFlow = data?.flow_of_funds || [];

  if (loading) return <LoadingState label="Loading user risk profile..." />;
  if (error) return <ErrorState error={error} onRetry={execute} />;
  if (!data) return null;

  return (
    <div className="space-y-8">
      <PageHeader
        title={`Risk Profile: ${data.user_id}`}
        subtitle="Analyst view of user risk, transactions, and graph-linked behavior"
        action={<Link to="/" className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm">Back to Dashboard</Link>}
      />

      <section className="grid gap-6 md:grid-cols-3">
        <div className="card p-6 shadow-panel">
          <p className="text-sm uppercase tracking-[0.15em] font-semibold text-muted">Risk Score</p>
          <p className={`mt-3 text-4xl font-extrabold ${riskTone(data.risk_score)}`}>{Number(data.risk_score || 0).toFixed(2)}</p>
        </div>
        <div className="card p-6 shadow-panel">
          <p className="text-sm uppercase tracking-[0.15em] font-semibold text-muted">Risk Level</p>
          <p className="mt-3 text-4xl font-extrabold text-ink">{String(data.risk_level || "GREEN").toUpperCase()}</p>
        </div>
        <div className="card p-6 shadow-panel">
          <p className="text-sm uppercase tracking-[0.15em] font-semibold text-muted">Current Status</p>
          <p className="mt-3 text-4xl font-extrabold text-ink">{String(data.current_status || "ALLOW").toUpperCase()}</p>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6 shadow-panel">
          <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Risk Score Breakdown</h3>
          <div className="mt-4 space-y-3 text-base">
            {Object.keys(breakdown).length === 0 ? (
              <p className="text-slate-400">No breakdown available.</p>
            ) : (
              Object.entries(breakdown).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between border-b border-slate-800/70 py-2">
                  <span className="font-medium text-slate-300">{key}</span>
                  <span className="font-bold text-slate-100">{String(value)}</span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card p-6 shadow-panel">
          <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Flagging Explanation</h3>
          <div className="mt-4 space-y-4 text-base">
            {(data.explanation || []).length === 0 ? (
              <p className="text-slate-400">No explanation available.</p>
            ) : (
              (data.explanation || []).map((reason) => (
                <p key={reason} className="rounded-lg border border-slate-700/70 bg-slate-900/70 p-4 text-slate-200 shadow-sm leading-relaxed">
                  {reason}
                </p>
              ))
            )}
          </div>
        </div>
      </section>

      <section className="card p-6 shadow-panel">
        <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Graph / Network Connections</h3>
        <p className="mt-2 text-sm text-muted">Mule links derived from graph analytics</p>
        <div className="mt-4 space-y-4 text-base">
          {graphLinks.length === 0 ? (
            <p className="text-slate-400">No connected graph links found.</p>
          ) : (
            graphLinks.slice(0, 20).map((link, idx) => (
              <div key={`${link.source}-${link.target}-${idx}`} className="rounded-lg border border-slate-700/70 bg-slate-900/70 p-4 text-slate-200 font-medium shadow-sm">
                {String(link.source)} {"->"} {String(link.target)} (risk {Number(link.risk_score || 0).toFixed(2)})
              </div>
            ))
          )}
        </div>
      </section>

      <section className="card p-6 shadow-panel">
        <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Interactive Account Network</h3>
        <p className="mt-2 text-sm text-muted">Drag and inspect linked entities and suspicious transaction edges for this account.</p>
        <div className="mt-4">
          <NetworkGraph graphData={graphWidgetData} />
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="card p-6 shadow-panel">
          <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Flow of Funds</h3>
          <p className="mt-2 text-sm text-muted">Source {"->"} intermediate {"->"} destination paths linked to this account.</p>
          <div className="mt-4 space-y-4 text-base">
            {fundFlow.length === 0 ? (
              <p className="text-slate-400">No fund flow paths available.</p>
            ) : (
              fundFlow.slice(0, 20).map((flow, idx) => (
                <div key={`${flow.source}-${flow.destination}-${idx}`} className="rounded-lg border border-slate-700/70 bg-slate-900/70 p-4 text-slate-200 shadow-sm leading-relaxed">
                  <span className="font-bold">{String(flow.source)}</span> {"->"} <span className="font-bold">{String(flow.intermediate)}</span> {"->"} <span className="font-bold">{String(flow.destination)}</span>
                  <p className="mt-1 text-sm font-medium text-slate-400">Risk {Number(flow.risk_score || 0).toFixed(2)}</p>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="card p-6 shadow-panel">
          <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Pattern Detection</h3>
          <p className="mt-2 text-sm text-muted">Structuring, fragmentation, nesting, and unusual routing indicators.</p>
          <div className="mt-4 space-y-4 text-base">
            {Object.keys(patterns).length === 0 ? (
              <p className="text-slate-400">No pattern indicators available.</p>
            ) : (
              Object.entries(patterns).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between rounded-lg border border-slate-700/70 bg-slate-900/70 p-4 shadow-sm">
                  <span className="font-semibold text-slate-200">{key}</span>
                  <span className={value ? "font-bold text-red-300" : "font-bold text-emerald-300"}>{value ? "Detected" : "Not detected"}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      <section className="card p-6 shadow-panel">
        <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Jurisdiction Risk Indicators</h3>
        <p className="mt-2 text-sm text-muted">Country-level activity concentration used in compliance risk review.</p>
        <div className="mt-4 space-y-4 text-base">
          {jurisdictions.length === 0 ? (
            <p className="text-slate-400">No jurisdiction indicators available.</p>
          ) : (
            jurisdictions.map((item) => (
              <div key={item.country} className="flex items-center justify-between rounded-lg border border-slate-700/70 bg-slate-900/70 p-4 shadow-sm">
                <span className="font-bold text-slate-200">{item.country}</span>
                <span className="font-medium text-slate-300">{Number(item.count || 0)} events</span>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="card overflow-x-auto shadow-panel">
        <div className="border-b border-slate-700/60 px-6 py-5">
          <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Transaction History</h3>
        </div>
        <table className="min-w-full text-base">
          <thead className="bg-slate-900/80 text-left text-sm font-semibold uppercase tracking-[0.15em] text-muted">
            <tr>
              <th className="px-6 py-4">Transaction ID</th>
              <th className="px-6 py-4">Amount</th>
              <th className="px-6 py-4">Risk</th>
              <th className="px-6 py-4">Decision</th>
              <th className="px-6 py-4">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {history.length === 0 ? (
              <tr>
                <td className="px-6 py-6 text-center text-muted" colSpan={5}>No transactions found for this user.</td>
              </tr>
            ) : (
              history.map((row) => (
                <tr key={row.transaction_id || row.timestamp} className="border-t border-slate-800/80 odd:bg-slate-950/20">
                  <td className="px-6 py-4 font-medium text-slate-100">{row.transaction_id || "-"}</td>
                  <td className="px-6 py-4 font-medium text-slate-300">{Number(row.amount || 0).toFixed(2)} {row.currency || "INR"}</td>
                  <td className={`px-6 py-4 font-bold ${riskTone(row.risk_score)}`}>{Number(row.risk_score || 0).toFixed(2)}</td>
                  <td className="px-6 py-4 font-medium text-slate-300">{String(row.decision || "ALLOW").toUpperCase()}</td>
                  <td className="px-6 py-4 text-sm text-slate-400">{row.timestamp || "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
