# 📋 Job Tracker — Operations Reference

> Day-to-day guide for keeping the app running. (Keep your actual password and
> SECRET_KEY in a password manager / Railway Variables — never in this file.)

## Key locations
- **Live app:** https://job-tracker-production-bdcc.up.railway.app/
- **GitHub repo:** https://github.com/BillB106/job-tracker (private, account `BillB106`)
- **Local code:** `/Users/billbolls/job-tracker/`
- **Hosting:** Railway (web service + PostgreSQL add-on)
- **Login:** single password (your `APP_PASSWORD`).

## What it is
A personal web tool to track interesting jobs (LinkedIn now, other portals later).
- **Stack:** FastAPI + SQLAlchemy + PostgreSQL backend; AG Grid frontend.
- **Columns:** Job Portal · Prio · Status · Job Title (linked) · Company · Location · Work Type · Posted (approx) · Posted · Applicants/Clicks · Apply Method · Notes.
- **Prio** (6): Not prioritized / Keep an eye on / Tackle now / Applied–in progress / Keep in backpocket / Discard. Rows colour-code by Prio (Keep in backpocket = grey background; Discard = grey font).
- **Status** (4): Open / Offline / Unknown / Archived. Offline rows = italic + strikethrough + grey; Archived rows = dimmed + strikethrough.
- Filter & sort on every column; **all cells are editable** (double-click) and save automatically — Prio/Status/Notes plus Posted, Posted (approx), Applicants, Apply Method, etc.

---

## ⭐ Standard refresh routine (recommended)
The normal way to keep the board current — re-scrape, then push with archiving:
```bash
# 1. (Ask Claude to) re-scrape your LinkedIn tracker → writes scripts/scraped.json
# 2. Push the fresh data AND archive anything you've un-saved:
cd /Users/billbolls/job-tracker/scripts
python3 sync_linkedin.py --json scraped.json --archive-missing \
  --base-url https://job-tracker-production-bdcc.up.railway.app \
  --password 'YOUR_APP_PASSWORD'
```
Result looks like `{'created': X, 'updated': Y, 'archived': Z, 'total': N}`.
Then (optional) click **⬇ Export Excel** in the app, or run `build_xlsx.py`.
In the app, filter the **Status** column to exclude `Archived` to see only active jobs.

Details of each piece below. 👇

## 🔄 Re-scrape LinkedIn (get fresh jobs)
LinkedIn can only be scraped **from your own logged-in browser** — it can't run on the server. So the flow is:
1. Have the scrape run in your browser (ask Claude to re-run the LinkedIn jobs-tracker extraction, or do it manually). Save the result as a JSON array, e.g. `scraped.json`, with this shape per job:
   ```json
   [{"external_id":"4413583582","title":"…","company":"…","location":"…",
     "work_type":"Hybrid","posted":"3 weeks ago","posted_date":"2026-05-13",
     "applicants":"6 clicked apply","apply_method":"Off LinkedIn",
     "source_url":"https://www.linkedin.com/jobs/view/4413583582/"}]
   ```
2. Push it to the live app:
   ```bash
   cd /Users/billbolls/job-tracker/scripts
   python3 sync_linkedin.py --json scraped.json \
     --base-url https://job-tracker-production-bdcc.up.railway.app \
     --password 'YOUR_APP_PASSWORD'
   ```
- **Upsert behaviour:** matches by `job_portal + external_id`. New jobs added, existing ones refreshed.
- **Your Prio / Status / Notes are NEVER overwritten** by a re-scrape.

### Clean up jobs you've un-saved (archive-missing)
Add `--archive-missing` to flag any LinkedIn job NOT in the current scrape as
`Archived` (a status that dims + strikes the row). Manually-added jobs (other
portals / no LinkedIn id) are never touched, and a job that reappears in a later
scrape is automatically un-archived back to `Open`.
```bash
python3 sync_linkedin.py --json scraped.json --archive-missing \
  --base-url https://job-tracker-production-bdcc.up.railway.app \
  --password 'YOUR_APP_PASSWORD'
```
Safety: archiving only runs when the scrape actually returned jobs (an empty
file won't wipe the board). Status values are now: Open / Offline / Unknown / Archived.

## 📤 Update the Excel export
Two ways — both pull **live** data and include colours/links/offline styling:
- **Easiest:** click **"⬇ Export Excel"** in the app toolbar → downloads `job_tracker_export.xlsx`.
- **CLI:**
  ```bash
  cd /Users/billbolls/job-tracker/scripts
  python3 build_xlsx.py \
    --base-url https://job-tracker-production-bdcc.up.railway.app \
    --password 'YOUR_APP_PASSWORD' --out ~/LinkedIn_Saved_Jobs.xlsx
  ```
- ⚠️ Don't leave the .xlsx open in Excel/Numbers while regenerating — the open app can overwrite the fresh file.

## 🚀 Deploy code changes
Railway auto-redeploys on every push to `main`. Data persists (it's in Postgres).
```bash
cd /Users/billbolls/job-tracker
git add -A
git commit -m "describe change"
git push origin main          # Railway rebuilds automatically (~40s)
```

## 🗄️ First-time / reset seed
Loads the baseline job snapshot (normally only needed once or after a DB reset):
```bash
cd /Users/billbolls/job-tracker/scripts
python3 seed_data.py --base-url https://job-tracker-production-bdcc.up.railway.app \
  --password 'YOUR_APP_PASSWORD'
```

---

## ⚠️ Critical: make sure it's on Postgres (not SQLite)
If the app uses SQLite instead of Postgres, **all data is wiped on every redeploy.**
- **Check anytime:** open https://job-tracker-production-bdcc.up.railway.app/healthz
  - ✅ `{"ok":true,"db":"postgresql"}` = good, data persists.
  - ❌ `{"ok":true,"db":"sqlite"}` = broken. Fix: in Railway → `job-tracker` service → **Variables**, set
    `DATABASE_URL = ${{Postgres.DATABASE_URL}}`, then redeploy.

## 🔑 Railway environment variables (on the `job-tracker` service)
- `APP_PASSWORD` — your login password
- `SECRET_KEY` — signs the login cookie (random 64-char hex)
- `DATABASE_URL` = `${{Postgres.DATABASE_URL}}` — links app to Postgres
- (Generate a new SECRET_KEY if ever needed: `python3 -c "import secrets; print(secrets.token_hex(32))"`)

## 💻 Run locally (for testing changes before pushing)
```bash
cd /Users/billbolls/job-tracker/backend
python3 -m pip install fastapi "uvicorn[standard]" SQLAlchemy pydantic itsdangerous python-multipart openpyxl requests
APP_PASSWORD="testpass123" SECRET_KEY="localdev" python3 -m uvicorn app.main:app --reload --port 8000
# open http://localhost:8000  — uses a local SQLite file (backend/jobs.db); no Postgres needed locally
```

## 🔐 Security notes
- Never paste `APP_PASSWORD` / `SECRET_KEY` into chats, docs, or commits.
- The repo is private; `.gitignore` keeps `jobs.db`, `.env`, and `*.xlsx` out of git.
- The app is password-protected — don't remove that before exposing it publicly.

## ➕ Add a job manually (non-LinkedIn)
For jobs not on LinkedIn (company sites, referrals, other portals): click **"+ Add job"**
in the toolbar, then double-click cells to fill in Job Portal (e.g. `Company site`),
Title, Company, Posted, Apply Method, Prio, Status, Notes — every column is editable.
- Manual jobs are saved straight to the database and persist.
- They have **no LinkedIn id**, so a re-scrape **never touches or archives them** — they
  stay put no matter how often you sync LinkedIn.
- You can add as many as you like (no collisions).

## 🔌 Adding another job portal later (automated)
Produce the same JSON shape with `"job_portal":"StepStone"` (etc.) and a stable `external_id`, then POST to `/api/import`. The UI, filters, and dedupe work unchanged.

## 🗂️ Project layout
```
job-tracker/
  Dockerfile            # builds backend + bundles frontend
  OPERATIONS.md         # this file
  README.md             # setup + deploy guide
  backend/app/
    main.py             # routes + static serving
    models.py           # Job table (+ allowed Prio/Status values)
    db.py               # Postgres (prod) / SQLite (local) engine
    auth.py             # single-password signed-cookie auth
    importer.py         # upsert (preserves Prio/Status/Notes)
    excel.py            # Excel export formatting (used by button + CLI)
  frontend/             # index.html, app.js, styles.css (AG Grid SPA)
  scripts/
    seed_data.py        # baseline seed
    import_excel.py     # seed from an .xlsx
    sync_linkedin.py    # push a fresh scrape to the app
    build_xlsx.py       # download the live Excel export
```
