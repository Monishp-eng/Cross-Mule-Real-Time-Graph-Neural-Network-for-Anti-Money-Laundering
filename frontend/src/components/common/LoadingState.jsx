export default function LoadingState({ label = "Loading..." }) {
  return (
    <div className="card overflow-hidden p-5">
      <div className="mb-4 h-1.5 w-24 rounded-full bg-gradient-to-r from-cyan-400/70 to-cyan-500/20" />
      <div className="h-5 w-40 animate-pulse rounded bg-slate-700/60" />
      <div className="mt-3 h-4 w-full animate-pulse rounded bg-slate-800/70" />
      <div className="mt-2 h-4 w-3/4 animate-pulse rounded bg-slate-800/70" />
      <p className="mt-4 text-sm text-muted">{label}</p>
    </div>
  );
}
