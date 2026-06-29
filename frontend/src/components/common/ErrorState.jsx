export default function ErrorState({ error, onRetry }) {
  return (
    <div className="card overflow-hidden p-5 text-sm text-red-300">
      <div className="mb-4 h-1.5 w-24 rounded-full bg-gradient-to-r from-red-400/70 to-red-500/20" />
      <p className="font-semibold">Something went wrong</p>
      <p className="mt-1 text-red-200/90">{error?.message || "Unable to load data."}</p>
      {onRetry ? (
        <button type="button" className="btn-secondary mt-3" onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </div>
  );
}
