export default function PageHeader({ title, subtitle, action }) {
  return (
    <header className="mb-8 flex flex-wrap items-end justify-between gap-6 rounded-3xl border border-slate-700/50 bg-slate-950/40 px-6 py-6 shadow-panel backdrop-blur">
      <div>
        <p className="text-sm uppercase tracking-[0.15em] font-semibold text-cyan-300">Cross Mule Detection</p>
        <h1 className="mt-2 text-3xl font-extrabold text-ink md:text-4xl">{title}</h1>
        {subtitle ? <p className="mt-2 text-base text-muted">{subtitle}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </header>
  );
}
