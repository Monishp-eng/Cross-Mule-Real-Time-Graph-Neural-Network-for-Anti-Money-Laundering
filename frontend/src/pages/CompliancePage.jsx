import { useState } from "react";
import { apiService } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import PageHeader from "../components/common/PageHeader";
import LoadingState from "../components/common/LoadingState";
import ErrorState from "../components/common/ErrorState";

export default function CompliancePage() {
  const [sarReport, setSarReport] = useState(null);

  const { data, loading, error, execute } = useAsync(async () => {
    const summary = await apiService.getComplianceRiskSummary(300);
    return summary;
  }, []);

  const loadSar = async () => {
    const sar = await apiService.getComplianceSar(100);
    setSarReport(sar);
  };

  if (loading) return <LoadingState label="Loading compliance workspace..." />;
  if (error) return <ErrorState error={error} onRetry={execute} />;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Compliance & Reporting"
        subtitle="Generate regulator-ready suspicious activity and risk summary reports"
        action={
          <div className="flex gap-2">
            <button type="button" className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm" onClick={execute}>Refresh Summary</button>
            <button type="button" className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm" onClick={loadSar}>Generate SAR</button>
          </div>
        }
      />

      <section className="grid gap-6 md:grid-cols-3">
        <div className="card p-6 shadow-panel">
          <p className="text-sm uppercase tracking-[0.15em] font-semibold text-muted">Accounts Covered</p>
          <p className="mt-3 text-4xl font-extrabold text-ink">{Number(data?.accounts_total || 0)}</p>
        </div>
        <div className="card p-6 shadow-panel">
          <p className="text-sm uppercase tracking-[0.15em] font-semibold text-muted">High Risk</p>
          <p className="mt-3 text-4xl font-extrabold text-red-300">{Number(data?.risk_distribution?.high || 0)}</p>
        </div>
        <div className="card p-6 shadow-panel">
          <p className="text-sm uppercase tracking-[0.15em] font-semibold text-muted">Medium Risk</p>
          <p className="mt-3 text-4xl font-extrabold text-amber-300">{Number(data?.risk_distribution?.medium || 0)}</p>
        </div>
      </section>

      <section className="card p-6 shadow-panel">
        <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Top Risk Accounts</h3>
        <div className="mt-4 space-y-4 text-base">
          {(data?.top_accounts || []).slice(0, 15).map((row) => (
            <div key={row.user_id} className="flex items-center justify-between rounded-lg border border-slate-700/70 bg-slate-900/70 p-4 shadow-sm">
              <span className="font-bold text-slate-100">{row.user_id}</span>
              <span className="font-medium text-slate-300">Risk {Number(row.risk_score || 0).toFixed(2)} • {String(row.risk_level || "LOW")}</span>
            </div>
          ))}
          {(data?.top_accounts || []).length === 0 ? <p className="text-slate-400">No risk accounts available.</p> : null}
        </div>
      </section>

      <section className="card p-6 shadow-panel">
        <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Suspicious Activity Report (SAR)</h3>
          <p className="mt-2 text-sm text-muted">Generated timeline with explainable risk factors, channels, and flow summaries.</p>
        {!sarReport ? (
          <p className="mt-4 text-base text-slate-400">Click Generate SAR to build a regulator-ready activity timeline.</p>
        ) : (
          <div className="mt-4 space-y-4 text-base">
            <p className="font-medium text-slate-200">Events: {Number(sarReport.total_suspicious_events || 0)}</p>
              <p className="font-medium text-slate-300">Avg Risk: {Number(sarReport.average_risk_score || 0).toFixed(2)}</p>
              <p className="font-medium text-slate-300">Channels: {Array.isArray(sarReport.channels_observed) ? sarReport.channels_observed.join(" -> ") : "APP"}</p>
            {(sarReport.timeline || []).slice(0, 20).map((entry) => (
              <div key={`${entry.alert_id}-${entry.timestamp}`} className="rounded-lg border border-slate-700/70 bg-slate-900/70 p-5 shadow-sm">
                  <p className="font-bold text-slate-100">{entry.alert_id} • {entry.account_id} • {String(entry.alert_type || "decision").toUpperCase()}</p>
                <p className="mt-1 font-medium text-slate-300">{entry.reason}</p>
                <p className="mt-2 text-sm font-medium text-slate-400">{entry.timestamp} • Risk {Number(entry.risk_score || 0).toFixed(2)} • Confidence {Number(entry.confidence_score || 0).toFixed(2)}</p>
                  <p className="text-sm text-slate-400">
                    Channels: {Array.isArray(entry.channels_involved) ? entry.channels_involved.join(" -> ") : "APP"}
                    {" • "}
                    Breakdown G:{Number(entry.risk_breakdown?.graph || 0).toFixed(2)} R:{Number(entry.risk_breakdown?.rule || 0).toFixed(2)} P:{Number(entry.risk_breakdown?.pattern || 0).toFixed(2)} J:{Number(entry.risk_breakdown?.jurisdiction || 0).toFixed(2)}
                  </p>
                  <p className="text-sm text-slate-400">
                    Patterns: S:{entry.pattern_indicators?.structuring ? "Y" : "N"} F:{entry.pattern_indicators?.fragmentation ? "Y" : "N"} N:{entry.pattern_indicators?.nesting ? "Y" : "N"} U:{entry.pattern_indicators?.unusual_routing ? "Y" : "N"}
                  </p>
                  <p className="text-sm text-slate-400">
                    Flow: {Array.isArray(entry.flow_summary?.path) && entry.flow_summary.path.length > 0 ? entry.flow_summary.path.join(" -> ") : "N/A"}
                    {" • Hops "}{Number(entry.flow_summary?.hops || 0)}
                    {" • Max Gap "}{Number(entry.flow_summary?.max_gap_minutes || 0).toFixed(2)}m
                  </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
