"""Pydantic request/response schemas."""
from typing import Optional, List
from pydantic import BaseModel


class JobCreate(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    work_type: str = ""
    posted: str = ""
    posted_date: str = ""
    applicants: str = ""
    apply_method: str = ""
    job_portal: str = "LinkedIn"
    external_id: str = ""
    source_url: str = ""
    prio: Optional[str] = None
    status: Optional[str] = None
    notes: str = ""


class JobUpdate(BaseModel):
    # All optional — only provided fields are changed.
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_type: Optional[str] = None
    posted: Optional[str] = None
    posted_date: Optional[str] = None
    applicants: Optional[str] = None
    apply_method: Optional[str] = None
    job_portal: Optional[str] = None
    external_id: Optional[str] = None
    source_url: Optional[str] = None
    prio: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class ImportPayload(BaseModel):
    portal: str = "LinkedIn"
    jobs: List[JobCreate]
    archive_missing: bool = False


class LoginPayload(BaseModel):
    password: str
