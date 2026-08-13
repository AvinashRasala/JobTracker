"use client";

/**
 * Browser Notification API helpers for interview reminders. This is
 * intentionally simple: it only works while the app tab is open (a poller
 * checks upcoming interviews periodically and fires a Notification). This
 * is NOT a true background push notification -- that would need a service
 * worker, VAPID keys, and a backend push subscription store, which is a
 * meaningfully bigger feature. Documented clearly in Settings so this
 * doesn't overpromise.
 */

const REMINDERS_ENABLED_KEY = "jobtrack_reminders_enabled";
const NOTIFIED_KEY = "jobtrack_notified_interview_ids";

export function getNotificationPermission(): "default" | "granted" | "denied" | "unsupported" {
  if (typeof window === "undefined" || !("Notification" in window)) return "unsupported";
  return Notification.permission;
}

export async function requestNotificationPermission(): Promise<boolean> {
  if (typeof window === "undefined" || !("Notification" in window)) return false;
  const result = await Notification.requestPermission();
  return result === "granted";
}

export function areRemindersEnabled(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(REMINDERS_ENABLED_KEY) === "true";
}

export function setRemindersEnabled(enabled: boolean) {
  if (typeof window === "undefined") return;
  localStorage.setItem(REMINDERS_ENABLED_KEY, enabled ? "true" : "false");
}

function getNotifiedIds(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = localStorage.getItem(NOTIFIED_KEY);
    return new Set(raw ? JSON.parse(raw) : []);
  } catch {
    return new Set();
  }
}

function markNotified(id: string) {
  const ids = getNotifiedIds();
  ids.add(id);
  localStorage.setItem(NOTIFIED_KEY, JSON.stringify([...ids]));
}

export function fireInterviewReminder(roleTitle: string, companyName: string | null, scheduledAt: string, interviewId: string) {
  const notified = getNotifiedIds();
  if (notified.has(interviewId)) return; // don't repeat within this browser

  if (getNotificationPermission() !== "granted") return;

  const time = new Date(scheduledAt.endsWith("Z") ? scheduledAt : `${scheduledAt}Z`).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  new Notification(`Interview: ${roleTitle}${companyName ? ` at ${companyName}` : ""}`, {
    body: `Scheduled for ${time}`,
    tag: interviewId,
  });

  markNotified(interviewId);
}
