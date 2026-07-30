"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { DailyCount } from "@/lib/types";

export function ApplicationsPerDayChart({ data }: { data: DailyCount[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={data} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="fillApplied" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#1F3A5F" stopOpacity={0.35} />
            <stop offset="95%" stopColor="#1F3A5F" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(23,27,38,0.08)" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 11, fill: "#4B5468" }}
          tickFormatter={(d: string) => d.slice(5)}
        />
        <YAxis tick={{ fontSize: 11, fill: "#4B5468" }} allowDecimals={false} />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid rgba(23,27,38,0.12)" }} />
        <Area type="monotone" dataKey="count" stroke="#1F3A5F" strokeWidth={2} fill="url(#fillApplied)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
