/**
 * Extracts job info from the current page and detects "Apply" clicks.
 *
 * Written as pure functions that take (doc, url, hostname) as arguments
 * rather than reading `document`/`window` directly, so this file can be
 * loaded as a plain content-script global AND unit-tested in Node with
 * jsdom -- same code, no duplication.
 *
 * IMPORTANT HONESTY NOTE: job sites change their page markup periodically.
 * These selectors are best-effort and deliberately layered with generic
 * fallbacks (meta tags, document.title) so a full breakage is unlikely,
 * but a *perfect* extraction on every page isn't realistic long-term --
 * expect to occasionally need to update the site-specific selectors below.
 */

const PLATFORM_BY_HOSTNAME = [
  { match: (h) => h.includes("linkedin.com"), slug: "linkedin", name: "LinkedIn Jobs" },
  { match: (h) => h.includes("naukri.com"), slug: "naukri", name: "Naukri" },
  { match: (h) => h.includes("indeed.com"), slug: "indeed", name: "Indeed" },
  { match: (h) => h.includes("internshala.com"), slug: "internshala", name: "Internshala" },
];

// Phrases that identify an "Apply" action, matched case-insensitively
// against a clicked element's visible text. Text-based matching is more
// resilient to markup/class-name changes than CSS selectors, since sites
// restyle far more often than they change their button wording.
const APPLY_PHRASES = [
  "easy apply",
  "apply now",
  "submit application",
  "apply to this job",
  "apply for this job",
  "apply",
];

function detectPlatform(hostname) {
  const found = PLATFORM_BY_HOSTNAME.find((p) => p.match(hostname));
  return found || { slug: "manual", name: "Company Career Page" };
}

function getMetaContent(doc, property) {
  const el =
    doc.querySelector(`meta[property="${property}"]`) ||
    doc.querySelector(`meta[name="${property}"]`);
  return el ? el.getAttribute("content")?.trim() || null : null;
}

function textOf(doc, selector) {
  const el = doc.querySelector(selector);
  return el ? el.textContent.trim().replace(/\s+/g, " ") : null;
}

// Site-specific selector guesses, tried before falling back to generic
// meta-tag/heading extraction. Each entry is a list tried in order --
// first non-empty match wins.
const ROLE_SELECTORS = {
  linkedin: ["h1.top-card-layout__title", ".jobs-unified-top-card__job-title", "h1"],
  naukri: ["h1.jd-header-title", "h1"],
  indeed: ["h1.jobsearch-JobInfoHeader-title", "h1"],
  internshala: ["#job_title_html", "h1"],
};

const COMPANY_SELECTORS = {
  linkedin: [".top-card-layout__second-subline a", ".jobs-unified-top-card__company-name", "a[data-tracking-control-name*='company']"],
  naukri: [".jd-header-comp-name", "a.comp-name"],
  indeed: ["[data-testid='inlineHeader-companyName']", ".jobsearch-InlineCompanyRating a"],
  internshala: ["#company_name a", ".company_name"],
};

function extractRoleTitle(doc, platformSlug) {
  const selectors = ROLE_SELECTORS[platformSlug] || [];
  for (const sel of selectors) {
    const text = textOf(doc, sel);
    if (text) return text;
  }
  // Generic fallbacks, in order of reliability.
  return getMetaContent(doc, "og:title") || textOf(doc, "h1") || (doc.title || "").split(/[-|]/)[0].trim() || null;
}

function extractCompanyName(doc, platformSlug, platformInfo) {
  const selectors = COMPANY_SELECTORS[platformSlug] || [];
  for (const sel of selectors) {
    const text = textOf(doc, sel);
    if (text) return text;
  }
  // og:site_name is often the platform itself (e.g. "LinkedIn"), not the
  // hiring company, so it's a weak fallback -- only used as a last resort.
  const ogSiteName = getMetaContent(doc, "og:site_name");
  if (ogSiteName && ogSiteName.toLowerCase() !== platformInfo.name.toLowerCase()) {
    return ogSiteName;
  }
  return null; // caller decides how to handle "couldn't determine company"
}

/**
 * Main entry point: given the page's document, URL, and hostname, returns
 * the best-effort job info to send to the backend.
 */
function extractJobInfo(doc, url, hostname) {
  const platform = detectPlatform(hostname);
  const roleTitle = extractRoleTitle(doc, platform.slug);
  const companyName = extractCompanyName(doc, platform.slug, platform);

  return {
    platform_slug: platform.slug,
    role_title: roleTitle || "Unknown role (edit me)",
    company_name: companyName || "Unknown company (edit me)",
    job_url: url,
  };
}

/**
 * Returns true if the given element's own visible text matches a known
 * "Apply" phrase. Checked against the clicked element and a couple of
 * ancestors, since the click target is often an inner <span> inside the
 * actual button.
 */
function isApplyElement(el) {
  if (!el || !el.textContent) return false;
  const text = el.textContent.trim().toLowerCase();
  if (!text || text.length > 40) return false; // avoid matching large containers
  return APPLY_PHRASES.some((phrase) => text === phrase || text.startsWith(phrase));
}

function findApplyAncestor(el, maxDepth = 4) {
  let current = el;
  for (let i = 0; i < maxDepth && current; i++) {
    if (isApplyElement(current)) return current;
    current = current.parentElement;
  }
  return null;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    detectPlatform,
    extractRoleTitle,
    extractCompanyName,
    extractJobInfo,
    isApplyElement,
    findApplyAncestor,
    APPLY_PHRASES,
  };
}
