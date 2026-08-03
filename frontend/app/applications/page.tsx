"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, ExternalLink, BellRing, Download } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { StatusStamp } from "@/components/ui/status-stamp";
import { AddApplicationDialog } from "@/components/add-application-dialog";
import { api } from "@/lib/api";
import { ApplicationStatus, STATUS_LABELS } from "@/lib/types";
import { formatDateShort, isPastOrNow } from "@/lib/dates";

const STATUS_OPTIONS = Object.entries(STATUS_LABELS) as [ApplicationStatus, string][];

export default function ApplicationsPage() {
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [exporting, setExporting] = useState(false);
  const queryClient = useQueryClient();

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await api.exportApplicationsCsv();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `jobtrack-applications-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  const params: Record<string, string> = {};
  if (keyword) params.keyword = keyword;
  if (statusFilter) params.status = statusFilter;

  const { data, isLoading } = useQuery({
    queryKey: ["applications", params],
    queryFn: () => api.listApplications(params),
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ApplicationStatus }) => api.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["status-distribution"] });
    },
  });

  return (
    <AppShell>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="postmark w-fit text-ledger">Ledger</p>
          <h2 className="mt-2 font-display text-2xl font-bold text-ink">Applications</h2>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleExport} disabled={exporting}>
            <Download size={16} /> {exporting ? "Exporting…" : "Export CSV"}
          </Button>
          <Button onClick={() => setDialogOpen(true)}>
            <Plus size={16} /> Log application
          </Button>
        </div>
      </div>

      <Card className="mb-4 flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
        <Input
          placeholder="Search by role…"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          className="sm:max-w-xs"
        />
        <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="sm:max-w-xs">
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </Select>
        {(keyword || statusFilter) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setKeyword("");
              setStatusFilter("");
            }}
          >
            Clear filters
          </Button>
        )}
      </Card>

      <Card>
        {isLoading ? (
          <p className="p-6 text-sm text-ink-soft">Loading ledger…</p>
        ) : !data || data.items.length === 0 ? (
          <div className="p-10 text-center">
            <p className="text-sm font-medium text-ink">No applications logged yet.</p>
            <p className="mt-1 text-sm text-ink-soft">Click "Log application" to add your first entry.</p>
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
                    {app.follow_up_at && isPastOrNow(app.follow_up_at) && (
                      <span className="flex items-center gap-1 text-xs font-medium text-stamp-amber">
                        <BellRing size={12} /> Follow up
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-ink-soft">{app.company_name || "Company not set"}</p>
                  <p className="mt-0.5 font-mono text-xs text-ink-soft">
                    {formatDateShort(app.applied_at)}
                    {app.location ? ` · ${app.location}` : ""}
                    {app.work_type !== "unknown" ? ` · ${app.work_type}` : ""}
                    {app.platform_name ? ` · ${app.platform_name}` : ""}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusStamp status={app.status} />
                  <Select
                    value={app.status}
                    onChange={(e) =>
                      statusMutation.mutate({ id: app.id, status: e.target.value as ApplicationStatus })
                    }
                    className="w-auto text-xs"
                  >
                    {STATUS_OPTIONS.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </Select>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <AddApplicationDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </AppShell>
  );
}
