"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/dates";
import {
  InterviewMode,
  InterviewOutcome,
  INTERVIEW_MODE_LABELS,
  INTERVIEW_OUTCOME_LABELS,
} from "@/lib/types";

const MODE_OPTIONS = Object.entries(INTERVIEW_MODE_LABELS) as [InterviewMode, string][];
const OUTCOME_OPTIONS = Object.entries(INTERVIEW_OUTCOME_LABELS) as [InterviewOutcome, string][];

const OUTCOME_COLOR: Record<InterviewOutcome, string> = {
  pending: "text-stamp-slate",
  cleared: "text-stamp-green",
  rejected: "text-stamp-red",
  rescheduled: "text-stamp-amber",
  no_show: "text-stamp-red",
};

export function InterviewRoundsPanel({ applicationId }: { applicationId: string }) {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    round_name: "",
    mode: "video" as InterviewMode,
    interviewer_name: "",
    interviewer_designation: "",
    scheduled_at: "",
  });

  const { data: rounds, isLoading } = useQuery({
    queryKey: ["interview-rounds", applicationId],
    queryFn: () => api.listInterviewRounds(applicationId),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["interview-rounds", applicationId] });

  const createMutation = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = { ...form };
      // <input type="datetime-local"> gives local wall-clock time with no
      // timezone marker (e.g. "2026-08-05T14:30"). Converting through
      // `new Date(...)` (which correctly treats a marker-less string as
      // local time) then `.toISOString()` gives the backend an unambiguous
      // UTC timestamp, matching what the display-side formatting expects.
      if (form.scheduled_at) {
        payload.scheduled_at = new Date(form.scheduled_at).toISOString();
      } else {
        delete payload.scheduled_at;
      }
      if (!form.interviewer_name) delete payload.interviewer_name;
      if (!form.interviewer_designation) delete payload.interviewer_designation;
      return api.createInterviewRound(applicationId, payload);
    },
    onSuccess: () => {
      invalidate();
      setForm({ round_name: "", mode: "video", interviewer_name: "", interviewer_designation: "", scheduled_at: "" });
      setShowForm(false);
    },
  });

  const outcomeMutation = useMutation({
    mutationFn: ({ roundId, outcome }: { roundId: string; outcome: InterviewOutcome }) =>
      api.updateInterviewRound(applicationId, roundId, { outcome }),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: (roundId: string) => api.deleteInterviewRound(applicationId, roundId),
    onSuccess: invalidate,
  });

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-ink">Interview rounds</h3>
        <Button size="sm" variant="secondary" onClick={() => setShowForm((s) => !s)}>
          <Plus size={14} /> Add round
        </Button>
      </div>

      {showForm && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createMutation.mutate();
          }}
          className="mt-4 space-y-3 rounded-md border border-dashed border-hairline p-3"
        >
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="round_name">Round name</Label>
              <Input
                id="round_name"
                required
                value={form.round_name}
                onChange={(e) => setForm((f) => ({ ...f, round_name: e.target.value }))}
                placeholder="Technical Round 1"
              />
            </div>
            <div>
              <Label htmlFor="mode">Mode</Label>
              <Select
                id="mode"
                value={form.mode}
                onChange={(e) => setForm((f) => ({ ...f, mode: e.target.value as InterviewMode }))}
              >
                {MODE_OPTIONS.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="interviewer_name">Interviewer</Label>
              <Input
                id="interviewer_name"
                value={form.interviewer_name}
                onChange={(e) => setForm((f) => ({ ...f, interviewer_name: e.target.value }))}
                placeholder="optional"
              />
            </div>
            <div>
              <Label htmlFor="scheduled_at">Scheduled at</Label>
              <Input
                id="scheduled_at"
                type="datetime-local"
                value={form.scheduled_at}
                onChange={(e) => setForm((f) => ({ ...f, scheduled_at: e.target.value }))}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" size="sm" variant="ghost" onClick={() => setShowForm(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Saving…" : "Save round"}
            </Button>
          </div>
        </form>
      )}

      <div className="mt-4">
        {isLoading ? (
          <p className="text-sm text-ink-soft">Loading…</p>
        ) : !rounds || rounds.length === 0 ? (
          <p className="text-sm text-ink-soft">No interview rounds logged yet.</p>
        ) : (
          <div className="space-y-3">
            {rounds.map((round) => (
              <div key={round.id} className="ledger-row flex items-start justify-between gap-3 pt-3 first:pt-0">
                <div className="min-w-0">
                  <p className="font-medium text-ink">{round.round_name}</p>
                  <p className="mt-0.5 font-mono text-xs text-ink-soft">
                    {INTERVIEW_MODE_LABELS[round.mode]}
                    {round.interviewer_name ? ` · ${round.interviewer_name}` : ""}
                    {round.scheduled_at ? ` · ${formatDateTime(round.scheduled_at)}` : ""}
                  </p>
                  {round.feedback && <p className="mt-1 text-sm text-ink-soft">{round.feedback}</p>}
                </div>
                <div className="flex flex-shrink-0 items-center gap-2">
                  <Select
                    value={round.outcome}
                    onChange={(e) =>
                      outcomeMutation.mutate({ roundId: round.id, outcome: e.target.value as InterviewOutcome })
                    }
                    className={`w-auto text-xs ${OUTCOME_COLOR[round.outcome]}`}
                  >
                    {OUTCOME_OPTIONS.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </Select>
                  <button
                    onClick={() => deleteMutation.mutate(round.id)}
                    className="text-ink-soft hover:text-stamp-red"
                    aria-label="Delete round"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
