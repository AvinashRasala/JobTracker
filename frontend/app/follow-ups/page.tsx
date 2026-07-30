"use client";

import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { BellRing, ExternalLink } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusStamp } from "@/components/ui/status-stamp";
import { api } from "@/lib/api";

export default function FollowUpsPage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["needs-follow-up"],
    queryFn: api.needsFollowUp,
  });

  const snoozeMutation = useMutation({
    mutationFn: (id: string) => {
      const nextFollowUp = new Date();
      nextFollowUp.setDate(nextFollowUp.getDate() + 3);
      return api.updateApplication(id, { follow_up_at: nextFollowUp.toISOString() });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["needs-follow-up"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  return (
    <AppShell>
      <div className="mb-6">
        <p className="postmark w-fit text-ledger">Reminders</p>
        <h2 className="mt-2 font-display text-2xl font-bold text-ink">Needs follow-up</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Applications with no movement past their check-in date. Nudge the recruiter, or snooze if you've already followed up.
        </p>
      </div>

      <Card>
        {isLoading ? (
          <p className="p-6 text-sm text-ink-soft">Loading…</p>
        ) : !data || data.items.length === 0 ? (
          <div className="p-10 text-center">
            <BellRing size={28} className="mx-auto text-stamp-green" />
            <p className="mt-3 text-sm font-medium text-ink">Nothing needs a follow-up right now.</p>
            <p className="mt-1 text-sm text-ink-soft">New applications default to a 7-day check-in reminder.</p>
          </div>
        ) : (
          <div>
            {data.items.map((app) => (
              <div key={app.id} className="ledger-row flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Link href={`/applications/${app.id}`} className="truncate font-medium text-ink hover:text-ledger hover:underline">
                      {app.role_title}
                    </Link>
                    {app.job_url && (
                      <a href={app.job_url} target="_blank" rel="noreferrer" className="text-ink-soft hover:text-ledger">
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                  <p className="mt-0.5 font-mono text-xs text-ink-soft">
                    Follow-up was due {app.follow_up_at ? new Date(app.follow_up_at).toISOString().slice(0, 10) : "—"}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusStamp status={app.status} />
                  <Button size="sm" variant="secondary" onClick={() => snoozeMutation.mutate(app.id)} disabled={snoozeMutation.isPending}>
                    Snooze 3 days
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </AppShell>
  );
}
