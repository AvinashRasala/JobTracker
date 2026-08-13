"use client";

import { DailyCount } from "@/lib/types";

/**
 * GitHub-contributions-style heatmap. Renders a grid of week columns x
 * 7 day rows for the trailing ~52 weeks. `data` dates are plain
 * "YYYY-MM-DD" strings (date-only ISO strings parse as UTC per the JS
 * spec, unlike datetime strings, so no timezone-normalization needed here).
 */
export function ApplicationsHeatmap({ data }: { data: DailyCount[] }) {
  const countByDate = new Map(data.map((d) => [d.date, d.count]));
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  const today = new Date();
  const start = new Date(today);
  start.setDate(start.getDate() - 52 * 7);
  // Align to the most recent Sunday on/before `start` so week columns line up.
  start.setDate(start.getDate() - start.getDay());

  const weeks: Date[][] = [];
  let cursor = new Date(start);
  while (cursor <= today) {
    const week: Date[] = [];
    for (let d = 0; d < 7; d++) {
      week.push(new Date(cursor));
      cursor.setDate(cursor.getDate() + 1);
    }
    weeks.push(week);
  }

  function colorFor(count: number): string {
    if (count === 0) return "#EEF1F6";
    const intensity = Math.min(count / maxCount, 1);
    if (intensity < 0.25) return "#c9dcd2";
    if (intensity < 0.5) return "#8fb9a3";
    if (intensity < 0.75) return "#5c9a7c";
    return "#3A7D5C";
  }

  function toDateKey(d: Date): string {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  const monthLabels: { index: number; label: string }[] = [];
  let lastMonth = -1;
  weeks.forEach((week, i) => {
    const month = week[0].getMonth();
    if (month !== lastMonth) {
      monthLabels.push({ index: i, label: week[0].toLocaleDateString(undefined, { month: "short" }) });
      lastMonth = month;
    }
  });

  return (
    <div className="overflow-x-auto">
      <div className="inline-block">
        <div className="mb-1 flex" style={{ paddingLeft: 0 }}>
          {weeks.map((_, i) => {
            const label = monthLabels.find((m) => m.index === i);
            return (
              <div key={i} className="w-[13px] flex-shrink-0 text-[10px] text-ink-soft">
                {label ? label.label : ""}
              </div>
            );
          })}
        </div>
        <div className="flex gap-[3px]">
          {weeks.map((week, wi) => (
            <div key={wi} className="flex flex-col gap-[3px]">
              {week.map((day, di) => {
                const key = toDateKey(day);
                const count = countByDate.get(key) || 0;
                const isFuture = day > today;
                return (
                  <div
                    key={di}
                    title={`${key}: ${count} application${count === 1 ? "" : "s"}`}
                    className="h-[10px] w-[10px] rounded-sm"
                    style={{ backgroundColor: isFuture ? "transparent" : colorFor(count) }}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
