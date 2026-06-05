"""Upsert logic shared by the Excel seed and the LinkedIn sync.

Match key is (job_portal, external_id). On an existing match we refresh the
scraped fields but PRESERVE the user-owned fields (prio, status, notes) so a
re-import never clobbers your triage.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import Job, PRIO_VALUES, STATUS_VALUES, DEFAULT_PRIO, DEFAULT_STATUS

SCRAPED_FIELDS = [
    "title", "company", "location", "work_type", "posted",
    "posted_date", "applicants", "apply_method", "source_url",
]


def _clean_prio(value):
    return value if value in PRIO_VALUES else DEFAULT_PRIO


def _clean_status(value):
    return value if value in STATUS_VALUES else DEFAULT_STATUS


def upsert_job(db: Session, data: dict, portal: str) -> tuple[Job, bool]:
    """Insert or update one job. Returns (job, created?)."""
    portal = data.get("job_portal") or portal or "LinkedIn"
    external_id = (data.get("external_id") or "").strip()

    job = None
    if external_id:
        job = (
            db.query(Job)
            .filter(Job.job_portal == portal, Job.external_id == external_id)
            .first()
        )

    now = datetime.now(timezone.utc)
    created = False

    if job is None:
        job = Job(job_portal=portal, external_id=external_id)
        for f in SCRAPED_FIELDS:
            setattr(job, f, data.get(f, "") or "")
        # user fields: take provided value or default (only on first insert)
        job.prio = _clean_prio(data.get("prio") or DEFAULT_PRIO)
        job.status = _clean_status(data.get("status") or DEFAULT_STATUS)
        job.notes = data.get("notes", "") or ""
        job.date_added = now
        job.last_checked = now
        db.add(job)
        created = True
    else:
        # EXISTING job: refresh only the scraped fields. Prio, Status and Notes
        # are user-owned and are NEVER overwritten by a scrape/import.
        for f in SCRAPED_FIELDS:
            if data.get(f):
                setattr(job, f, data.get(f))
        job.last_checked = now

    return job, created


def import_jobs(db: Session, jobs: list[dict], portal: str) -> dict:
    created = updated = 0
    for data in jobs:
        _, was_created = upsert_job(db, data, portal)
        if was_created:
            created += 1
        else:
            updated += 1
    db.commit()
    return {"created": created, "updated": updated, "total": created + updated}
