"""Session lifecycle management."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from ..database.models import SessionRecord
from ..models import (
    CreateSessionRequest,
    ProcessingSettings,
    SessionResponse,
    SessionStatus,
    SessionSummary,
)
from order_block.utils import discover_images, SUPPORTED_EXTENSIONS, HEIC_EXTENSIONS


def create_session(db: Session, req: CreateSessionRequest) -> SessionResponse:
    """Create a new processing session."""
    session_id = str(uuid.uuid4())[:8]
    name = req.name or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    # Count images in input directory
    input_path = Path(req.input_path)
    image_count = 0
    if input_path.exists() and input_path.is_dir():
        all_ext = SUPPORTED_EXTENSIONS
        image_count = sum(
            1 for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in all_ext
        )

    record = SessionRecord(
        id=session_id,
        name=name,
        input_path=req.input_path,
        output_path=req.output_path,
        status="pending",
        image_count=image_count,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return _to_response(record)


def get_session(db: Session, session_id: str) -> Optional[SessionResponse]:
    """Get a session by ID."""
    record = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
    if not record:
        return None
    return _to_response(record)


def list_sessions(db: Session) -> List[SessionResponse]:
    """List all sessions, most recent first."""
    records = db.query(SessionRecord).order_by(SessionRecord.created_at.desc()).all()
    return [_to_response(r) for r in records]


def update_session_status(db: Session, session_id: str, status: str):
    """Update session status."""
    record = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
    if record:
        record.status = status
        record.updated_at = datetime.now(timezone.utc)
        db.commit()


def save_session_results(
    db: Session,
    session_id: str,
    results: list,
    clusters: dict,
    cluster_assignments: list,
    best_picks: list,
    summary: dict,
    settings_dict: dict,
):
    """Save processing results to the session."""
    record = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
    if record:
        record.results_json = json.dumps(results)
        record.clusters_json = json.dumps(
            {str(k): v for k, v in clusters.items()}
        )
        record.cluster_assignments_json = json.dumps(cluster_assignments)
        record.best_picks_json = json.dumps(best_picks)
        record.summary_json = json.dumps(summary)
        record.settings_json = json.dumps(settings_dict)
        record.status = "complete"
        record.updated_at = datetime.now(timezone.utc)
        db.commit()


def get_session_results(db: Session, session_id: str) -> Optional[dict]:
    """Get full results for a session."""
    record = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
    if not record:
        return None

    return {
        "results": json.loads(record.results_json or "[]"),
        "clusters": json.loads(record.clusters_json or "{}"),
        "cluster_assignments": json.loads(record.cluster_assignments_json or "[]"),
        "best_picks": json.loads(record.best_picks_json or "[]"),
        "summary": json.loads(record.summary_json or "{}"),
    }


def delete_session(db: Session, session_id: str) -> bool:
    """Delete a session."""
    record = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def _to_response(record: SessionRecord) -> SessionResponse:
    """Convert a database record to a response model."""
    settings = None
    if record.settings_json and record.settings_json != "{}":
        try:
            settings = ProcessingSettings(**json.loads(record.settings_json))
        except Exception:
            pass

    summary = None
    if record.summary_json and record.summary_json != "{}":
        try:
            summary = SessionSummary(**json.loads(record.summary_json))
        except Exception:
            pass

    return SessionResponse(
        id=record.id,
        name=record.name,
        input_path=record.input_path,
        output_path=record.output_path,
        status=SessionStatus(record.status),
        created_at=record.created_at.isoformat() if record.created_at else "",
        updated_at=record.updated_at.isoformat() if record.updated_at else "",
        settings=settings,
        summary=summary,
        image_count=record.image_count or 0,
    )
