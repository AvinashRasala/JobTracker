# JobTrack AI — Module 1: Architecture, Database, Core Backend

This is the foundational, **running** module of JobTrack AI. Every later module
(Gmail parsing, Chrome extension, AI features, frontend dashboard) plugs into
the schema and API built here — nothing here is throwaway scaffolding.

## What's included in this module

- **Database schema** (PostgreSQL, via SQLAlchemy models + a hand-written Alembic migration):
  `users`, `companies`, `platforms`, `recruiters`, `applications`, `status_history`, `notes`
- **Auth**: email/password registration + login, JWT bearer tokens
- **Applications API**: create (with automatic company/platform/recruiter resolution
  and duplicate detection via `external_application_id`), list with filters
  (status, company, platform, keyword), get by id, update status (records full
  history), delete
- **Dashboard/analytics API**: totals (today/week/month/year), success/interview/
  offer/rejection/response rates, average response time, most-applied company/role,
  most-used platform, status distribution, platform distribution, applications-per-day
- **18 platforms pre-seeded**: LinkedIn, Indeed, Naukri, Foundit, Wellfound, Glassdoor,
  Instahyre, Hirist, Cutshort, Internshala, Dice, ZipRecruiter, Lever, Greenhouse,
  Workday, SmartRecruiters, Company Career Page, and Manual Entry — adding a new one
  is a single row insert (`app/models/platform.py`), no migration required.
- **Docker Compose** setup: Postgres + Redis + backend, ready for `docker compose up`

This has been tested end-to-end (register → login → create application →
duplicate rejection → status update → dashboard stats) against a live database.

## What's intentionally NOT in this module yet

Gmail parsing, the Chrome extension, AI features, Google Calendar, notifications,
document uploads, and the Next.js frontend are separate modules — building them
all in one shot without testing each in isolation is how "AI-generated projects"
end up full of code that looks right but doesn't run. We'll build those next,
each wired into this same schema/API.

## Running it locally

### Option A — Docker (recommended)

```bash
cp .env.example .env
# edit .env if you want, defaults work out of the box

docker compose up --build
```

Then, in a second terminal, run migrations and seed the platforms table:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed_platforms.py
```

API docs (interactive): http://localhost:8000/docs

### Option B — Local Python (no Docker)

Requires a local PostgreSQL instance running.

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp ../.env.example .env
# edit .env: set DATABASE_URL to your local Postgres connection string

alembic upgrade head
python scripts/seed_platforms.py

uvicorn app.main:app --reload
```

## Trying it out

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword","full_name":"Your Name"}'

# Login (note: form-encoded, not JSON)
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=you@example.com&password=yourpassword"
# -> copy the access_token from the response

# Create an application
curl -X POST http://localhost:8000/api/applications \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role_title": "Senior Backend Engineer",
    "company_name": "Acme Corp",
    "platform_slug": "linkedin",
    "location": "Bangalore",
    "work_type": "remote",
    "employment_type": "full_time"
  }'

# Dashboard stats
curl http://localhost:8000/api/dashboard/stats -H "Authorization: Bearer <token>"
```

Or just open http://localhost:8000/docs and use the "Authorize" button with your token.

## Project structure

```
jobtrack-ai/
├── docker-compose.yml
├── .env.example
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── alembic.ini
    ├── alembic/
    │   ├── env.py
    │   └── versions/0001_initial_schema.py
    ├── scripts/
    │   └── seed_platforms.py
    └── app/
        ├── main.py           # FastAPI app + router registration
        ├── config.py         # env-driven settings
        ├── database.py       # SQLAlchemy engine/session
        ├── models/           # ORM models (one file per table)
        ├── schemas/          # Pydantic request/response models
        ├── core/
        │   └── security.py   # password hashing, JWT
        └── api/
            ├── deps.py        # get_current_user dependency
            └── routes/
                ├── auth.py
                ├── applications.py
                └── dashboard.py
```

---

# Module 2: Frontend Dashboard

A Next.js 16 (App Router) + TypeScript + Tailwind dashboard that talks directly
to the Module 1 API. Verified with a real `next build` (production build, 0
errors, all 6 routes compiling) in addition to manual review.

**Design direction:** the app leans into the "tracking" in JobTrack AI — a
ledger/waybill aesthetic (navy + paper + dashed "postmark" status stamps)
instead of a generic dashboard template. Status badges are the one signature
element, used consistently everywhere a status appears.

## What's included

- **Auth**: register / login pages, JWT stored client-side, route protection
- **Dashboard**: all the stat cards from the spec (totals by day/week/month/
  year, success/interview/offer/rejection/response rate, avg. response time,
  most-applied company/role, most-used platform) plus three charts
  (applications-per-day area chart, status distribution bar chart, platform
  distribution bar chart) built with Recharts
- **Applications ledger**: searchable/filterable list (keyword, status),
  inline status updates, a "Log application" dialog covering all 18 seeded
  platforms
- Lightweight, dependency-free UI primitives (Button, Input, Select, Card,
  Dialog, StatusStamp) in the spirit of shadcn/ui, styled with Tailwind and the
  app's own design tokens

## What's not built yet
No PWA/offline support, no document uploads, no AI-feature panels — those
land in the modules for Gmail, the extension, and AI features, since they need
backend work first.

## Running it

```bash
cd frontend
cp .env.local.example .env.local
# edit .env.local if your backend isn't on localhost:8000

npm install
npm run dev
```

Then open http://localhost:3000 — register an account (this talks to the
Module 1 backend, so make sure that's running first), and start logging
applications.

**Note on fonts:** the layout uses `next/font/google` (Space Grotesk, IBM Plex
Sans, IBM Plex Mono), which fetches font files from Google Fonts at build
time. This needs normal internet access — true of any Next.js project using
`next/font/google` — and will work fine on your machine, Vercel, or any CI
with outbound internet. It just can't be verified inside this sandboxed
tool environment, which blocks that domain; everything else (routing, data
fetching, TypeScript, the production build itself) was verified here with a
real `next build`.

## Project structure

```
frontend/
├── package.json
├── tailwind.config.ts
├── app/
│   ├── layout.tsx          # fonts, providers
│   ├── page.tsx            # redirects to /login or /dashboard
│   ├── login/page.tsx
│   ├── register/page.tsx
│   ├── dashboard/page.tsx  # stats + charts
│   └── applications/page.tsx
├── components/
│   ├── app-shell.tsx        # sidebar nav + auth guard
│   ├── stat-card.tsx
│   ├── add-application-dialog.tsx
│   ├── charts/
│   └── ui/                  # button, input, select, card, dialog, status-stamp
├── lib/
│   ├── api.ts                # typed fetch client
│   ├── auth-context.tsx
│   └── types.ts
└── providers/query-provider.tsx
```

---

# Module 3: Interview Tracking, Follow-up Reminders, Offer Comparison, Referrals

Added on top of Modules 1 & 2, aimed at both freshers and experienced
professionals. Verified against a real Postgres instance (not just
SQLite) end-to-end, including the incremental migration path from an
existing Module-1/2 database.

## What's included

- **Interview round tracking**: log each round separately (name, mode —
  phone/video/onsite/assessment, interviewer, scheduled time, feedback,
  outcome). Lives on the application's detail page.
- **Follow-up reminders**: every new application gets a `follow_up_at`
  date, defaulting to 7 days after you applied. A dedicated **Follow-ups**
  page lists anything overdue (and not already offered/rejected/withdrawn/
  joined), with a one-click "snooze 3 days" action. Also surfaced as a
  dashboard stat and a badge on the applications ledger.
- **Offer comparison**: once an application's status is "Offer Received"
  or "Joined", it shows up on the **Offers** page as a card — offered CTC,
  expected CTC, notice period, location, work type — with the highest
  offer highlighted.
- **Referral tracking**: who referred you and their relationship to you,
  captured at creation or added later from the application detail page.
- **CTC & experience fields**: expected/offered CTC and notice period per
  application; current CTC, notice period, and years of experience on
  your profile (`GET/PATCH /api/auth/me`) — all optional, so freshers can
  simply leave them blank.

## Upgrading an existing Module 1/2 setup

This adds a new migration (`0002`) and new columns/tables — it does **not**
require wiping your existing data. From your running project:

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

That's it — `alembic upgrade head` only applies what's new.

## New API endpoints

- `GET/POST /api/applications/{id}/interviews`, `PATCH/DELETE .../interviews/{round_id}`
- `GET /api/applications/needs-follow-up`
- `GET /api/applications/offers/compare`
- `PATCH /api/applications/{id}` — general edit (CTC, referral, location, etc; separate from the status-only endpoint so status changes always stay in `status_history`)
- `GET/PATCH /api/auth/me` — profile (current CTC, notice period, years of experience)

## New frontend pages

- `/applications/[id]` — detail view: edit CTC/notice period/referral, manage interview rounds
- `/follow-ups` — overdue applications with a snooze action
- `/offers` — offer comparison cards

---

# Module 4: Account Management (Password Visibility, Profile, Deactivate/Delete)

Verified end-to-end against real Postgres, including a full lifecycle test:
register → update profile/phone → upload+serve+delete avatar → change
password (old password confirmed dead) → export CSV → deactivate → login
blocked → reactivate → delete account (wrong password rejected first) →
account confirmed gone.

## What's included

- **Password visibility toggle** on login, register, and the new password-change
  form — an eye icon that shows/hides the typed password.
- **Profile settings** (`/settings`): edit full name and phone number; upload,
  replace, or remove a profile picture (JPEG/PNG/WebP, 3 MB max, served from
  `/static/avatars/...`).
- **Change password**: requires the current password; rejects anything under
  8 characters for the new one.
- **Deactivate account**: soft-disable — blocks login until reactivated, but
  keeps all your data. The login page detects a deactivated account and
  offers a one-click "Reactivate my account" option (re-enters the same
  email/password).
- **Delete account**: hard delete, requires re-entering your password to
  confirm. Cascades to every application, interview round, note, and status
  history you've logged.
- **CSV export**: an "Export CSV" button on the Applications page downloads
  every logged application (company, role, platform, status, CTC, notice
  period, referral, etc.) as a spreadsheet-ready file.

## New API endpoints

- `POST /api/auth/me/avatar`, `DELETE /api/auth/me/avatar`
- `POST /api/auth/me/password`
- `POST /api/auth/me/deactivate`
- `POST /api/auth/reactivate` (unauthenticated — a deactivated account has no
  other way to get a token)
- `POST /api/auth/me/delete`
- `GET /api/applications/export.csv`
- `PATCH /api/auth/me` now also accepts `phone_number`

## Upgrading an existing setup

Adds migration `0003` (phone number + avatar columns on `users`). No data is
wiped:

```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```

Uploaded avatars are written to `backend/static/avatars/`, which is inside
the bind-mounted `./backend:/app` volume in `docker-compose.yml`, so they
persist across container restarts without any extra volume configuration.

---

# Module 5: Gmail Integration (Automatic Application Detection)

This is the "stop typing every application in by hand" module. Connect your
Gmail once, and JobTrack AI reads confirmation and status-update emails to
create and update applications automatically.

## What was tested, and what wasn't (read this first)

I can't get real Google OAuth credentials or a real inbox in my build
environment, so here's exactly what was and wasn't verified:

**Tested (13 automated tests, all passing, against a real Postgres database):**
- Email parsing heuristics — 10 realistic sample emails (LinkedIn, Naukri,
  Indeed, Internshala, direct company emails, interview/offer/rejection/
  assessment notices) correctly classified and had company/role extracted
- Full sync logic with the Gmail API mocked — confirmation emails create
  applications, status emails update the right existing application (even
  when the sender's display name doesn't exactly match the stored company
  name, e.g. "Acme Corp Recruiting" vs. "Acme Corp"), and re-running sync
  never creates duplicates
- Token encryption round-trip, all API endpoints (connect/status/sync/disconnect)
- Migration `0004`, both fresh and incremental (0003→0004)

**Not tested (needs your real Google account to verify):**
- The actual OAuth consent screen flow
- Real token exchange with Google's servers
- Parsing real emails from your actual inbox — the heuristics are pattern-based
  and won't catch every possible email template. Expect it to work well for
  common cases and occasionally miss unusual ones or misidentify a company;
  everything it creates is fully editable from the application detail page.

Run the automated tests yourself anytime with:
```bash
cd backend
DATABASE_URL=<your db> ENCRYPTION_KEY=<your key> pytest tests/ --asyncio-mode=auto -v
```

## Setting up Google Cloud (do this first — I can't do it for you)

1. Go to **console.cloud.google.com** → create a new project (or pick an existing one)
2. **APIs & Services** → **Library** → search "Gmail API" → **Enable**
3. **APIs & Services** → **OAuth consent screen**:
   - User type: External (unless you have a Google Workspace org)
   - Fill in app name, your email, etc.
   - Scopes: add `https://www.googleapis.com/auth/gmail.readonly`
   - Test users: add your own Gmail address (required while the app is in "Testing" status — otherwise Google blocks login for anyone not listed)
4. **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**
   - Application type: **Web application**
   - Authorized redirect URIs: add both:
     - `http://localhost:8000/api/gmail/callback` (for local dev)
     - `https://your-backend.onrender.com/api/gmail/callback` (your real Render URL)
5. Copy the **Client ID** and **Client Secret** it gives you

## Environment variables to set

On both your local `.env` and your Render backend service:
```
GOOGLE_CLIENT_ID=<from step 5 above>
GOOGLE_CLIENT_SECRET=<from step 5 above>
GOOGLE_REDIRECT_URI=https://your-backend.onrender.com/api/gmail/callback
FRONTEND_URL=https://your-app.vercel.app
ENCRYPTION_KEY=<generate below>
```

Generate `ENCRYPTION_KEY`:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

⚠️ Treat `ENCRYPTION_KEY` like a password. If it changes, every previously-stored
Gmail token becomes undecryptable and users will need to reconnect Gmail.

## Upgrading an existing deployment

Adds migration `0004`. No data is wiped:
```bash
docker compose up --build -d
docker compose exec backend alembic upgrade head
```
(On Render, this happens automatically on deploy via `start.sh`.)

## How it works

1. **Settings page** → "Connect Gmail" → Google's consent screen → redirected back, connected
2. **"Sync now"** — manually triggered for now (no background scheduler wired up yet, see below). Searches recent job-related emails, skips anything already processed, creates new applications from confirmation emails, and updates existing ones' status from interview/offer/rejection/assessment emails matched by company name
3. Every processed email is recorded (`processed_gmail_messages` table) so syncing repeatedly is always safe — nothing is ever double-counted

**More serious bug: bare word "unfortunately" was silently misclassifying
emails as rejections.** The status-detection rules included the single
word `"unfortunately"` as a rejection signal, checked before confirmation
phrases. Since that word appears in all kinds of unrelated boilerplate
(disclaimers, unrelated correspondence, even incidental phrasing inside a
genuine confirmation email), this caused real, active applications to get
silently marked as Rejected. Fixed by:
- Removing the bare word entirely from the classifier — rejections now
  require one of several more specific phrases ("regret to inform", "not
  moving forward", "not selected", etc.)
- Quoting every remaining term in the *search query* too (interview,
  assessment, offer, rejection phrases), not just the confirmation ones —
  the bare words there were also over-fetching irrelevant emails
- Adding **`GET /api/gmail/recent-changes`** and a "Recent Gmail changes"
  panel in Settings, listing every status change the sync has made with a
  one-click **Revert** button — if a future misclassification slips
  through, you can see and undo it in one place instead of hunting through
  applications individually

Covered by a permanent regression test proving an email containing
"unfortunately" as incidental text is still correctly classified as a
confirmation, not a rejection
(`tests/test_email_parser.py`, the last parametrized case).

**If you were affected by this bug before the fix**: open **Settings**,
scroll to "Recent Gmail changes," and review/revert anything incorrect.
The panel only appears once Gmail is connected and shows changes going
back through your sync history.

## Known fixes since initial release

**Skipped-email visibility (migration `0005`).** Added `GET /api/gmail/skipped-emails`
and a "Recently skipped emails" collapsible panel in Settings, showing the
subject/sender of every email the sync found but deliberately didn't act
on — either because the wording wasn't specific enough to be confident it's
a real confirmation/status update, or because it looked like a status
update but couldn't be matched to any existing application by company
name. This is usually correct, conservative behavior (skipping an
ambiguous email is safer than guessing wrong), but the panel exists so you
can judge for yourself rather than just trusting the "X skipped" count
blindly.

**Search query was too broad, and the sync watermark had a real bug.**
The original search query (`application OR applying OR interview OR ...`)
matched far too much — job-alert digest emails (LinkedIn, Indeed) contain
words like "apply" everywhere and were crowding real confirmation emails
out of the search results. Fixed by:
- Using quoted exact phrases ("thank you for applying", "application
  confirmed", etc.) instead of bare common words
- Excluding known noisy senders (job alert / chat notification addresses)
- **Removing the "only search since last sync" optimization entirely.**
  This was a real bug: once any sync ran — even one that found nothing
  useful — it permanently narrowed every future search to "after that
  point," so an older email a buggy/narrow earlier sync missed could never
  be found again. Every sync now re-scans a rolling 30-day window; dedup
  is handled safely by the `processed_gmail_messages` table regardless
  (already-processed messages are skipped without an extra API call), so
  this is both more correct and still cheap.
- Sync errors (previously silently swallowed) now display in the Settings
  UI under the sync result

Covered by a permanent regression test:
`tests/test_gmail_sync.py::test_old_email_still_found_after_a_previous_sync_ran`

## What's intentionally not automatic yet

There's no background job polling Gmail every N minutes — "Sync now" is a
manual button. Wiring up a real scheduler (Celery beat, using the Redis
already in `docker-compose.yml`) is a reasonable next step, but needs an
always-on worker process, which costs extra on Render's free/starter tiers.
Happy to build it if you want to run that infrastructure.

## New API endpoints

- `GET /api/gmail/connect` — returns the Google OAuth consent URL
- `GET /api/gmail/callback` — OAuth redirect target (Google calls this directly)
- `GET /api/gmail/status` — connected?, last synced at
- `POST /api/gmail/sync` — manually trigger a sync
- `DELETE /api/gmail/disconnect` — remove stored tokens

---

# Module 6: Chrome Extension (Instant Apply Capture)

Auto-logs applications the moment you click Apply on LinkedIn, Naukri,
Indeed, or Internshala — no manual entry, no waiting for a confirmation
email.

## What was tested, and what wasn't (read this first)

Same honesty policy as the Gmail module — I can't load a real Chrome
browser or visit live job sites from my build environment, so here's
exactly what's verified:

**Tested (20 automated tests passing, using jsdom against realistic HTML fixtures):**
- Job title / company extraction for all 4 supported sites, using markup
  that mirrors each site's real structure
- Generic fallback extraction (og:title, `<h1>`, page title) for any other
  company career page not in the specific-selector list
- "Apply" button detection by visible text ("Easy Apply", "Apply now",
  "Submit Application", etc.), including when the click lands on an inner
  `<span>` inside the real button
- **Negative cases**: a "Save for later" button and a large text block that
  merely *contains* the word "apply" are correctly **not** detected — this
  matters because false positives would silently log garbage applications
- The exact JSON payload the extension sends was tested against the real
  backend: creates the application, records `source: chrome_extension`
  correctly, and a duplicate "Apply" click (page re-render, debounce
  failure, etc.) is correctly rejected as a 409, not double-logged

**Not tested (needs your real browser + real job sites to verify):**
- Loading the extension in actual Chrome and clicking real Apply buttons
- Whether LinkedIn/Naukri/Indeed/Internshala's *current* live markup matches
  the selectors below — sites change their HTML periodically without
  warning, and this is the one part of the whole project that will need
  occasional maintenance as a result. If capture stops working for a
  specific site, it's almost always a selector needing an update in
  `extension/extractor.js`, not a deeper bug.

Run the tests yourself anytime with:
```bash
cd extension
npm install
npm test
```

## Installing it (Chrome, unpacked/developer mode)

This isn't published to the Chrome Web Store (that needs a $5 one-time
developer fee and a review process) — you load it directly:

1. Open `chrome://extensions`
2. Toggle **Developer mode** on (top-right)
3. **Load unpacked** → select the `extension/` folder
4. Click the extension's icon in your toolbar → sign in with your JobTrack AI
   account (same email/password as the web app)
5. If your backend isn't on `localhost:8000`, update the **Backend URL**
   field in the popup (e.g. your Render URL) and click Save

## Using it

Just browse LinkedIn/Naukri/Indeed/Internshala and click Apply / Easy Apply
/ Submit Application as normal. A small confirmation toast appears in the
corner of the page once it's logged. Check the **Applications** page in the
web app — it should show up immediately (`source: Chrome Extension`).

## If a site stops being detected correctly

Open `extension/extractor.js` and look at `ROLE_SELECTORS` / `COMPANY_SELECTORS`
for that platform. Right-click the job title or company name on the actual
page → **Inspect** → find its CSS selector (class name, id, etc.) → add it
to the front of that site's selector list → reload the extension at
`chrome://extensions` (the reload icon on the card).

## Using it against your deployed backend

The manifest's `host_permissions` currently allow `localhost:8000` and any
`*.onrender.com` subdomain. If you deploy the backend somewhere else, add
that domain to `host_permissions` in `extension/manifest.json`, then reload
the unpacked extension.

## Project structure

```
extension/
├── manifest.json       # MV3 config
├── background.js       # service worker: owns the JWT token, calls the API
├── content.js          # runs on job pages, detects Apply clicks
├── extractor.js         # pure extraction logic (shared with tests)
├── popup.html/css/js    # sign-in + backend URL settings
├── icons/
└── tests/
    └── test_extractor.js
```

## Next modules (in order)

1. ~~Frontend dashboard~~ ✅ done
2. ~~Interview tracking, follow-ups, offers, referrals~~ ✅ done
3. ~~Account management: password visibility, profile, deactivate/delete~~ ✅ done
4. ~~Gmail integration~~ ✅ done
5. ~~Chrome extension~~ ✅ done
6. **AI features** — ATS match score, cover letter generation, follow-up emails
7. **Notifications, calendar sync, document management, exports (Excel/PDF)**

Let me know which one to build next.
