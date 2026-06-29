import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export default function ChannelActivityChart({ data = [] }) {
  return (
    <div className="card p-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-100">Channel-wise Activity</h3>
        <p className="mt-1 text-xs text-muted">Transaction volume split by App, Web, ATM, and UPI channels.</p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#243041" />
            <XAxis dataKey="channel" stroke="#94a3b8" />
            <YAxis stroke="#94a3b8" />
            <Tooltip
              contentStyle={{ background: "#0f1728", border: "1px solid #334155", borderRadius: "12px" }}
              itemStyle={{ color: "#eaf2ff" }}
            />
            <Bar dataKey="count" fill="#22d3ee" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
