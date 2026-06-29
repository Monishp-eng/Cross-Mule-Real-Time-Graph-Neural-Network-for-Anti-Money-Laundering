import { dateTime } from "../../utils/formatters";

export default function AlertsTable({ alerts = [], onMarkReviewed, onAction, compact = false }) {
  return (
    <div className="card overflow-hidden shadow-panel">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-700/50 bg-slate-950/35 px-6 py-5">
        <div>
          <h3 className="text-base font-bold uppercase tracking-[0.15em] text-slate-200">Alerts</h3>
          <p className="mt-2 text-sm text-muted">Prioritized fraud findings with review workflow.</p>
        </div>
        <p className="rounded-full border border-slate-700/70 bg-slate-900/70 px-4 py-2 text-sm font-semibold text-slate-300 shadow-sm">
          {alerts.length} alerts
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-base">
          <thead className="bg-slate-900/80 text-left text-sm font-semibold uppercase tracking-[0.15em] text-muted">
            <tr>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4">Case ID</th>
              <th className="px-6 py-4">Alert ID</th>
              <th className="px-6 py-4">Account</th>
              <th className="px-6 py-4">Severity</th>
              <th className="px-6 py-4">Confidence</th>
              <th className="px-6 py-4">Channels</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Reason</th>
              <th className="px-6 py-4">Created</th>
              <th className="px-6 py-4">Breakdown</th>
              {!compact ? <th className="px-6 py-4">Action</th> : null}
            </tr>
          </thead>
          <tbody>
            {alerts.length === 0 ? (
              <tr>
                <td className="px-6 py-6 text-center text-muted" colSpan={compact ? 11 : 12}>
                  No alerts found.
                </td>
              </tr>
            ) : (
              alerts.map((alert) => {
                const rawSeverity = String(alert.severity || "LOW").toUpperCase();
                let sev = "LOW";
                if (["CRITICAL", "HIGH", "RED"].includes(rawSeverity)) sev = "HIGH";
                else if (["MEDIUM", "YELLOW", "WARN"].includes(rawSeverity)) sev = "MEDIUM";
                else if (["LOW", "SAFE", "GREEN"].includes(rawSeverity)) sev = "LOW";

                const isHigh = sev === "HIGH";
                const isMedium = sev === "MEDIUM";

                return (
                  <tr
                    key={alert.alert_id || alert.id}
                    className={[
                      "border-t border-slate-800/80",
                      isHigh ? "bg-red-500/10" : isMedium ? "bg-amber-400/10" : "odd:bg-slate-950/20",
                    ].join(" ")}
                  >
                    <td className="px-6 py-4 text-sm font-medium uppercase text-slate-300">{String(alert.alert_type || "decision")}</td>
                    <td className="px-6 py-4 code text-sm font-medium text-slate-300">{alert.case_id || `CASE-${alert.alert_id || alert.id}`}</td>
                    <td className="px-6 py-4 code text-sm font-bold text-slate-100">{alert.alert_id || alert.id}</td>
                    <td className="px-6 py-4 font-medium">{alert.account_id || alert.user_id || "-"}</td>
                    <td className="px-6 py-4">
                      <span
                        className={[
                          "rounded-full px-3 py-1 text-sm font-bold shadow-sm",
                          isHigh
                            ? "bg-red-500/20 text-red-300"
                            : isMedium
                              ? "bg-amber-400/20 text-amber-300"
                              : "bg-emerald-500/20 text-emerald-300",
                        ].join(" ")}
                      >
                        {sev}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-200">{Number(alert.confidence_score || 0).toFixed(2)}</td>
                    <td className="px-6 py-4 font-medium text-slate-300">{Array.isArray(alert.channels_involved) ? alert.channels_involved.join(" -> ") : (alert.channels_involved || "APP")}</td>
                    <td className="px-6 py-4">
                      <span className="rounded-full border border-slate-700/70 bg-slate-900/60 px-3 py-1 text-sm font-medium text-slate-200 shadow-sm">
                        {String(alert.status || "OPEN").toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm leading-relaxed text-slate-300">{alert.detection_reason || alert.reason || alert.explanation || "-"}</td>
                    <td className="px-6 py-4 text-sm text-slate-400">{dateTime(alert.timestamp || alert.created_at)}</td>
                    <td className="px-6 py-4 text-sm text-slate-400">
                      G:{Number(alert.risk_breakdown?.graph || 0).toFixed(2)} R:{Number(alert.risk_breakdown?.rule || 0).toFixed(2)} P:{Number(alert.risk_breakdown?.pattern || 0).toFixed(2)}
                    </td>
                    {!compact ? (
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm"
                            onClick={() => onAction?.(alert.alert_id || alert.id, "open_case")}
                          >
                            Open Case
                          </button>
                          <button
                            type="button"
                            className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm"
                            onClick={() => onAction?.(alert.alert_id || alert.id, "mark_investigating")}
                          >
                            Mark as Investigating
                          </button>
                          <button
                            type="button"
                            className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm"
                            onClick={() => onAction?.(alert.alert_id || alert.id, "confirm_mule")}
                          >
                            Confirm Mule/Fraud
                          </button>
                          <button
                            type="button"
                            className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm"
                            onClick={() => onAction?.(alert.alert_id || alert.id, "false_positive")}
                          >
                            Mark as False Positive
                          </button>
                          <button
                            type="button"
                            className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm"
                            onClick={() => onAction?.(alert.alert_id || alert.id, "freeze_account")}
                          >
                            Freeze Account
                          </button>
                          <button
                            type="button"
                            className="btn-secondary px-4 py-2 text-sm font-semibold shadow-sm"
                            onClick={() => onAction?.(alert.alert_id || alert.id, "escalate_compliance_review")}
                          >
                            Escalate for Compliance Review
                          </button>
                        </div>
                      </td>
                    ) : null}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
