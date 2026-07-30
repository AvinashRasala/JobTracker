import { Card } from "@/components/ui/card";
import { cn } from "@/lib/cn";

export function StatCard({
  label,
  value,
  sublabel,
  accent = "ink",
}: {
  label: string;
  value: string | number;
  sublabel?: string;
  accent?: "ink" | "green" | "amber" | "red";
}) {
  const accentClass = {
    ink: "text-ink",
    green: "text-stamp-green",
    amber: "text-stamp-amber",
    red: "text-stamp-red",
  }[accent];

  return (
    <Card className="px-5 py-4">
      <p className="text-xs font-medium uppercase tracking-wide text-ink-soft">{label}</p>
      <p className={cn("mt-1 font-mono text-2xl font-medium tabular-nums", accentClass)}>{value}</p>
      {sublabel && <p className="mt-0.5 text-xs text-ink-soft">{sublabel}</p>}
    </Card>
  );
}
