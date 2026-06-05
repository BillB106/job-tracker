#!/usr/bin/env python3
"""Download the live Excel export from the running app and save it to disk.

The formatting lives server-side (app/excel.py) and is the same file the UI's
"Export Excel" button produces, so CLI and button never drift.

Usage:
    python3 build_xlsx.py --base-url http://127.0.0.1:8000 --password "$APP_PASSWORD"
    python3 build_xlsx.py --base-url https://YOUR-APP-URL --password "..." --out ~/jobs.xlsx
"""
import argparse
import os
import sys
import requests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--password", required=True)
    ap.add_argument("--out", default=os.path.expanduser("~/LinkedIn_Saved_Jobs.xlsx"))
    args = ap.parse_args()

    s = requests.Session()
    if s.post(f"{args.base_url}/api/login", json={"password": args.password}).status_code != 200:
        sys.exit("Login failed - check --password / --base-url.")
    r = s.get(f"{args.base_url}/api/export.xlsx")
    if r.status_code != 200:
        sys.exit(f"Export failed ({r.status_code}): {r.text[:200]}")
    with open(args.out, "wb") as f:
        f.write(r.content)
    print(f"Saved live export -> {args.out} ({len(r.content)} bytes)")


if __name__ == "__main__":
    main()
