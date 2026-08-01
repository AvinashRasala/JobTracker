const assert = require("assert");
const { JSDOM } = require("jsdom");
const {
  extractJobInfo,
  isApplyElement,
  findApplyAncestor,
  detectPlatform,
} = require("../extractor.js");

function domFromHtml(html) {
  return new JSDOM(html).window.document;
}

let passed = 0;
let failed = 0;
function check(label, condition) {
  if (condition) {
    passed++;
    console.log(`PASS: ${label}`);
  } else {
    failed++;
    console.log(`FAIL: ${label}`);
  }
}

// --- LinkedIn ---
{
  const doc = domFromHtml(`
    <html><head><meta property="og:title" content="Senior Backend Engineer"></head>
    <body>
      <h1 class="top-card-layout__title">Senior Backend Engineer</h1>
      <div class="top-card-layout__second-subline"><a href="/company/acme">Acme Corp</a></div>
      <button class="jobs-apply-button"><span>Easy Apply</span></button>
    </body></html>
  `);
  const info = extractJobInfo(doc, "https://www.linkedin.com/jobs/view/12345", "www.linkedin.com");
  check("LinkedIn: platform detected", info.platform_slug === "linkedin");
  check("LinkedIn: role extracted", info.role_title === "Senior Backend Engineer");
  check("LinkedIn: company extracted", info.company_name === "Acme Corp");

  const span = doc.querySelector("button.jobs-apply-button span");
  const applyMatch = findApplyAncestor(span);
  check("LinkedIn: Easy Apply button detected from inner span", applyMatch !== null);
}

// --- Naukri ---
{
  const doc = domFromHtml(`
    <html><body>
      <h1 class="jd-header-title">Software Development Engineer II</h1>
      <div class="jd-header-comp-name">Beta Solutions Pvt Ltd</div>
      <button id="apply-button">Apply</button>
    </body></html>
  `);
  const info = extractJobInfo(doc, "https://www.naukri.com/job-listings-sde-2-9988", "www.naukri.com");
  check("Naukri: platform detected", info.platform_slug === "naukri");
  check("Naukri: role extracted", info.role_title === "Software Development Engineer II");
  check("Naukri: company extracted", info.company_name === "Beta Solutions Pvt Ltd");

  const btn = doc.querySelector("#apply-button");
  check("Naukri: Apply button detected", isApplyElement(btn));
}

// --- Indeed ---
{
  const doc = domFromHtml(`
    <html><body>
      <h1 class="jobsearch-JobInfoHeader-title">Data Analyst</h1>
      <div data-testid="inlineHeader-companyName">Gamma Inc</div>
      <button class="jobsearch-IndeedApplyButton"><span>Apply now</span></button>
    </body></html>
  `);
  const info = extractJobInfo(doc, "https://www.indeed.com/viewjob?jk=abc123", "www.indeed.com");
  check("Indeed: platform detected", info.platform_slug === "indeed");
  check("Indeed: role extracted", info.role_title === "Data Analyst");
  check("Indeed: company extracted", info.company_name === "Gamma Inc");

  const span = doc.querySelector(".jobsearch-IndeedApplyButton span");
  check("Indeed: Apply now button detected from inner span", findApplyAncestor(span) !== null);
}

// --- Internshala ---
{
  const doc = domFromHtml(`
    <html><body>
      <div id="job_title_html">Data Analyst Intern</div>
      <div id="company_name"><a href="#">Delta Labs</a></div>
      <button class="btn-primary">Apply Now</button>
    </body></html>
  `);
  const info = extractJobInfo(doc, "https://internshala.com/internship/detail/9988", "internshala.com");
  check("Internshala: platform detected", info.platform_slug === "internshala");
  check("Internshala: role extracted", info.role_title === "Data Analyst Intern");
  check("Internshala: company extracted", info.company_name === "Delta Labs");
}

// --- Generic fallback (unknown/company career page, no site-specific selectors) ---
{
  const doc = domFromHtml(`
    <html><head><title>Frontend Engineer - Epsilon Careers</title>
    <meta property="og:title" content="Frontend Engineer"></head>
    <body><h1>Frontend Engineer</h1>
    <button>Submit Application</button></body></html>
  `);
  const info = extractJobInfo(doc, "https://careers.epsilon.com/jobs/42", "careers.epsilon.com");
  check("Unknown site: falls back to 'manual' platform", info.platform_slug === "manual");
  check("Unknown site: role extracted via og:title fallback", info.role_title === "Frontend Engineer");

  const btn = doc.querySelector("button");
  check("Unknown site: 'Submit Application' detected", isApplyElement(btn));
}

// --- Negative case: a random button should NOT be detected as Apply ---
{
  const doc = domFromHtml(`<html><body><button>Save for later</button></body></html>`);
  const btn = doc.querySelector("button");
  check("Non-apply button correctly NOT detected", !isApplyElement(btn));
}

// --- Negative case: a huge container containing the word "apply" somewhere shouldn't match ---
{
  const doc = domFromHtml(`<html><body><div class="page-footer">Apply now or browse more jobs, terms and conditions apply to all applications submitted through this portal.</div></body></html>`);
  const div = doc.querySelector(".page-footer");
  check("Large container text correctly NOT detected as apply button", !isApplyElement(div));
}

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed > 0 ? 1 : 0);
