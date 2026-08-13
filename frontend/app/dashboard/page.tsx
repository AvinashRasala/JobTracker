"use client";

import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/app-shell";
import { StatCard } from "@/components/stat-card";
import { Card } from "@/components/ui/card";
import { StatusDistributionChart } from "@/components/charts/status-distribution-chart";
import { PlatformDistributionChart } from "@/components/charts/platform-distribution-chart";
import { ApplicationsPerDayChart } from "@/components/charts/applications-per-day-chart";
import { FunnelChart } from "@/components/charts/funnel-chart";
import { ApplicationsHeatmap } from "@/components/charts/applications-heatmap";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const stats = useQuery({ queryKey: ["dashboard-stats"], queryFn: api.dashboardStats });
  const statusDist = useQuery({ queryKey: ["status-distribution"], queryFn: api.statusDistribution });
  const platformDist = useQuery({ queryKey: ["platform-distribution"], queryFn: api.platformDistribution });
  const perDay = useQuery({ queryKey: ["applications-per-day"], queryFn: () => api.applicationsPerDay(30) });
  const funnel = useQuery({ queryKey: ["funnel"], queryFn: api.funnel });
  const heatmapData = useQuery({ queryKey: ["applications-heatmap"], queryFn: () => api.applicationsPerDay(365) });

  const s = stats.data;

  return (
    <AppShell>
      <div className="mb-6 flex items-baseline justify-between">
        <div>
          <p className="postmark w-fit text-ledger">Manifest</p>
          <h2 className="mt-2 font-display text-2xl font-bold text-ink">Pipeline overview</h2>
        </div>
      </div>

      {stats.isLoading ? (
        <p className="text-sm text-ink-soft">Loading manifest…</p>
      ) : s ? (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Total logged" value={s.total_applications} />
            <StatCard label="Today" value={s.applications_today} />
            <StatCard label="This week" value={s.applications_this_week} />
            <StatCard label="This month" value={s.applications_this_month} />
          </div>

          <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
            <StatCard label="Response rate" value={`${s.response_rate}%`} />
            <StatCard label="Interview rate" value={`${s.interview_rate}%`} accent="amber" />
            <StatCard label="Offer rate" value={`${s.offer_rate}%`} accent="green" />
            <StatCard label="Rejection rate" value={`${s.rejection_rate}%`} accent="red" />
            <StatCard
              label="Avg. response"
              value={s.average_response_time_days != null ? `${s.average_response_time_days}d` : "—"}
            />
            <StatCard
              label="Needs follow-up"
              value={s.needs_follow_up}
              accent={s.needs_follow_up > 0 ? "amber" : "ink"}
            />
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
            <StatCard label="Most applied company" value={s.most_applied_company || "—"} />
            <StatCard label="Most applied role" value={s.most_applied_role || "—"} />
            <StatCard label="Most used platform" value={s.most_used_platform || "—"} />
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Card className="p-5">
              <h3 className="font-display text-sm font-semibold text-ink">Applications — last 30 days</h3>
              <div className="mt-2">
                {perDay.data && perDay.data.length > 0 ? (
                  <ApplicationsPerDayChart data={perDay.data} />
                ) : (
                  <EmptyChart />
                )}
              </div>
            </Card>

            <Card className="p-5">
              <h3 className="font-display text-sm font-semibold text-ink">Status distribution</h3>
              <div className="mt-2">
                {statusDist.data && statusDist.data.length > 0 ? (
                  <StatusDistributionChart data={statusDist.data} />
                ) : (
                  <EmptyChart />
                )}
              </div>
            </Card>

            <Card className="p-5 lg:col-span-2">
              <h3 className="font-display text-sm font-semibold text-ink">Platform distribution</h3>
              <div className="mt-2">
                {platformDist.data && platformDist.data.length > 0 ? (
                  <PlatformDistributionChart data={platformDist.data} />
                ) : (
                  <EmptyChart />
                )}
              </div>
            </Card>

            <Card className="p-5">
              <h3 className="font-display text-sm font-semibold text-ink">Pipeline funnel</h3>
              <p className="mt-0.5 text-xs text-ink-soft">Applications that ever reached each stage</p>
              <div className="mt-4">
                {funnel.data && funnel.data.some((f) => f.count > 0) ? (
                  <FunnelChart data={funnel.data} />
                ) : (
                  <EmptyChart />
                )}
              </div>
            </Card>

            <Card className="p-5">
              <h3 className="font-display text-sm font-semibold text-ink">Activity — last 12 months</h3>
              <div className="mt-4">
                {heatmapData.data && heatmapData.data.length > 0 ? (
                  <ApplicationsHeatmap data={heatmapData.data} />
                ) : (
                  <EmptyChart />
                )}
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </AppShell>
  );
}

function EmptyChart() {
  return (
    <div className="flex h-48 flex-col items-center justify-center gap-2 text-center">
      <p className="text-sm text-ink-soft">Nothing logged yet.</p>
      <p className="text-xs text-ink-soft">Add an application to see it show up here.</p>
    </div>
  );
}
