"""On-demand thumbnail generation with caching."""

import hashlib
import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from ..config import settings

logger = logging.getLogger("order_block.server")

THUMBNAIL_DIR = settings.data_dir / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(image_path: str, size: int) -> str:
    """Generate a cache key for a thumbnail."""
    h = hashlib.md5(image_path.encode()).hexdigest()[:12]
    name = Path(image_path).stem
    return f"{name}_{h}_{size}.jpg"


def get_thumbnail(image_path: str, size: str = "thumb") -> Optional[Path]:
    """Get or generate a thumbnail. Returns path to the thumbnail file."""
    max_size = settings.thumbnail_sizes.get(size, 200)
    cache_name = _cache_key(image_path, max_size)
    cache_path = THUMBNAIL_DIR / cache_name

    if cache_path.exists():
        return cache_path

    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        img.save(cache_path, "JPEG", quality=85)
        return cache_path
    except Exception as e:
        logger.error(f"Failed to generate thumbnail for {image_path}: {e}")
        return None


def get_original(image_path: str) -> Optional[Path]:
    """Verify and return the original image path."""
    p = Path(image_path)
    if p.exists():
        return p
    return None
