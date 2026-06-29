import { AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";

export default function VelocityTrendChart({ data = [] }) {
  return (
    <div className="card p-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-100">Transaction Velocity Trends</h3>
        <p className="mt-1 text-xs text-muted">Near real-time volume trend indicating rapid movement periods.</p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#243041" vertical={false} />
            <XAxis 
              dataKey="label" 
              stroke="#94a3b8" 
              tickMargin={10} 
            />
            <YAxis 
              stroke="#94a3b8" 
              tickFormatter={(value) => `${value} txns`}
              width={80}
            />
            <Tooltip
              contentStyle={{ background: "#0f1728", border: "1px solid #334155", borderRadius: "12px" }}
              itemStyle={{ color: "#eaf2ff" }}
              formatter={(value) => [`${value} Transactions`, "Volume"]}
              labelFormatter={(label) => `Time: ${label}`}
            />
            <Area type="monotone" dataKey="count" stroke="#f59e0b" fill="#f59e0b33" strokeWidth={2.5} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
