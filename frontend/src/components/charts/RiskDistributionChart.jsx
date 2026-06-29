import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#ef4444", "#f59e0b", "#10b981"];

export default function RiskDistributionChart({ high = 0, medium = 0, low = 0 }) {
  const data = [
    { name: "High", value: high },
    { name: "Medium", value: medium },
    { name: "Low", value: low },
  ];

  return (
    <div className="card p-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-100">Risk Distribution</h3>
        <p className="mt-1 text-xs text-muted">Current account risk bands across monitored entities.</p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={68} outerRadius={96}>
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
