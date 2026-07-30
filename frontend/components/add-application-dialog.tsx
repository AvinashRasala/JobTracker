"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Dialog } from "@/components/ui/dialog";
import { Input, Label } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";

const PLATFORM_OPTIONS = [
  ["linkedin", "LinkedIn Jobs"],
  ["indeed", "Indeed"],
  ["naukri", "Naukri"],
  ["foundit", "Foundit (Monster)"],
  ["wellfound", "Wellfound"],
  ["glassdoor", "Glassdoor"],
  ["instahyre", "Instahyre"],
  ["hirist", "Hirist"],
  ["cutshort", "Cutshort"],
  ["internshala", "Internshala"],
  ["dice", "Dice"],
  ["ziprecruiter", "ZipRecruiter"],
  ["lever", "Lever"],
  ["greenhouse", "Greenhouse"],
  ["workday", "Workday"],
  ["smartrecruiters", "SmartRecruiters"],
  ["company-site", "Company Career Page"],
  ["manual", "Manual Entry"],
];

export function AddApplicationDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({
    role_title: "",
    company_name: "",
    platform_slug: "manual",
    location: "",
    job_url: "",
    work_type: "unknown",
    employment_type: "unknown",
    expected_ctc: "",
    notice_period_days: "",
    referred_by_name: "",
    referred_by_email: "",
    referred_by_relationship: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [showMore, setShowMore] = useState(false);

  const initialForm = {
    role_title: "",
    company_name: "",
    platform_slug: "manual",
    location: "",
    job_url: "",
    work_type: "unknown",
    employment_type: "unknown",
    expected_ctc: "",
    notice_period_days: "",
    referred_by_name: "",
    referred_by_email: "",
    referred_by_relationship: "",
  };

  const mutation = useMutation({
    mutationFn: () => {
      const payload: Record<string, unknown> = { ...form };
      if (form.expected_ctc) payload.expected_ctc = Number(form.expected_ctc);
      else delete payload.expected_ctc;
      if (form.notice_period_days) payload.notice_period_days = Number(form.notice_period_days);
      else delete payload.notice_period_days;
      if (!form.referred_by_name) delete payload.referred_by_name;
      if (!form.referred_by_email) delete payload.referred_by_email;
      if (!form.referred_by_relationship) delete payload.referred_by_relationship;
      return api.createApplication(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["status-distribution"] });
      queryClient.invalidateQueries({ queryKey: ["platform-distribution"] });
      queryClient.invalidateQueries({ queryKey: ["applications-per-day"] });
      queryClient.invalidateQueries({ queryKey: ["needs-follow-up"] });
      setForm(initialForm);
      setShowMore(false);
      onClose();
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : "Could not save this application."),
  });

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  return (
    <Dialog open={open} onClose={onClose} title="Log an application">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          mutation.mutate();
        }}
        className="space-y-4"
      >
        <div>
          <Label htmlFor="role_title">Role</Label>
          <Input id="role_title" required value={form.role_title} onChange={update("role_title")} placeholder="Senior Backend Engineer" />
        </div>
        <div>
          <Label htmlFor="company_name">Company</Label>
          <Input id="company_name" required value={form.company_name} onChange={update("company_name")} placeholder="Acme Corp" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="platform_slug">Platform</Label>
            <Select id="platform_slug" value={form.platform_slug} onChange={update("platform_slug")}>
              {PLATFORM_OPTIONS.map(([slug, label]) => (
                <option key={slug} value={slug}>
                  {label}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="location">Location</Label>
            <Input id="location" value={form.location} onChange={update("location")} placeholder="Bangalore" />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="work_type">Work type</Label>
            <Select id="work_type" value={form.work_type} onChange={update("work_type")}>
              <option value="unknown">Unspecified</option>
              <option value="remote">Remote</option>
              <option value="hybrid">Hybrid</option>
              <option value="onsite">Onsite</option>
            </Select>
          </div>
          <div>
            <Label htmlFor="employment_type">Employment type</Label>
            <Select id="employment_type" value={form.employment_type} onChange={update("employment_type")}>
              <option value="unknown">Unspecified</option>
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
              <option value="freelance">Freelance</option>
            </Select>
          </div>
        </div>
        <div>
          <Label htmlFor="job_url">Job URL (optional)</Label>
          <Input id="job_url" type="url" value={form.job_url} onChange={update("job_url")} placeholder="https://…" />
        </div>

        <button
          type="button"
          onClick={() => setShowMore((s) => !s)}
          className="flex items-center gap-1 text-xs font-medium uppercase tracking-wide text-ink-soft hover:text-ledger"
        >
          {showMore ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          More details — CTC &amp; referral
        </button>

        {showMore && (
          <div className="space-y-4 rounded-md border border-dashed border-hairline p-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="expected_ctc">Expected CTC (optional)</Label>
                <Input
                  id="expected_ctc"
                  type="number"
                  value={form.expected_ctc}
                  onChange={update("expected_ctc")}
                  placeholder="e.g. 1500000"
                />
              </div>
              <div>
                <Label htmlFor="notice_period_days">Notice period (days)</Label>
                <Input
                  id="notice_period_days"
                  type="number"
                  value={form.notice_period_days}
                  onChange={update("notice_period_days")}
                  placeholder="e.g. 30"
                />
              </div>
            </div>
            <p className="text-xs text-ink-soft">
              Freshers: leave these blank. Experienced: fill in what you're expecting or negotiating.
            </p>
            <div>
              <Label htmlFor="referred_by_name">Referred by (optional)</Label>
              <Input
                id="referred_by_name"
                value={form.referred_by_name}
                onChange={update("referred_by_name")}
                placeholder="Name of the person who referred you"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="referred_by_email">Referrer email</Label>
                <Input
                  id="referred_by_email"
                  type="email"
                  value={form.referred_by_email}
                  onChange={update("referred_by_email")}
                  placeholder="optional"
                />
              </div>
              <div>
                <Label htmlFor="referred_by_relationship">Relationship</Label>
                <Input
                  id="referred_by_relationship"
                  value={form.referred_by_relationship}
                  onChange={update("referred_by_relationship")}
                  placeholder="e.g. Ex-colleague, Friend"
                />
              </div>
            </div>
          </div>
        )}

        {error && <p className="text-sm text-stamp-red">{error}</p>}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Saving…" : "Save application"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
