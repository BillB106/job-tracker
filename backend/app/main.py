"""FastAPI application: API + static frontend."""
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .db import get_db, init_db, engine
from .models import Job, PRIO_VALUES, STATUS_VALUES
from .schemas import JobCreate, JobUpdate, ImportPayload, LoginPayload
from . import auth
from .importer import import_jobs, upsert_job

app = FastAPI(title="Job Tracker")

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@app.on_event("startup")
def _startup():
    init_db()


# ---------------- auth ----------------
@app.post("/api/login")
def login(payload: LoginPayload, request: Request):
    if not auth.check_password(payload.password):
        raise HTTPException(status_code=401, detail="Wrong password")
    resp = JSONResponse({"ok": True})
    auth.issue_session(resp, request)
    return resp


@app.post("/api/logout")
def logout():
    resp = JSONResponse({"ok": True})
    auth.clear_session(resp)
    return resp


@app.get("/api/me")
def me(request: Request):
    return {"authenticated": auth.is_authenticated(request)}


@app.get("/api/meta")
def meta(_: bool = Depends(auth.require_auth)):
    """Dropdown options for the frontend."""
    return {"prio_values": PRIO_VALUES, "status_values": STATUS_VALUES}


# ---------------- jobs CRUD ----------------
@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db), _: bool = Depends(auth.require_auth)):
    jobs = db.query(Job).order_by(Job.id.asc()).all()
    return [j.as_dict() for j in jobs]


@app.post("/api/jobs")
def create_job(payload: JobCreate, db: Session = Depends(get_db),
               _: bool = Depends(auth.require_auth)):
    job, _created = upsert_job(db, payload.model_dump(), payload.job_portal)
    db.commit()
    db.refresh(job)
    return job.as_dict()


@app.patch("/api/jobs/{job_id}")
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db),
               _: bool = Depends(auth.require_auth)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    data = payload.model_dump(exclude_unset=True)
    if "prio" in data and data["prio"] not in PRIO_VALUES:
        raise HTTPException(status_code=422, detail="Invalid prio")
    if "status" in data and data["status"] not in STATUS_VALUES:
        raise HTTPException(status_code=422, detail="Invalid status")
    for k, v in data.items():
        setattr(job, k, v)
    db.commit()
    db.refresh(job)
    return job.as_dict()


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db),
               _: bool = Depends(auth.require_auth)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(job)
    db.commit()
    return {"ok": True}


# ---------------- bulk import ----------------
@app.post("/api/import")
def import_endpoint(payload: ImportPayload, db: Session = Depends(get_db),
                    _: bool = Depends(auth.require_auth)):
    result = import_jobs(db, [j.model_dump() for j in payload.jobs], payload.portal)
    return result


# ---------------- static frontend ----------------
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/healthz")
def healthz():
    # `db` reports the active backend: "postgresql" (persistent) or "sqlite" (ephemeral).
    return {"ok": True, "db": engine.dialect.name}
