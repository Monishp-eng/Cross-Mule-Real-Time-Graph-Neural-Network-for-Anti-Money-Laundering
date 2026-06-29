import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

export default function TransactionsLineChart({ data = [] }) {
  return (
    <div className="card p-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-100">Transactions Over Time</h3>
        <p className="mt-1 text-xs text-muted">Daily ingestion volume from the backend activity stream.</p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#243041" />
            <XAxis dataKey="label" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{ background: "#0f1728", border: "1px solid #334155", borderRadius: "12px" }}
              itemStyle={{ color: "#eaf2ff" }}
            />
            <Line type="monotone" dataKey="count" stroke="#22d3ee" strokeWidth={2.5} dot={{ r: 2 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
