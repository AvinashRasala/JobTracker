/**
 * Runs on job site pages. Listens for clicks anywhere on the page and
 * checks if the clicked element (or a close ancestor) looks like an
 * "Apply" button. If so, extracts job info from the page and sends it
 * to the background service worker, which does the authenticated API call.
 *
 * Depends on extractor.js being loaded first (see manifest.json content_scripts
 * order) -- they share the same content-script global scope.
 */

let lastCapturedUrl = null;
let lastCapturedAt = 0;

document.addEventListener(
  "click",
  (event) => {
    const applyEl = findApplyAncestor(event.target);
    if (!applyEl) return;

    // Debounce: a single "Apply" click often bubbles through multiple
    // nested elements, and some pages fire this more than once when a
    // modal/redirect happens. Ignore repeats within 3 seconds for the
    // same URL.
    const now = Date.now();
    if (window.location.href === lastCapturedUrl && now - lastCapturedAt < 3000) return;
    lastCapturedUrl = window.location.href;
    lastCapturedAt = now;

    const jobInfo = extractJobInfo(document, window.location.href, window.location.hostname);

    chrome.runtime.sendMessage({ type: "APPLY_DETECTED", jobInfo }, (response) => {
      if (chrome.runtime.lastError) {
        console.warn("JobTrack AI: could not reach extension background script.", chrome.runtime.lastError);
        return;
      }
      if (response?.ok) {
        showToast(`JobTrack AI: logged "${jobInfo.role_title}" at ${jobInfo.company_name}`);
      } else if (response?.duplicate) {
        showToast(`JobTrack AI: already logged this application`);
      } else if (response?.needsAuth) {
        showToast("JobTrack AI: sign in via the extension icon to auto-log this application");
      } else {
        showToast(`JobTrack AI: couldn't log this application (${response?.error || "unknown error"})`);
      }
    });
  },
  true // capture phase -- catches clicks even if the site stops propagation later
);

function showToast(message) {
  const existing = document.getElementById("jobtrack-ai-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.id = "jobtrack-ai-toast";
  toast.textContent = message;
  Object.assign(toast.style, {
    position: "fixed",
    bottom: "20px",
    right: "20px",
    zIndex: "2147483647",
    background: "#1F3A5F",
    color: "#fff",
    padding: "10px 16px",
    borderRadius: "8px",
    fontFamily: "system-ui, sans-serif",
    fontSize: "13px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.25)",
    maxWidth: "320px",
  });
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}
