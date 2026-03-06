"""File copying/moving and folder creation."""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger("order_block")


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def transfer_file(src: Path, dest_dir: Path, move: bool = False) -> Path:
    """Copy or move a file to the destination directory.

    Handles filename collisions by appending a counter.
    Returns the destination path.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name

    # Handle filename collisions
    if dest.exists():
        counter = 1
        stem = src.stem
        suffix = src.suffix
        while dest.exists():
            dest = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    try:
        if move:
            shutil.move(str(src), str(dest))
            logger.debug(f"Moved {src.name} -> {dest}")
        else:
            shutil.copy2(str(src), str(dest))
            logger.debug(f"Copied {src.name} -> {dest}")
    except (OSError, PermissionError) as e:
        logger.error(f"Failed to {'move' if move else 'copy'} {src.name}: {e}")
        return src

    return dest


def create_output_structure(output_dir: Path, include_clusters: bool = False,
                            include_best_picks: bool = False) -> dict:
    """Create the output folder structure and return a dict of paths."""
    dirs = {
        "root": ensure_dir(output_dir),
        "good": ensure_dir(output_dir / "good"),
        "blurry": ensure_dir(output_dir / "blurry"),
        "overexposed": ensure_dir(output_dir / "overexposed"),
        "underexposed": ensure_dir(output_dir / "underexposed"),
    }

    if include_clusters:
        # Restructure under quality/ and clusters/
        dirs["quality_good"] = ensure_dir(output_dir / "quality" / "good")
        dirs["quality_blurry"] = ensure_dir(output_dir / "quality" / "blurry")
        dirs["quality_overexposed"] = ensure_dir(output_dir / "quality" / "overexposed")
        dirs["quality_underexposed"] = ensure_dir(output_dir / "quality" / "underexposed")
        dirs["clusters"] = ensure_dir(output_dir / "clusters")
        dirs["unique"] = ensure_dir(output_dir / "clusters" / "unique")

    if include_best_picks:
        dirs["best_picks"] = ensure_dir(output_dir / "best_picks")

    return dirs
