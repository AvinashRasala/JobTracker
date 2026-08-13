"use client";

import { FunnelStage } from "@/lib/types";

const STAGE_COLORS = ["#5B6472", "#5B6472", "#5B6472", "#D98E2B", "#D98E2B", "#3A7D5C"];

export function FunnelChart({ data }: { data: FunnelStage[] }) {
  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="space-y-2">
      {data.map((stage, i) => {
        const widthPct = Math.max((stage.count / maxCount) * 100, stage.count > 0 ? 4 : 0);
        return (
          <div key={stage.stage} className="flex items-center gap-3">
            <span className="w-24 flex-shrink-0 text-right text-xs text-ink-soft">{stage.stage}</span>
            <div className="relative h-7 flex-1 overflow-hidden rounded bg-paper">
              <div
                className="h-full rounded transition-all"
                style={{ width: `${widthPct}%`, backgroundColor: STAGE_COLORS[i % STAGE_COLORS.length] }}
              />
            </div>
            <span className="w-8 flex-shrink-0 font-mono text-xs font-medium text-ink">{stage.count}</span>
          </div>
        );
      })}
    </div>
  );
}
