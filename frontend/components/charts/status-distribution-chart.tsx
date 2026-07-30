"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { StatusCount, ApplicationStatus, STATUS_LABELS, STATUS_COLOR } from "@/lib/types";

const COLOR_HEX = { green: "#3A7D5C", amber: "#D98E2B", red: "#B3432B", slate: "#5B6472" };

export function StatusDistributionChart({ data }: { data: StatusCount[] }) {
  const chartData = data.map((d) => ({
    name: STATUS_LABELS[d.status as ApplicationStatus] || d.status,
    count: d.count,
    color: COLOR_HEX[STATUS_COLOR[d.status as ApplicationStatus] || "slate"],
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(23,27,38,0.08)" vertical={false} />
        <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#4B5468" }} angle={-25} textAnchor="end" height={60} interval={0} />
        <YAxis tick={{ fontSize: 11, fill: "#4B5468" }} allowDecimals={false} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid rgba(23,27,38,0.12)" }}
          cursor={{ fill: "rgba(23,27,38,0.04)" }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
