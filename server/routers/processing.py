"""Pipeline execution and WebSocket progress endpoints."""

import asyncio
import json
import logging
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..database.connection import get_db, SessionLocal
from ..models import StartProcessingRequest
from ..services.processing_service import ProcessingService
from ..services.session_manager import (
    get_session,
    save_session_results,
    update_session_status,
)

logger = logging.getLogger("order_block.server")
router = APIRouter(prefix="/api", tags=["processing"])

# Track active processing tasks
_active_tasks: Dict[str, ProcessingService] = {}


@router.post("/sessions/{session_id}/process")
async def start_processing(
    session_id: str,
    req: StartProcessingRequest,
    db: Session = Depends(get_db),
):
    """Start processing pipeline for a session."""
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status == "processing":
        raise HTTPException(status_code=409, detail="Session is already processing")

    update_session_status(db, session_id, "processing")

    # Run in background
    service = ProcessingService()
    _active_tasks[session_id] = service

    asyncio.create_task(_run_processing(session_id, session, req))

    return {"ok": True, "message": "Processing started"}


async def _run_processing(session_id: str, session, req: StartProcessingRequest):
    """Background task to run the pipeline."""
    db = SessionLocal()
    service = _active_tasks.get(session_id)
    if not service:
        return

    try:
        settings_dict = req.settings.model_dump()

        async def progress_callback(event: dict):
            # Store events for WebSocket clients to pick up
            if session_id in _progress_queues:
                for q in _progress_queues[session_id]:
                    await q.put(event)

        result = await service.run_pipeline(
            input_dir=session.input_path,
            output_dir=session.output_path,
            settings=settings_dict,
            progress_callback=progress_callback,
        )

        save_session_results(
            db,
            session_id,
            results=result["results"],
            clusters=result["clusters"],
            cluster_assignments=result["cluster_assignments"],
            best_picks=result["best_picks"],
            summary=result["summary"],
            settings_dict=settings_dict,
        )

    except Exception as e:
        logger.error(f"Processing error for session {session_id}: {e}")
        update_session_status(db, session_id, "error")
        if session_id in _progress_queues:
            for q in _progress_queues[session_id]:
                await q.put({"type": "error", "message": str(e)})
    finally:
        _active_tasks.pop(session_id, None)
        db.close()


@router.post("/sessions/{session_id}/cancel")
async def cancel_processing(session_id: str, db: Session = Depends(get_db)):
    """Cancel an active processing job."""
    service = _active_tasks.get(session_id)
    if not service:
        raise HTTPException(status_code=404, detail="No active processing for this session")

    service.cancel()
    update_session_status(db, session_id, "cancelled")
    return {"ok": True}


# WebSocket progress streaming
_progress_queues: Dict[str, list] = {}


@router.websocket("/api/sessions/{session_id}/progress")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """Stream processing progress via WebSocket."""
    await websocket.accept()

    queue: asyncio.Queue = asyncio.Queue()
    if session_id not in _progress_queues:
        _progress_queues[session_id] = []
    _progress_queues[session_id].append(queue)

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                await websocket.send_json(event)

                if event.get("type") in ("pipeline_complete", "error", "cancelled"):
                    break
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
    except WebSocketDisconnect:
        pass
    finally:
        if session_id in _progress_queues:
            _progress_queues[session_id].remove(queue)
            if not _progress_queues[session_id]:
                del _progress_queues[session_id]
