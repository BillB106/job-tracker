#!/usr/bin/env python3
"""Authoritative seed: the current 31 LinkedIn saved jobs.

Regenerates the Excel file AND imports into the running app via /api/import.
This avoids depending on an xlsx that an open spreadsheet app might overwrite.

Usage:
    python3 seed_data.py --base-url http://127.0.0.1:8000 --password "$APP_PASSWORD"
"""
import argparse
import re
import sys
import requests

# (title, company, location, work_type, posted, posted_date, applicants, apply_method, job_id, notes)
ROWS = [
    ("Applied AI & Automations", "hansetherm", "Hamburg, Hamburg, Germany", "On-site", "1 month ago", "2026-05-03", "51 clicked apply", "Off LinkedIn", "4404182046", "Bewerben"),
    ("Senior Consultant Hybrides Projektmanagement (all genders)", "Adesso Business Consulting", "Hamburg, Hamburg, Germany", "", "Reposted 3 hours ago", "2026-06-03", "31 clicked apply", "Off LinkedIn", "4193255503", ""),
    ("Senior Project & Process Manager – Operational Excellence Group Functions (m/f/d)", "adjoe", "Hamburg, Hamburg, Germany", "Hybrid", "23 hours ago", "2026-06-02", "26 clicked apply", "Off LinkedIn", "4422407379", ""),
    ("Projektleitung AI (all genders)", "adesso SE", "Hamburg, Hamburg, Germany", "", "Reposted 2 hours ago", "2026-06-03", "25 clicked apply", "Off LinkedIn", "4324396082", ""),
    ("IT-Consultant Conversational AI (all genders)", "adesso SE", "Hamburg, Hamburg, Germany", "", "Reposted 2 hours ago", "2026-06-03", "24 clicked apply", "Off LinkedIn", "4078616301", ""),
    ("Head of Product & Go-to-Market (m/w/d/x)", "pilot group", "Hamburg, Hamburg, Germany", "Hybrid", "3 weeks ago", "2026-05-13", "6 clicked apply", "Off LinkedIn", "4413583582", "Sent inMail to Kristian Meinken (02.06.26)"),
    ("Product Director – Conversational AI CS & Pharma Advisory (m/f/d)", "Redcare Pharmacy", "Berlin, Berlin, Germany", "", "2 weeks ago", "2026-05-20", "89 applicants", "Easy Apply", "4414467550", ""),
    ("Implementation Expert (f/d/m)", "Parto", "Hamburg, Hamburg, Germany", "On-site", "2 days ago", "2026-06-01", "10 clicked apply", "Off LinkedIn", "4422822329", ""),
    ("IT-Consultant Digitales Lernen / Lernmanagementsysteme (m/w/d)", "EDEKA IT", "Hamburg, Hamburg, Germany", "On-site", "2 days ago", "2026-06-01", "5 clicked apply", "Off LinkedIn", "4418755180", ""),
    ("Director of Product (m/f/d) - SaaS/AI", "Voize", "Berlin, Berlin, Germany", "Hybrid", "Reposted 4 days ago", "2026-05-30", "Over 100 clicked apply", "Off LinkedIn", "4381609062", ""),
    ("Vice President, Product", "Andercore", "Berlin, Berlin, Germany", "", "1 week ago", "2026-05-27", "57 clicked apply", "Off LinkedIn", "4416324619", ""),
    ("Head of Product", "Annapurna", "Berlin, Germany", "On-site", "1 week ago", "2026-05-27", "Over 100 applicants", "Easy Apply", "4413610675", ""),
    ("Manager*in KI-Transformation & Anwendungen", "GP JOULE", "Hamburg, Hamburg, Germany", "Hybrid", "5 days ago", "2026-05-29", "20 clicked apply", "Off LinkedIn", "4417650908", ""),
    ("KI Transformationsmanager*in", "GP JOULE", "Hamburg, Hamburg, Germany", "Hybrid", "5 days ago", "2026-05-29", "45 clicked apply", "Off LinkedIn", "4417652862", ""),
    ("VP Product - Capital Markets", "Keyrock", "Berlin, Berlin, Germany", "Remote", "Reposted 6 days ago", "2026-05-28", "98 clicked apply", "Off LinkedIn", "4378889164", ""),
    ("AI Enablement Manager (m/f/d)", "Voize", "Berlin, Berlin, Germany", "Hybrid", "6 days ago", "2026-05-28", "73 clicked apply", "Off LinkedIn", "4419924509", ""),
    ("Chief Product Officer", "Gradias", "Germany", "Remote", "6 days ago", "2026-05-28", "Over 100 applicants", "Easy Apply", "4417241587", ""),
    ("Senior / Lead Expert (m/w/d) || Projektmanagement und Digitalisierung", "ifok GmbH", "Berlin, Berlin, Germany", "", "1 week ago", "2026-05-27", "14 clicked apply", "Off LinkedIn", "4416851471", ""),
    ("Program & Project Management Lead (m/f/d)", "Riverty", "Berlin, Berlin, Germany", "Hybrid", "Reposted 1 week ago", "2026-05-27", "Over 100 clicked apply", "Off LinkedIn", "4351756701", ""),
    ("Business Project Lead - Non Food (m/w/d)", "Tchibo GmbH", "Hamburg, Hamburg, Germany", "", "Reposted 6 days ago", "2026-05-28", "Over 100 clicked apply", "Off LinkedIn", "4364365851", ""),
    ("Product Leader (Agent Platform)", "JetBrains", "Berlin, Berlin, Germany", "Hybrid", "Reposted 2 weeks ago", "2026-05-20", "79 clicked apply", "Off LinkedIn", "4405527502", ""),
    ("Regional Product Manager/Lead – Central Europe", "Aurora Energy Research", "Berlin, Berlin, Germany", "Hybrid", "Reposted 1 week ago", "2026-05-27", "76 clicked apply", "Off LinkedIn", "4414476043", ""),
    ("(Senior) Consultant / Manager - AI Transformation (all genders)", "Forvis Mazars in Germany", "Hamburg, Hamburg, Germany", "On-site", "3 weeks ago", "2026-05-13", "6 clicked apply", "Off LinkedIn", "4411398116", ""),
    ("(Senior) Data & AI Strategy Consultant (all genders)", "msg", "Hamburg, Hamburg, Germany", "", "1 month ago", "2026-05-03", "3 clicked apply", "Off LinkedIn", "4407610046", ""),
    ("AI Business Solutions & Automation Manager / Citizen Development Enabler (m/w/d)", "Netfonds AG", "Hamburg, Hamburg, Germany", "On-site", "2 weeks ago", "2026-05-20", "9 clicked apply", "Off LinkedIn", "4410396933", ""),
    ("Transformation Director", "Amplifon", "Hamburg, Hamburg, Germany", "Hybrid", "1 week ago", "2026-05-27", "Over 100 clicked apply", "Off LinkedIn", "4419423533", ""),
    ("Transformation & Efficiency (T&E) Lead (m/w/d)", "AstraZeneca", "Hamburg, Hamburg, Germany", "", "Reposted 1 week ago", "2026-05-27", "Over 100 clicked apply", "Off LinkedIn", "4369822175", ""),
    ("Manager Organizational Excellence & Transformation (all genders)", "Eraneos", "Hamburg, Hamburg, Germany", "", "Reposted 1 week ago", "2026-05-27", "Over 100 clicked apply", "Off LinkedIn", "4399536452", ""),
    ("GenAI / AI Solution Architect (m/f/d)", "CGI", "Hamburg, Hamburg, Germany", "", "Reposted 3 weeks ago", "2026-05-13", "Over 100 clicked apply", "Off LinkedIn", "4380124027", ""),
    ("Manager Business Innovations - KI (m/w/d)", "SPORTFIVE", "Hamburg, Hamburg, Germany", "", "Reposted 2 weeks ago", "2026-05-20", "Over 100 clicked apply", "Off LinkedIn", "4404272687", ""),
    ("Head of Product (m/w/d)", "Reneo Group", "Hamburg, Hamburg, Germany", "", "Reposted 1 week ago", "2026-05-27", "Over 100 clicked apply", "Off LinkedIn", "4399649179", ""),
]


def to_jobs():
    jobs = []
    for (title, company, loc, wt, posted, pdate, appl, method, jid, notes) in ROWS:
        jobs.append({
            "title": title, "company": company, "location": loc, "work_type": wt,
            "posted": posted, "posted_date": pdate, "applicants": appl,
            "apply_method": method, "job_portal": "LinkedIn", "external_id": jid,
            "source_url": f"https://www.linkedin.com/jobs/view/{jid}/", "notes": notes,
        })
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--password", required=True)
    args = ap.parse_args()

    jobs = to_jobs()
    s = requests.Session()
    if s.post(f"{args.base_url}/api/login", json={"password": args.password}).status_code != 200:
        sys.exit("Login failed.")
    res = s.post(f"{args.base_url}/api/import", json={"portal": "LinkedIn", "jobs": jobs})
    if res.status_code != 200:
        sys.exit(f"Import failed: {res.text}")
    print(f"Seeded {len(jobs)} jobs. Result:", res.json())


if __name__ == "__main__":
    main()
