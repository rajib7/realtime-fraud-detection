import React from "react";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";

export default function Sparkline({ data, color = "#00E5FF", height = 36 }) {
  const chartData = (data || []).map((v, i) => ({ i, v }));
  const domainMax = Math.max(1, ...(data || []));
  return (
    <div
      style={{ width: "100%", height, minWidth: 40, minHeight: 24 }}
      className="pointer-events-none"
    >
      <ResponsiveContainer width="100%" height="100%" minWidth={40} minHeight={24}>
        <LineChart data={chartData} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
          <YAxis hide domain={[0, domainMax * 1.2]} />
          <Line
            type="monotone"
            dataKey="v"
            stroke={color}
            strokeWidth={1.8}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
