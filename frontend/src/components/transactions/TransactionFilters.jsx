export default function TransactionFilters({ filters, onChange, onReset }) {
  return (
    <div className="card overflow-hidden p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-700/50 bg-slate-950/35 p-4">
        <div>
          <p className="text-xs uppercase tracking-[0.16em] text-muted">Filter workspace</p>
          <p className="mt-1 text-sm text-slate-200">Narrow the stream by account, date, amount, or verdict.</p>
        </div>
        <button type="button" className="btn-secondary" onClick={onReset}>
          Reset Filters
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-5">
        <label className="text-xs text-muted">
          Search
          <input
            className="input mt-1"
            placeholder="txn id / user id"
            value={filters.search}
            onChange={(e) => onChange({ search: e.target.value })}
          />
        </label>

        <label className="text-xs text-muted">
          Date From
          <input
            type="date"
            className="input mt-1"
            value={filters.dateFrom}
            onChange={(e) => onChange({ dateFrom: e.target.value })}
          />
        </label>

        <label className="text-xs text-muted">
          Date To
          <input
            type="date"
            className="input mt-1"
            value={filters.dateTo}
            onChange={(e) => onChange({ dateTo: e.target.value })}
          />
        </label>

        <label className="text-xs text-muted">
          Min Amount
          <input
            type="number"
            className="input mt-1"
            value={filters.minAmount}
            onChange={(e) => onChange({ minAmount: e.target.value })}
          />
        </label>

        <label className="text-xs text-muted">
          Max Amount
          <input
            type="number"
            className="input mt-1"
            value={filters.maxAmount}
            onChange={(e) => onChange({ maxAmount: e.target.value })}
          />
        </label>

        <label className="text-xs text-muted md:col-span-2">
          Status
          <select className="input mt-1" value={filters.status} onChange={(e) => onChange({ status: e.target.value })}>
            <option value="all">All</option>
            <option value="fraud">Fraud</option>
            <option value="safe">Safe</option>
          </select>
        </label>
      </div>
    </div>
  );
}
