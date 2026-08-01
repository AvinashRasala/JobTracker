/**
 * MV3 service worker. Owns the JWT token and API base URL (both in
 * chrome.storage.local), and is the only place that actually talks to
 * the JobTrack AI backend -- content scripts just send it messages.
 */

const DEFAULT_API_BASE_URL = "http://localhost:8000";

async function getSettings() {
  const { apiBaseUrl, token } = await chrome.storage.local.get(["apiBaseUrl", "token"]);
  return { apiBaseUrl: apiBaseUrl || DEFAULT_API_BASE_URL, token: token || null };
}

async function apiRequest(path, options = {}) {
  const { apiBaseUrl, token } = await getSettings();
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
  const res = await fetch(`${apiBaseUrl}${path}`, { ...options, headers });
  return res;
}

async function handleLogin(email, password) {
  const { apiBaseUrl } = await getSettings();
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  const res = await fetch(`${apiBaseUrl}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Login failed" }));
    return { ok: false, error: data.detail || "Login failed" };
  }
  const data = await res.json();
  await chrome.storage.local.set({ token: data.access_token });
  return { ok: true };
}

async function handleApplyDetected(jobInfo) {
  const { token } = await getSettings();
  if (!token) return { needsAuth: true };

  // Use the job URL (truncated to fit the backend's column limit) as the
  // dedup key so re-clicking Apply, or a page re-render firing twice,
  // doesn't create duplicate entries.
  const externalId = (jobInfo.job_url || "").slice(0, 250);

  try {
    const res = await apiRequest("/api/applications", {
      method: "POST",
      body: JSON.stringify({
        role_title: jobInfo.role_title,
        company_name: jobInfo.company_name,
        platform_slug: jobInfo.platform_slug,
        job_url: jobInfo.job_url,
        external_application_id: externalId || undefined,
        source: "chrome_extension",
      }),
    });

    if (res.status === 201) return { ok: true };
    if (res.status === 409) return { duplicate: true };
    if (res.status === 401) return { needsAuth: true };

    const data = await res.json().catch(() => ({}));
    return { ok: false, error: data.detail || `HTTP ${res.status}` };
  } catch (err) {
    return { ok: false, error: err.message || "Network error" };
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "APPLY_DETECTED") {
    handleApplyDetected(message.jobInfo).then(sendResponse);
    return true; // keep the message channel open for the async response
  }
  if (message.type === "LOGIN") {
    handleLogin(message.email, message.password).then(sendResponse);
    return true;
  }
  if (message.type === "LOGOUT") {
    chrome.storage.local.remove(["token"]).then(() => sendResponse({ ok: true }));
    return true;
  }
  if (message.type === "GET_STATUS") {
    getSettings().then(({ apiBaseUrl, token }) => sendResponse({ apiBaseUrl, connected: !!token }));
    return true;
  }
  if (message.type === "SET_API_BASE_URL") {
    chrome.storage.local.set({ apiBaseUrl: message.apiBaseUrl }).then(() => sendResponse({ ok: true }));
    return true;
  }
  return false;
});
