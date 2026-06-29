import { scoreToRisk } from "../../utils/formatters";

export default function FraudScoreCard({ result }) {
  if (!result) {
    return (
      <section className="card p-5 text-sm text-muted">
        Enter a user ID and run an analysis to see the score, risk level, and explanation.
      </section>
    );
  }

  const score = Number(result.fraud_score ?? result.score ?? 0);
  const percentage = Math.max(0, Math.min(100, Math.round(score * 100)));
  const risk = result.risk_level || scoreToRisk(score);

  const barClass =
    risk === "High"
      ? "from-red-600 to-red-400"
      : risk === "Medium"
        ? "from-amber-500 to-amber-300"
        : "from-emerald-500 to-emerald-300";

  return (
    <section className="card fade-in overflow-hidden p-4">
      <div className={`mb-4 h-1.5 w-24 rounded-full bg-gradient-to-r ${barClass}`} />
      <h3 className="text-sm font-semibold text-slate-100">Fraud Analysis Result</h3>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <div>
          <p className="text-xs text-muted">Fraud Score</p>
          <p className="code text-2xl font-bold text-cyan-200">{score.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-xs text-muted">Risk Level</p>
          <p className="text-2xl font-bold">{risk}</p>
        </div>
        <div>
          <p className="text-xs text-muted">User</p>
          <p className="code text-sm text-slate-200">{result.user_id || "-"}</p>
        </div>
      </div>

      <div className="mt-4">
        <div className="mb-1 flex items-center justify-between text-xs text-muted">
          <span>Risk indicator</span>
          <span>{percentage}%</span>
        </div>
        <div className="h-3 overflow-hidden rounded-full bg-slate-800">
          <div className={`h-full rounded-full bg-gradient-to-r ${barClass} transition-all duration-500`} style={{ width: `${percentage}%` }} />
        </div>
      </div>

      <p className="mt-4 rounded-2xl border border-slate-700 bg-slate-900/70 p-4 text-sm leading-6 text-slate-300">
        {result.explanation || "No explanation provided by backend."}
      </p>
    </section>
  );
}
