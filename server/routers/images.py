"""Image serving and results endpoints."""

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.models import SessionRecord
from ..models import OverrideRequest, ResultsResponse, SessionSummary, QualityResult
from ..services.session_manager import get_session_results
from ..services.thumbnail_service import get_original, get_thumbnail

router = APIRouter(prefix="/api", tags=["images"])


@router.get("/sessions/{session_id}/results")
def get_results(session_id: str, db: Session = Depends(get_db)):
    """Get all results for a session."""
    data = get_session_results(db, session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Build clusters grouped by cluster_id
    clusters_by_id = {}
    raw_clusters = data.get("clusters", {})
    for cluster_id, members in raw_clusters.items():
        clusters_by_id[str(cluster_id)] = members

    return {
        "quality_results": data["results"],
        "cluster_assignments": data["cluster_assignments"],
        "best_picks": data["best_picks"],
        "summary": data["summary"],
        "clusters": clusters_by_id,
    }


@router.get("/sessions/{session_id}/images/{filename}")
def serve_image(
    session_id: str,
    filename: str,
    size: Optional[str] = Query(None, description="Thumbnail size: thumb, medium, or null for original"),
    db: Session = Depends(get_db),
):
    """Serve an image file (original or thumbnail)."""
    # Find the image path from session results
    data = get_session_results(db, session_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Search for the filename in results
    image_path = None
    for result in data["results"]:
        if result.get("filename") == filename:
            image_path = result.get("original_path")
            break

    if not image_path:
        raise HTTPException(status_code=404, detail=f"Image not found: {filename}")

    if size and size in ("thumb", "medium"):
        thumb_path = get_thumbnail(image_path, size)
        if thumb_path:
            return FileResponse(
                str(thumb_path),
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=3600"},
            )

    # Serve original
    original = get_original(image_path)
    if not original:
        raise HTTPException(status_code=404, detail="Image file not found on disk")

    # Detect media type
    suffix = original.suffix.lower()
    media_types = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".bmp": "image/bmp", ".tiff": "image/tiff", ".tif": "image/tiff",
    }
    media_type = media_types.get(suffix, "image/jpeg")

    return FileResponse(
        str(original),
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.put("/sessions/{session_id}/overrides")
def save_overrides(
    session_id: str,
    req: OverrideRequest,
    db: Session = Depends(get_db),
):
    """Save manual best-pick overrides."""
    record = db.query(SessionRecord).filter(SessionRecord.id == session_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Session not found")

    # Load current best picks and apply overrides
    best_picks = json.loads(record.best_picks_json or "[]")
    results = json.loads(record.results_json or "[]")
    results_by_name = {r["filename"]: r for r in results}

    for cluster_id_str, new_filename in req.overrides.items():
        # Find and update the best pick for this cluster
        for i, pick in enumerate(best_picks):
            if str(pick.get("cluster_id")) == cluster_id_str:
                if new_filename in results_by_name:
                    r = results_by_name[new_filename]
                    best_picks[i] = {
                        "filename": new_filename,
                        "original_path": r["original_path"],
                        "source": pick["source"],
                        "cluster_id": pick["cluster_id"],
                        "quality_score": r["quality_score"],
                        "selection_reason": "manual override",
                    }
                break

    record.best_picks_json = json.dumps(best_picks)
    db.commit()

    return {"ok": True, "best_picks": best_picks}
