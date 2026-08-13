"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Sparkles, Copy, Check } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";

type ResultKind = "match_score" | "cover_letter" | "follow_up_email" | null;

export function AiFeaturesPanel({ applicationId }: { applicationId: string }) {
  const [activeResult, setActiveResult] = useState<ResultKind>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const matchScoreMutation = useMutation({
    mutationFn: () => api.aiMatchScore(applicationId),
    onSuccess: () => {
      setActiveResult("match_score");
      setError(null);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not generate match score."),
  });

  const coverLetterMutation = useMutation({
    mutationFn: () => api.aiCoverLetter(applicationId),
    onSuccess: () => {
      setActiveResult("cover_letter");
      setError(null);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not generate cover letter."),
  });

  const followUpMutation = useMutation({
    mutationFn: () => api.aiFollowUpEmail(applicationId),
    onSuccess: () => {
      setActiveResult("follow_up_email");
      setError(null);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not generate follow-up email."),
  });

  const anyPending = matchScoreMutation.isPending || coverLetterMutation.isPending || followUpMutation.isPending;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <Card className="p-5">
      <div className="flex items-center gap-2">
        <Sparkles size={16} className="text-ledger" />
        <h3 className="font-display text-sm font-semibold text-ink">AI features</h3>
      </div>
      <p className="mt-1 text-sm text-ink-soft">
        Uses your resume text (Settings) and this application's job description. Requires the
        server to have an OpenAI API key configured.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button size="sm" variant="secondary" onClick={() => matchScoreMutation.mutate()} disabled={anyPending}>
          {matchScoreMutation.isPending ? "Scoring…" : "Resume match score"}
        </Button>
        <Button size="sm" variant="secondary" onClick={() => coverLetterMutation.mutate()} disabled={anyPending}>
          {coverLetterMutation.isPending ? "Writing…" : "Generate cover letter"}
        </Button>
        <Button size="sm" variant="secondary" onClick={() => followUpMutation.mutate()} disabled={anyPending}>
          {followUpMutation.isPending ? "Drafting…" : "Draft follow-up email"}
        </Button>
      </div>

      {error && <p className="mt-3 text-sm text-stamp-red">{error}</p>}

      {activeResult === "match_score" && matchScoreMutation.data && (
        <div className="mt-4 rounded-md border border-dashed border-hairline p-4">
          <div className="flex items-center gap-3">
            <span className="font-display text-3xl font-bold text-ledger">{matchScoreMutation.data.score}</span>
            <span className="text-sm text-ink-soft">/ 100 match</span>
          </div>
          <p className="mt-2 text-sm text-ink">{matchScoreMutation.data.explanation}</p>
          {matchScoreMutation.data.matching_skills.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium uppercase tracking-wide text-ink-soft">Matching</p>
              <p className="mt-1 text-sm text-stamp-green">{matchScoreMutation.data.matching_skills.join(", ")}</p>
            </div>
          )}
          {matchScoreMutation.data.missing_skills.length > 0 && (
            <div className="mt-2">
              <p className="text-xs font-medium uppercase tracking-wide text-ink-soft">Gaps</p>
              <p className="mt-1 text-sm text-stamp-amber">{matchScoreMutation.data.missing_skills.join(", ")}</p>
            </div>
          )}
        </div>
      )}

      {activeResult === "cover_letter" && coverLetterMutation.data && (
        <div className="mt-4 rounded-md border border-dashed border-hairline p-4">
          <div className="mb-2 flex justify-end">
            <button
              onClick={() => copyToClipboard(coverLetterMutation.data!.cover_letter)}
              className="flex items-center gap-1 text-xs text-ink-soft hover:text-ledger"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />} {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <p className="whitespace-pre-wrap text-sm text-ink">{coverLetterMutation.data.cover_letter}</p>
        </div>
      )}

      {activeResult === "follow_up_email" && followUpMutation.data && (
        <div className="mt-4 rounded-md border border-dashed border-hairline p-4">
          <div className="mb-2 flex justify-end">
            <button
              onClick={() => copyToClipboard(followUpMutation.data!.email)}
              className="flex items-center gap-1 text-xs text-ink-soft hover:text-ledger"
            >
              {copied ? <Check size={12} /> : <Copy size={12} />} {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <p className="whitespace-pre-wrap text-sm text-ink">{followUpMutation.data.email}</p>
        </div>
      )}
    </Card>
  );
}
