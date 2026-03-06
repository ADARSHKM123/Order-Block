"""Session management and folder browsing endpoints."""

import os
import platform
import string
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..models import (
    BrowseRequest,
    BrowseResponse,
    CreateSessionRequest,
    FolderEntry,
    SessionResponse,
)
from ..services.session_manager import (
    create_session,
    delete_session,
    get_session,
    list_sessions,
)
from order_block.utils import SUPPORTED_EXTENSIONS

router = APIRouter(prefix="/api", tags=["sessions"])

IMAGE_EXTENSIONS = SUPPORTED_EXTENSIONS


@router.post("/sessions", response_model=SessionResponse)
def create_new_session(req: CreateSessionRequest, db: Session = Depends(get_db)):
    """Create a new processing session."""
    input_path = Path(req.input_path)
    if not input_path.exists():
        raise HTTPException(status_code=400, detail=f"Input path does not exist: {req.input_path}")
    if not input_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Input path is not a directory: {req.input_path}")

    # Create output dir if it doesn't exist
    output_path = Path(req.output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    return create_session(db, req)


@router.get("/sessions", response_model=list[SessionResponse])
def get_all_sessions(db: Session = Depends(get_db)):
    """List all sessions."""
    return list_sessions(db)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_one_session(session_id: str, db: Session = Depends(get_db)):
    """Get a session by ID."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}")
def remove_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a session."""
    if not delete_session(db, session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"ok": True}


@router.post("/browse", response_model=BrowseResponse)
def browse_filesystem(req: BrowseRequest):
    """Browse the local filesystem for folder selection."""
    # Determine starting path
    if req.path:
        current = Path(req.path)
    else:
        current = Path.home()

    if not current.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {req.path}")

    entries = []
    try:
        for item in sorted(current.iterdir()):
            # Skip hidden files/dirs
            if item.name.startswith("."):
                continue
            try:
                is_dir = item.is_dir()
                image_count = None
                if is_dir:
                    # Count images in subdirectory (shallow)
                    try:
                        image_count = sum(
                            1 for f in item.iterdir()
                            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
                        )
                    except PermissionError:
                        image_count = None
                elif not item.suffix.lower() in IMAGE_EXTENSIONS:
                    continue  # Only show directories and image files

                entries.append(FolderEntry(
                    name=item.name,
                    path=str(item),
                    is_dir=is_dir,
                    image_count=image_count,
                ))
            except PermissionError:
                continue
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    parent = str(current.parent) if current.parent != current else None

    # Get drives on Windows
    drives = None
    if platform.system() == "Windows":
        drives = [
            f"{d}:\\" for d in string.ascii_uppercase
            if os.path.exists(f"{d}:\\")
        ]

    return BrowseResponse(
        current_path=str(current),
        parent_path=parent,
        entries=entries,
        drives=drives,
    )
