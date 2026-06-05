# Job Tracker

A small self-hosted web app to track interesting job offerings across portals
(LinkedIn today, others later). Backend: FastAPI + SQLAlchemy + Postgres.
Frontend: a single page using AG Grid (per-column filter + sort, inline editing).

## Features
- All columns from your Excel export, plus:
  - **Job Portal** column (LinkedIn now; add StepStone/Indeed/… later)
  - **Prio** — 5 levels: Not prioritized · Keep an eye on · Tackle now · Applied / in progress · Discard / not interested
  - **Status** — the live posting state (**Open / Offline / Unknown**), *not* LinkedIn's "Saved"
- Filter **and** sort on every column (floating filter box under each header)
- Inline editing of Prio, Status, Notes (and any text field); add / delete rows
- Single-password login (it holds personal data — never deploy it open)
- Re-import is an **upsert**: matches on `job_portal + external_id`, refreshes scraped
  fields, and **preserves your Prio / Status / Notes**.

## Architecture / refresh model
Cloud servers can't scrape LinkedIn (needs your logged-in session; datacenter IPs
are blocked; against ToS). So:

```
[Your Mac, logged into LinkedIn]                 [Cloud: Railway/Render]
  scrape (Claude-in-Chrome) ─► scraped.json ─POST /api/import─► FastAPI + Postgres + UI
                                                                 (reachable from any device)
```

Scraping stays local; a sync command pushes results to the cloud DB.

---

## Run locally

```bash
cd job-tracker/backend
python3 -m pip install -r requirements.txt      # (psycopg2 only needed for Postgres)
APP_PASSWORD="testpass123" SECRET_KEY="$(python3 -c 'import secrets;print(secrets.token_hex(32))')" \
  python3 -m uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000 and log in with `APP_PASSWORD`.
With no `DATABASE_URL`, it uses a local SQLite file `backend/jobs.db`.

### Seed the current jobs
```bash
cd job-tracker/scripts
python3 seed_data.py --base-url http://127.0.0.1:8000 --password testpass123
```
Or load from an Excel export:
```bash
python3 import_excel.py --xlsx ~/LinkedIn_Saved_Jobs.xlsx \
  --base-url http://127.0.0.1:8000 --password testpass123
```

### Refresh from a new scrape
The Claude-in-Chrome flow produces a JSON array of jobs (see `sync_linkedin.py`
docstring for the shape). Then:
```bash
python3 sync_linkedin.py --json scraped.json \
  --base-url https://YOUR-APP-URL --password "$APP_PASSWORD"
```
A re-scrape **only refreshes scraped fields** (title, company, location, posted,
applicants, …). Your **Prio, Status and Notes are never overwritten** — they're
user-owned (enforced in `importer.py`).

### Export current data back to Excel
`build_xlsx.py` pulls the **live** data from the app (so it reflects whatever
Prio / Status / Notes you've set) and writes a formatted .xlsx. Column order
mirrors the web grid, the Job Title is hyperlinked, and rows are colour-coded by
Prio (use `--no-colour` to disable):
```bash
python3 build_xlsx.py --base-url http://127.0.0.1:8000 \
  --password "$APP_PASSWORD" --out ~/LinkedIn_Saved_Jobs.xlsx
```

---

## Deploy to Railway (or Render) + managed Postgres

You run these steps (account creation and secrets are yours to enter):

1. **Push this folder to a GitHub repo.**
2. **Railway:** New Project → *Deploy from GitHub repo* → pick the repo.
   Railway detects the root `Dockerfile`.
3. **Add Postgres:** in the project, *New → Database → PostgreSQL*. Railway sets
   `DATABASE_URL` on the service automatically.
4. **Set environment variables** on the web service:
   - `APP_PASSWORD` = a strong password
   - `SECRET_KEY` = output of `python3 -c "import secrets; print(secrets.token_hex(32))"`
5. **Deploy.** Open the generated URL, log in, then seed:
   ```bash
   python3 scripts/seed_data.py --base-url https://YOUR-APP-URL --password "YOUR_APP_PASSWORD"
   ```

**Render** is equivalent: New → *Web Service* (Docker) from the repo; add a
Postgres instance; copy its Internal Database URL into `DATABASE_URL`; set
`APP_PASSWORD` and `SECRET_KEY`.

> Tables are created automatically on startup. For schema *changes* later, add a
> migration tool (Alembic) — fine to skip for now.

## Project layout
```
job-tracker/
  Dockerfile            # builds backend + bundles frontend
  backend/
    requirements.txt
    app/
      main.py           # routes + static serving
      models.py         # Job table (+ allowed Prio/Status values)
      schemas.py        # request/response models
      db.py             # Postgres (prod) / SQLite (local) engine
      auth.py           # single-password signed-cookie auth
      importer.py       # upsert (preserves user fields)
  frontend/
    index.html, app.js, styles.css   # AG Grid SPA
  scripts/
    seed_data.py        # authoritative 31-job seed
    import_excel.py     # seed from an .xlsx export
    sync_linkedin.py    # push a fresh scrape JSON to the app
```

## Adding another portal later
Write a small scraper that outputs the same JSON shape with
`job_portal: "StepStone"` and a stable `external_id`, then POST to `/api/import`.
Everything else (UI, filters, dedupe) works unchanged.
