"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, Trash2 } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { StatusStamp } from "@/components/ui/status-stamp";
import { InterviewRoundsPanel } from "@/components/interview-rounds-panel";
import { api } from "@/lib/api";
import { ApplicationStatus, STATUS_LABELS } from "@/lib/types";
import { formatDateShort } from "@/lib/dates";

const STATUS_OPTIONS = Object.entries(STATUS_LABELS) as [ApplicationStatus, string][];

export default function ApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const applicationId = params.id as string;
  const queryClient = useQueryClient();

  const { data: application, isLoading } = useQuery({
    queryKey: ["application", applicationId],
    queryFn: () => api.getApplication(applicationId),
  });

  const [form, setForm] = useState({
    location: "",
    expected_ctc: "",
    offered_ctc: "",
    notice_period_days: "",
    referred_by_name: "",
    referred_by_email: "",
    referred_by_relationship: "",
  });

  useEffect(() => {
    if (application) {
      setForm({
        location: application.location || "",
        expected_ctc: application.expected_ctc?.toString() || "",
        offered_ctc: application.offered_ctc?.toString() || "",
        notice_period_days: application.notice_period_days?.toString() || "",
        referred_by_name: application.referred_by_name || "",
        referred_by_email: application.referred_by_email || "",
        referred_by_relationship: application.referred_by_relationship || "",
      });
    }
  }, [application]);

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ["application", applicationId] });
    queryClient.invalidateQueries({ queryKey: ["applications"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    queryClient.invalidateQueries({ queryKey: ["offers"] });
  };

  const statusMutation = useMutation({
    mutationFn: (status: ApplicationStatus) => api.updateStatus(applicationId, status),
    onSuccess: invalidateAll,
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = {
        location: form.location || null,
        referred_by_name: form.referred_by_name || null,
        referred_by_email: form.referred_by_email || null,
        referred_by_relationship: form.referred_by_relationship || null,
      };
      payload.expected_ctc = form.expected_ctc ? Number(form.expected_ctc) : null;
      payload.offered_ctc = form.offered_ctc ? Number(form.offered_ctc) : null;
      payload.notice_period_days = form.notice_period_days ? Number(form.notice_period_days) : null;
      return api.updateApplication(applicationId, payload);
    },
    onSuccess: invalidateAll,
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteApplication(applicationId),
    onSuccess: () => router.push("/applications"),
  });

  if (isLoading || !application) {
    return (
      <AppShell>
        <p className="text-sm text-ink-soft">Loading…</p>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <button
        onClick={() => router.push("/applications")}
        className="mb-4 flex items-center gap-1 text-sm text-ink-soft hover:text-ledger"
      >
        <ArrowLeft size={14} /> Back to applications
      </button>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="postmark w-fit text-ledger">Waybill</p>
          <h2 className="mt-2 flex items-center gap-2 font-display text-2xl font-bold text-ink">
            {application.role_title}
            {application.job_url && (
              <a href={application.job_url} target="_blank" rel="noreferrer" className="text-ink-soft hover:text-ledger">
                <ExternalLink size={18} />
              </a>
            )}
          </h2>
          <p className="mt-1 font-mono text-sm text-ink-soft">
            Applied {formatDateShort(application.applied_at)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <StatusStamp status={application.status} />
          <Select
            value={application.status}
            onChange={(e) => statusMutation.mutate(e.target.value as ApplicationStatus)}
            className="w-auto"
          >
            {STATUS_OPTIONS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="p-5">
          <h3 className="font-display text-sm font-semibold text-ink">Details</h3>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateMutation.mutate();
            }}
            className="mt-4 space-y-4"
          >
            <div>
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                value={form.location}
                onChange={(e) => setForm((f) => ({ ...f, location: e.target.value }))}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="expected_ctc">Expected CTC</Label>
                <Input
                  id="expected_ctc"
                  type="number"
                  value={form.expected_ctc}
                  onChange={(e) => setForm((f) => ({ ...f, expected_ctc: e.target.value }))}
                />
              </div>
              <div>
                <Label htmlFor="offered_ctc">Offered CTC</Label>
                <Input
                  id="offered_ctc"
                  type="number"
                  value={form.offered_ctc}
                  onChange={(e) => setForm((f) => ({ ...f, offered_ctc: e.target.value }))}
                  placeholder="fill in once you get an offer"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="notice_period_days">Notice period (days)</Label>
              <Input
                id="notice_period_days"
                type="number"
                value={form.notice_period_days}
                onChange={(e) => setForm((f) => ({ ...f, notice_period_days: e.target.value }))}
              />
            </div>
            <div className="border-t border-hairline pt-4">
              <p className="mb-3 text-xs font-medium uppercase tracking-wide text-ink-soft">Referral</p>
              <div className="space-y-3">
                <Input
                  value={form.referred_by_name}
                  onChange={(e) => setForm((f) => ({ ...f, referred_by_name: e.target.value }))}
                  placeholder="Referred by (name)"
                />
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    type="email"
                    value={form.referred_by_email}
                    onChange={(e) => setForm((f) => ({ ...f, referred_by_email: e.target.value }))}
                    placeholder="Referrer email"
                  />
                  <Input
                    value={form.referred_by_relationship}
                    onChange={(e) => setForm((f) => ({ ...f, referred_by_relationship: e.target.value }))}
                    placeholder="Relationship"
                  />
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                onClick={() => {
                  if (confirm("Delete this application? This cannot be undone.")) deleteMutation.mutate();
                }}
                className="flex items-center gap-1 text-sm text-stamp-red hover:underline"
              >
                <Trash2 size={14} /> Delete application
              </button>
              <Button type="submit" disabled={updateMutation.isPending}>
                {updateMutation.isPending ? "Saving…" : "Save changes"}
              </Button>
            </div>
          </form>
        </Card>

        <InterviewRoundsPanel applicationId={applicationId} />
      </div>
    </AppShell>
  );
}
