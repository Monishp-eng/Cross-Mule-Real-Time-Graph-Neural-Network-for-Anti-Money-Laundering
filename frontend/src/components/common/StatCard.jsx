export default function StatCard({ title, value, hint, tone = "default" }) {
  const barClass =
    tone === "danger"
      ? "from-red-400/70 to-red-500/20"
      : tone === "warn"
        ? "from-amber-400/70 to-amber-500/20"
        : tone === "success"
          ? "from-emerald-400/70 to-emerald-500/20"
          : "from-cyan-400/70 to-cyan-500/20";

  const toneClass =
    tone === "danger"
      ? "text-red-300"
      : tone === "warn"
        ? "text-amber-300"
        : tone === "success"
          ? "text-emerald-300"
          : "text-cyan-300";

  return (
    <article className="card fade-in overflow-hidden p-6 shadow-panel">
      <div className={`h-2 rounded-full bg-gradient-to-r ${barClass}`} />
      <p className="text-sm uppercase tracking-[0.15em] font-semibold text-muted mt-2">{title}</p>
      <p className={`mt-3 text-4xl font-extrabold ${toneClass}`}>{value}</p>
      {hint ? <p className="mt-2 text-sm text-muted">{hint}</p> : null}
    </article>
  );
}
