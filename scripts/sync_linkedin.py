#!/usr/bin/env python3
"""Push freshly scraped LinkedIn jobs to the (cloud) Job Tracker.

The actual scraping still happens locally in your logged-in browser (the
Claude-in-Chrome flow). That flow produces a JSON array of jobs; this script
upserts it into the app via /api/import — new jobs added, existing ones
refreshed, your prio/status/notes preserved.

Expected JSON shape (list of objects):
[
  {
    "external_id": "4413583582",
    "title": "Head of Product & Go-to-Market (m/w/d/x)",
    "company": "pilot group",
    "location": "Hamburg, Hamburg, Germany",
    "work_type": "Hybrid",
    "posted": "3 weeks ago",
    "posted_date": "2026-05-13",
    "applicants": "6 clicked apply",
    "apply_method": "Off LinkedIn",
    "source_url": "https://www.linkedin.com/jobs/view/4413583582/"
  }
]

Usage:
    python3 sync_linkedin.py --json scraped.json \
        --base-url https://your-app.up.railway.app \
        --password "$APP_PASSWORD"
"""
import argparse
import json
import re
import sys
import requests


def extract_id(job: dict) -> str:
    if job.get("external_id"):
        return str(job["external_id"])
    m = re.search(r"/jobs/view/(\d+)", job.get("source_url", "") or "")
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="Path to scraped jobs JSON array")
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--password", required=True)
    ap.add_argument("--portal", default="LinkedIn")
    args = ap.parse_args()

    with open(args.json) as f:
        jobs = json.load(f)
    for j in jobs:
        j["job_portal"] = args.portal
        j["external_id"] = extract_id(j)

    s = requests.Session()
    login = s.post(f"{args.base_url}/api/login", json={"password": args.password})
    if login.status_code != 200:
        sys.exit(f"Login failed ({login.status_code}).")

    res = s.post(f"{args.base_url}/api/import", json={"portal": args.portal, "jobs": jobs})
    if res.status_code != 200:
        sys.exit(f"Import failed ({res.status_code}): {res.text}")
    print("Sync result:", res.json())


if __name__ == "__main__":
    main()
