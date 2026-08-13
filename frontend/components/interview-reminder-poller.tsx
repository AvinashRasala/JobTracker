"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { api } from "@/lib/api";
import { areRemindersEnabled, fireInterviewReminder, getNotificationPermission } from "@/lib/notifications";

const REMINDER_WINDOW_HOURS = 2;
const POLL_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

/**
 * Mounted once in the app shell. Silently polls for interviews in the
 * next couple hours and fires a browser Notification for each one not
 * already notified this session. Renders nothing.
 */
export function InterviewReminderPoller() {
  const enabled = typeof window !== "undefined" && areRemindersEnabled() && getNotificationPermission() === "granted";

  const { data } = useQuery({
    queryKey: ["upcoming-interviews-poll"],
    queryFn: () => api.upcomingInterviews(REMINDER_WINDOW_HOURS),
    enabled,
    refetchInterval: enabled ? POLL_INTERVAL_MS : false,
  });

  useEffect(() => {
    if (!data) return;
    for (const interview of data) {
      fireInterviewReminder(interview.role_title, interview.company_name, interview.scheduled_at, interview.id);
    }
  }, [data]);

  return null;
}
