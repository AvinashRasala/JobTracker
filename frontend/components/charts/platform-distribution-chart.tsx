"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { PlatformCount } from "@/lib/types";

export function PlatformDistributionChart({ data }: { data: PlatformCount[] }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(23,27,38,0.08)" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 11, fill: "#4B5468" }} allowDecimals={false} />
        <YAxis type="category" dataKey="platform" tick={{ fontSize: 11, fill: "#4B5468" }} width={110} />
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid rgba(23,27,38,0.12)" }}
          cursor={{ fill: "rgba(23,27,38,0.04)" }}
        />
        <Bar dataKey="count" fill="#1F3A5F" radius={[0, 4, 4, 0]} barSize={14} />
      </BarChart>
    </ResponsiveContainer>
  );
}
