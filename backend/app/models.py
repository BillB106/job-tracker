"""SQLAlchemy ORM models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from .db import Base

# Allowed values (also enforced/offered in the frontend dropdowns).
PRIO_VALUES = [
    "Not prioritized",
    "Keep an eye on",
    "Tackle now",
    "Applied / in progress",
    "Discard / not interested",
]
STATUS_VALUES = ["Open", "Offline", "Unknown", "Archived"]

DEFAULT_PRIO = "Not prioritized"
DEFAULT_STATUS = "Open"


def _now():
    return datetime.now(timezone.utc)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("job_portal", "external_id", name="uq_portal_external"),
    )

    id = Column(Integer, primary_key=True)

    # --- scraped / source fields (overwritten on re-import) ---
    title = Column(String(500), nullable=False, default="")
    company = Column(String(300), default="")
    location = Column(String(300), default="")
    work_type = Column(String(50), default="")           # Hybrid / On-site / Remote
    posted = Column(String(100), default="")             # raw "Reposted 1 week ago"
    posted_date = Column(String(20), default="")         # YYYY-MM-DD (approx)
    applicants = Column(String(100), default="")         # "57 clicked apply"
    apply_method = Column(String(50), default="")        # Off LinkedIn / Easy Apply
    job_portal = Column(String(80), nullable=False, default="LinkedIn")
    external_id = Column(String(120), default="")        # portal-specific job id
    source_url = Column(String(800), default="")

    # --- user-owned fields (preserved on re-import) ---
    prio = Column(String(50), nullable=False, default=DEFAULT_PRIO)
    status = Column(String(20), nullable=False, default=DEFAULT_STATUS)  # open/offline state
    notes = Column(Text, default="")

    # --- bookkeeping ---
    date_added = Column(DateTime(timezone=True), default=_now)
    last_checked = Column(DateTime(timezone=True), default=_now)

    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "work_type": self.work_type,
            "posted": self.posted,
            "posted_date": self.posted_date,
            "applicants": self.applicants,
            "apply_method": self.apply_method,
            "job_portal": self.job_portal,
            "external_id": self.external_id,
            "source_url": self.source_url,
            "prio": self.prio,
            "status": self.status,
            "notes": self.notes or "",
            "date_added": self.date_added.isoformat() if self.date_added else None,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
        }
