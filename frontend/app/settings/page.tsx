"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Camera, Trash2, Mail, RefreshCw, CheckCircle2, Undo2, ChevronDown, ChevronRight } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/input";
import { PasswordInput } from "@/components/ui/password-input";
import { api, resolveAssetUrl, ApiError, clearToken } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { ApplicationStatus, STATUS_LABELS } from "@/lib/types";
import { formatDateTime } from "@/lib/dates";

export default function SettingsPage() {
  return (
    <Suspense fallback={null}>
      <SettingsPageInner />
    </Suspense>
  );
}

function SettingsPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { logout } = useAuth();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: profile, isLoading } = useQuery({ queryKey: ["profile"], queryFn: api.getProfile });

  // --- Gmail integration ---
  const { data: gmailStatus } = useQuery({ queryKey: ["gmail-status"], queryFn: api.gmailStatus });
  const [gmailMessage, setGmailMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [syncErrors, setSyncErrors] = useState<string[]>([]);

  useEffect(() => {
    const gmailParam = searchParams.get("gmail");
    if (!gmailParam) return;
    if (gmailParam === "connected") {
      setGmailMessage({ type: "success", text: "Gmail connected successfully." });
      queryClient.invalidateQueries({ queryKey: ["gmail-status"] });
    } else if (gmailParam === "no_refresh_token") {
      setGmailMessage({
        type: "error",
        text: "Google didn't grant a fresh permission token. Click Disconnect below (if shown) then Connect Gmail again.",
      });
    } else {
      setGmailMessage({ type: "error", text: "Couldn't connect Gmail. Please try again." });
    }
    router.replace("/settings");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const connectMutation = useMutation({
    mutationFn: api.gmailConnect,
    onSuccess: (data) => {
      window.location.href = data.auth_url;
    },
    onError: (err) => setGmailMessage({ type: "error", text: err instanceof ApiError ? err.message : "Could not start Gmail connection." }),
  });

  const syncMutation = useMutation({
    mutationFn: api.gmailSync,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["gmail-status"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["gmail-recent-changes"] });
      queryClient.invalidateQueries({ queryKey: ["gmail-skipped-emails"] });
      const summary = `Synced: ${data.new_applications} new application(s), ${data.status_updates} status update(s), ${data.ignored} skipped.`;
      const errorNote = data.errors && data.errors.length > 0 ? ` (${data.errors.length} email(s) had errors — see below)` : "";
      setSyncResult(summary + errorNote);
      setSyncErrors(data.errors || []);
    },
    onError: (err) => setGmailMessage({ type: "error", text: err instanceof ApiError ? err.message : "Sync failed." }),
  });

  const disconnectGmailMutation = useMutation({
    mutationFn: api.gmailDisconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gmail-status"] });
      setSyncResult(null);
      setSyncErrors([]);
    },
  });

  const { data: recentChanges, isLoading: recentChangesLoading } = useQuery({
    queryKey: ["gmail-recent-changes"],
    queryFn: api.gmailRecentChanges,
    enabled: !!gmailStatus?.connected,
  });

  const [showSkipped, setShowSkipped] = useState(false);
  const { data: skippedEmails, isLoading: skippedLoading } = useQuery({
    queryKey: ["gmail-skipped-emails"],
    queryFn: api.gmailSkippedEmails,
    enabled: !!gmailStatus?.connected && showSkipped,
  });

  const revertMutation = useMutation({
    mutationFn: ({ applicationId, toStatus }: { applicationId: string; toStatus: string }) =>
      api.updateStatus(applicationId, toStatus as ApplicationStatus),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["gmail-recent-changes"] });
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    },
  });

  const [profileForm, setProfileForm] = useState({ full_name: "", phone_number: "" });
  const [profileSaved, setProfileSaved] = useState(false);

  useEffect(() => {
    if (profile) {
      setProfileForm({ full_name: profile.full_name || "", phone_number: profile.phone_number || "" });
    }
  }, [profile]);

  const invalidateProfile = () => queryClient.invalidateQueries({ queryKey: ["profile"] });

  const profileMutation = useMutation({
    mutationFn: () => api.updateProfile(profileForm),
    onSuccess: () => {
      invalidateProfile();
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 2000);
    },
  });

  const avatarUploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadAvatar(file),
    onSuccess: invalidateProfile,
  });

  const avatarDeleteMutation = useMutation({
    mutationFn: () => api.deleteAvatar(),
    onSuccess: invalidateProfile,
  });

  // --- Password change ---
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [pwError, setPwError] = useState<string | null>(null);
  const [pwSuccess, setPwSuccess] = useState(false);

  const passwordMutation = useMutation({
    mutationFn: () => api.changePassword(pwForm.current, pwForm.next),
    onSuccess: () => {
      setPwForm({ current: "", next: "", confirm: "" });
      setPwSuccess(true);
      setPwError(null);
      setTimeout(() => setPwSuccess(false), 2500);
    },
    onError: (err) => setPwError(err instanceof ApiError ? err.message : "Could not change password."),
  });

  const onSubmitPassword = (e: React.FormEvent) => {
    e.preventDefault();
    setPwError(null);
    if (pwForm.next.length < 8) {
      setPwError("New password must be at least 8 characters.");
      return;
    }
    if (pwForm.next !== pwForm.confirm) {
      setPwError("New passwords don't match.");
      return;
    }
    passwordMutation.mutate();
  };

  // --- Danger zone ---
  const [deletePassword, setDeletePassword] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const deactivateMutation = useMutation({
    mutationFn: () => api.deactivateAccount(),
    onSuccess: () => {
      clearToken();
      router.push("/login");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteAccount(deletePassword),
    onSuccess: () => {
      clearToken();
      router.push("/register");
    },
    onError: (err) => setDeleteError(err instanceof ApiError ? err.message : "Could not delete account."),
  });

  if (isLoading || !profile) {
    return (
      <AppShell>
        <p className="text-sm text-ink-soft">Loading…</p>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mb-6">
        <p className="postmark w-fit text-ledger">Account</p>
        <h2 className="mt-2 font-display text-2xl font-bold text-ink">Settings</h2>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Profile */}
        <Card className="p-5">
          <h3 className="font-display text-sm font-semibold text-ink">Profile</h3>

          <div className="mt-4 flex items-center gap-4">
            <div className="relative h-16 w-16 flex-shrink-0 overflow-hidden rounded-full border border-hairline bg-paper">
              {profile.avatar_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={resolveAssetUrl(profile.avatar_url) || ""} alt="Profile" className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full items-center justify-center font-display text-lg text-ink-soft">
                  {(profile.full_name || profile.email)[0]?.toUpperCase()}
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) avatarUploadMutation.mutate(file);
                }}
              />
              <Button type="button" size="sm" variant="secondary" onClick={() => fileInputRef.current?.click()}>
                <Camera size={14} /> {profile.avatar_url ? "Change" : "Upload"}
              </Button>
              {profile.avatar_url && (
                <Button type="button" size="sm" variant="ghost" onClick={() => avatarDeleteMutation.mutate()}>
                  Remove
                </Button>
              )}
            </div>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              profileMutation.mutate();
            }}
            className="mt-5 space-y-4"
          >
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={profile.email} disabled className="bg-paper text-ink-soft" />
            </div>
            <div>
              <Label htmlFor="full_name">Full name</Label>
              <Input
                id="full_name"
                value={profileForm.full_name}
                onChange={(e) => setProfileForm((f) => ({ ...f, full_name: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="phone_number">Phone number</Label>
              <Input
                id="phone_number"
                type="tel"
                value={profileForm.phone_number}
                onChange={(e) => setProfileForm((f) => ({ ...f, phone_number: e.target.value }))}
                placeholder="+91 98765 43210"
              />
            </div>
            <div className="flex items-center gap-3">
              <Button type="submit" size="sm" disabled={profileMutation.isPending}>
                {profileMutation.isPending ? "Saving…" : "Save profile"}
              </Button>
              {profileSaved && <span className="text-xs text-stamp-green">Saved</span>}
            </div>
          </form>
        </Card>

        {/* Password */}
        <Card className="p-5">
          <h3 className="font-display text-sm font-semibold text-ink">Change password</h3>
          <form onSubmit={onSubmitPassword} className="mt-4 space-y-4">
            <div>
              <Label htmlFor="current_password">Current password</Label>
              <PasswordInput
                id="current_password"
                required
                value={pwForm.current}
                onChange={(e) => setPwForm((f) => ({ ...f, current: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="new_password">New password</Label>
              <PasswordInput
                id="new_password"
                required
                minLength={8}
                value={pwForm.next}
                onChange={(e) => setPwForm((f) => ({ ...f, next: e.target.value }))}
                placeholder="At least 8 characters"
              />
            </div>
            <div>
              <Label htmlFor="confirm_password">Confirm new password</Label>
              <PasswordInput
                id="confirm_password"
                required
                value={pwForm.confirm}
                onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))}
              />
            </div>
            {pwError && <p className="text-sm text-stamp-red">{pwError}</p>}
            {pwSuccess && <p className="text-sm text-stamp-green">Password updated.</p>}
            <Button type="submit" size="sm" disabled={passwordMutation.isPending}>
              {passwordMutation.isPending ? "Updating…" : "Update password"}
            </Button>
          </form>
        </Card>

        {/* Gmail Integration */}
        <Card className="p-5 lg:col-span-2">
          <div className="flex items-center gap-2">
            <Mail size={16} className="text-ledger" />
            <h3 className="font-display text-sm font-semibold text-ink">Gmail integration</h3>
          </div>
          <p className="mt-1 text-sm text-ink-soft">
            Automatically detect application confirmations and status updates (interviews, offers, rejections)
            from your inbox. We only read email metadata and content needed to match job applications — nothing
            is sent or modified.
          </p>

          {gmailMessage && (
            <p className={`mt-3 text-sm ${gmailMessage.type === "success" ? "text-stamp-green" : "text-stamp-red"}`}>
              {gmailMessage.text}
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-3">
            {gmailStatus?.connected ? (
              <>
                <span className="flex items-center gap-1.5 text-sm text-stamp-green">
                  <CheckCircle2 size={16} /> Connected
                  {gmailStatus.last_synced_at && (
                    <span className="text-ink-soft">
                      · last synced {formatDateTime(gmailStatus.last_synced_at)}
                    </span>
                  )}
                </span>
                <Button size="sm" variant="secondary" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
                  <RefreshCw size={14} /> {syncMutation.isPending ? "Syncing…" : "Sync now"}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => disconnectGmailMutation.mutate()}>
                  Disconnect
                </Button>
              </>
            ) : (
              <Button size="sm" onClick={() => connectMutation.mutate()} disabled={connectMutation.isPending}>
                <Mail size={14} /> {connectMutation.isPending ? "Redirecting…" : "Connect Gmail"}
              </Button>
            )}
          </div>
          {syncResult && <p className="mt-3 text-sm text-ink-soft">{syncResult}</p>}
          {syncErrors.length > 0 && (
            <ul className="mt-2 space-y-1 text-xs text-stamp-red">
              {syncErrors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          )}
        </Card>

        {/* Recent Gmail-caused changes, for auditing/reverting */}
        {gmailStatus?.connected && recentChanges && recentChanges.length > 0 && (
          <Card className="p-5 lg:col-span-2">
            <h3 className="font-display text-sm font-semibold text-ink">Recent Gmail changes</h3>
            <p className="mt-1 text-sm text-ink-soft">
              Every status change the Gmail sync has made. If anything looks wrong, revert it back to its
              previous status.
            </p>
            <div className="mt-4 space-y-3">
              {recentChangesLoading ? (
                <p className="text-sm text-ink-soft">Loading…</p>
              ) : (
                recentChanges.map((change) => (
                  <div
                    key={change.status_history_id}
                    className="ledger-row flex flex-col gap-2 pt-3 first:pt-0 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="min-w-0">
                      <p className="font-medium text-ink">
                        {change.role_title}
                        {change.company_name ? ` · ${change.company_name}` : ""}
                      </p>
                      <p className="mt-0.5 font-mono text-xs text-ink-soft">
                        {change.from_status ? STATUS_LABELS[change.from_status as ApplicationStatus] : "—"} →{" "}
                        {STATUS_LABELS[change.to_status as ApplicationStatus]} ·{" "}
                        {formatDateTime(change.created_at)}
                      </p>
                      {change.note && <p className="mt-0.5 text-xs text-ink-soft">{change.note}</p>}
                    </div>
                    {change.from_status && (
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() =>
                          revertMutation.mutate({ applicationId: change.application_id, toStatus: change.from_status! })
                        }
                        disabled={revertMutation.isPending}
                      >
                        <Undo2 size={14} /> Revert to {STATUS_LABELS[change.from_status as ApplicationStatus]}
                      </Button>
                    )}
                  </div>
                ))
              )}
            </div>
          </Card>
        )}

        {/* Skipped emails, for transparency into what the sync deliberately didn't act on */}
        {gmailStatus?.connected && (
          <Card className="p-5 lg:col-span-2">
            <button
              type="button"
              onClick={() => setShowSkipped((s) => !s)}
              className="flex w-full items-center gap-1.5 text-left"
            >
              {showSkipped ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              <h3 className="font-display text-sm font-semibold text-ink">Recently skipped emails</h3>
            </button>
            <p className="mt-1 text-sm text-ink-soft">
              Emails the sync found but didn't act on — either the wording wasn't specific enough to be sure it's a
              real confirmation/status update, or it couldn't be confidently matched to one of your applications.
              This is usually correct behavior, but check here if you think something real got missed.
            </p>

            {showSkipped && (
              <div className="mt-4">
                {skippedLoading ? (
                  <p className="text-sm text-ink-soft">Loading…</p>
                ) : !skippedEmails || skippedEmails.length === 0 ? (
                  <p className="text-sm text-ink-soft">Nothing skipped in your recent sync history.</p>
                ) : (
                  <div className="space-y-2">
                    {skippedEmails.map((email, i) => (
                      <div key={i} className="ledger-row pt-2 first:pt-0">
                        <p className="text-sm text-ink">{email.subject || "(no subject)"}</p>
                        <p className="mt-0.5 font-mono text-xs text-ink-soft">
                          {email.sender || "unknown sender"} · {formatDateTime(email.created_at)}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </Card>
        )}

        {/* Danger zone */}
        <Card className="border-stamp-red/40 p-5 lg:col-span-2">
          <h3 className="font-display text-sm font-semibold text-stamp-red">Danger zone</h3>

          <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-medium text-ink">Deactivate account</p>
              <p className="mt-0.5 text-sm text-ink-soft">
                Signs you out and blocks login until you reactivate with your email and password. Your data is kept.
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() => {
                if (confirm("Deactivate your account? You can reactivate any time by signing in again.")) {
                  deactivateMutation.mutate();
                }
              }}
              disabled={deactivateMutation.isPending}
            >
              Deactivate
            </Button>
          </div>

          <div className="mt-6 border-t border-hairline pt-6">
            <p className="text-sm font-medium text-ink">Delete account</p>
            <p className="mt-0.5 text-sm text-ink-soft">
              Permanently deletes your account and every application, interview round, and note you've logged. This
              cannot be undone.
            </p>

            {!showDeleteConfirm ? (
              <Button variant="danger" className="mt-3" onClick={() => setShowDeleteConfirm(true)}>
                <Trash2 size={14} /> Delete my account
              </Button>
            ) : (
              <div className="mt-3 max-w-sm space-y-3 rounded-md border border-dashed border-stamp-red/40 p-3">
                <Label htmlFor="delete_password">Confirm your password to permanently delete your account</Label>
                <PasswordInput
                  id="delete_password"
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                />
                {deleteError && <p className="text-sm text-stamp-red">{deleteError}</p>}
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setShowDeleteConfirm(false);
                      setDeletePassword("");
                      setDeleteError(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => deleteMutation.mutate()}
                    disabled={deleteMutation.isPending || !deletePassword}
                  >
                    {deleteMutation.isPending ? "Deleting…" : "Permanently delete"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
