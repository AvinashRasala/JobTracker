import { ApplicationStatus, STATUS_COLOR, STATUS_LABELS } from "@/lib/types";
import { cn } from "@/lib/cn";

const colorClasses = {
  green: "text-stamp-green",
  amber: "text-stamp-amber",
  red: "text-stamp-red",
  slate: "text-stamp-slate",
};

export function StatusStamp({ status, className }: { status: ApplicationStatus; className?: string }) {
  return (
    <span className={cn("postmark", colorClasses[STATUS_COLOR[status]], className)}>
      {STATUS_LABELS[status]}
    </span>
  );
}
