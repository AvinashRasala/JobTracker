"use client";

import type {
  Application,
  ApplicationListResponse,
  DashboardStats,
  StatusCount,
  PlatformCount,
  DailyCount,
  ApplicationStatus,
  InterviewRound,
  OfferComparisonItem,
  UserProfile,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "jobtrack_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // no JSON body
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export function resolveAssetUrl(path: string | null): string | null {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${API_URL}${path}`;
}

export const api = {
  register: (email: string, password: string, full_name: string) =>
    request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: async (email: string, password: string) => {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    const res = await fetch(`${API_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new ApiError(res.status, detail.detail || "Login failed");
    }
    const data = await res.json();
    setToken(data.access_token);
    return data;
  },

  reactivate: async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/api/auth/reactivate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: "Reactivation failed" }));
      throw new ApiError(res.status, detail.detail || "Reactivation failed");
    }
    const data = await res.json();
    setToken(data.access_token);
    return data;
  },

  listApplications: (params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request<ApplicationListResponse>(`/api/applications${qs ? `?${qs}` : ""}`);
  },

  createApplication: (payload: Record<string, unknown>) =>
    request<Application>("/api/applications", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateApplication: (id: string, payload: Record<string, unknown>) =>
    request<Application>(`/api/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  updateStatus: (id: string, status: ApplicationStatus, note?: string) =>
    request<Application>(`/api/applications/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status, note }),
    }),

  deleteApplication: (id: string) =>
    request<void>(`/api/applications/${id}`, { method: "DELETE" }),

  getApplication: (id: string) => request<Application>(`/api/applications/${id}`),

  needsFollowUp: () => request<ApplicationListResponse>("/api/applications/needs-follow-up"),

  compareOffers: () => request<OfferComparisonItem[]>("/api/applications/offers/compare"),

  listInterviewRounds: (applicationId: string) =>
    request<InterviewRound[]>(`/api/applications/${applicationId}/interviews`),

  createInterviewRound: (applicationId: string, payload: Record<string, unknown>) =>
    request<InterviewRound>(`/api/applications/${applicationId}/interviews`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  updateInterviewRound: (applicationId: string, roundId: string, payload: Record<string, unknown>) =>
    request<InterviewRound>(`/api/applications/${applicationId}/interviews/${roundId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteInterviewRound: (applicationId: string, roundId: string) =>
    request<void>(`/api/applications/${applicationId}/interviews/${roundId}`, { method: "DELETE" }),

  getProfile: () => request<UserProfile>("/api/auth/me"),

  updateProfile: (payload: Record<string, unknown>) =>
    request<UserProfile>("/api/auth/me", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  uploadAvatar: async (file: File) => {
    const token = getToken();
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_URL}/api/auth/me/avatar`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    });
    if (!res.ok) {
      const detail = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new ApiError(res.status, detail.detail || "Upload failed");
    }
    return res.json() as Promise<UserProfile>;
  },

  deleteAvatar: () => request<UserProfile>("/api/auth/me/avatar", { method: "DELETE" }),

  changePassword: (currentPassword: string, newPassword: string) =>
    request<void>("/api/auth/me/password", {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    }),

  deactivateAccount: () => request<void>("/api/auth/me/deactivate", { method: "POST" }),

  deleteAccount: (password: string) =>
    request<void>("/api/auth/me/delete", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  exportApplicationsCsv: async () => {
    const token = getToken();
    const res = await fetch(`${API_URL}/api/applications/export.csv`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError(res.status, "Export failed");
    return res.blob();
  },

  gmailStatus: () => request<{ connected: boolean; last_synced_at: string | null }>("/api/gmail/status"),

  gmailConnect: () => request<{ auth_url: string }>("/api/gmail/connect"),

  gmailSync: () =>
    request<{ new_applications: number; status_updates: number; ignored: number; errors: string[] }>(
      "/api/gmail/sync",
      { method: "POST" }
    ),

  gmailDisconnect: () => request<void>("/api/gmail/disconnect", { method: "DELETE" }),

  gmailRecentChanges: () =>
    request<
      {
        status_history_id: string;
        application_id: string;
        role_title: string;
        company_name: string | null;
        from_status: string | null;
        to_status: string;
        note: string | null;
        created_at: string;
      }[]
    >("/api/gmail/recent-changes"),

  gmailSkippedEmails: () =>
    request<{ gmail_message_id: string; subject: string | null; sender: string | null; created_at: string }[]>(
      "/api/gmail/skipped-emails"
    ),

  dashboardStats: () => request<DashboardStats>("/api/dashboard/stats"),
  statusDistribution: () => request<StatusCount[]>("/api/dashboard/status-distribution"),
  platformDistribution: () => request<PlatformCount[]>("/api/dashboard/platform-distribution"),
  applicationsPerDay: (days = 30) =>
    request<DailyCount[]>(`/api/dashboard/applications-per-day?days=${days}`),
};

export { ApiError };
