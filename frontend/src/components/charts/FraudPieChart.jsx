import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#10b981", "#ef4444"];

export default function FraudPieChart({ safeCount = 0, fraudCount = 0 }) {
  const data = [
    { name: "Safe", value: safeCount },
    { name: "Fraud", value: fraudCount },
  ];

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Fraud vs Normal</h3>
          <p className="mt-1 text-xs text-muted">Proportion of flagged transactions in the current data window.</p>
        </div>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={70} outerRadius={95}>
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: "#0f1728", border: "1px solid #334155", borderRadius: "12px" }}
              itemStyle={{ color: "#eaf2ff" }}
            />
            <Legend wrapperStyle={{ color: "#9cb0c8" }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
