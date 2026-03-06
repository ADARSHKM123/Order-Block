"""Image loading, format detection, file discovery, and logging utilities."""

import logging
import os
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
HEIC_EXTENSIONS = {".heic", ".heif"}

logger = logging.getLogger("order_block")

# Try to import HEIC support
_heic_available = False
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    _heic_available = True
except ImportError:
    pass


def setup_logging(output_dir: Path, verbose: bool = False) -> None:
    """Configure logging to console and file."""
    level = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    root_logger = logging.getLogger("order_block")
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    output_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(output_dir / "order_block.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def discover_images(input_dir: Path) -> List[Path]:
    """Find all supported image files in the input directory (non-recursive)."""
    all_extensions = SUPPORTED_EXTENSIONS | (HEIC_EXTENSIONS if _heic_available else set())
    images = []

    if not _heic_available:
        logger.info(
            "HEIC support not available. Install pillow-heif for HEIC/HEIF support."
        )

    for entry in sorted(input_dir.iterdir()):
        if entry.is_file() and entry.suffix.lower() in all_extensions:
            images.append(entry)

    # Warn about skipped HEIC files if support is missing
    if not _heic_available:
        heic_files = [
            f for f in input_dir.iterdir()
            if f.is_file() and f.suffix.lower() in HEIC_EXTENSIONS
        ]
        if heic_files:
            logger.warning(
                f"Found {len(heic_files)} HEIC/HEIF files but pillow-heif is not installed. "
                "These files will be skipped."
            )

    logger.info(f"Discovered {len(images)} images in {input_dir}")
    return images


def load_image_cv2(path: Path) -> Optional[np.ndarray]:
    """Load an image using OpenCV. Returns BGR numpy array or None on failure."""
    try:
        img = cv2.imread(str(path))
        if img is None:
            # Try via PIL for formats OpenCV can't handle
            return load_image_via_pil(path)
        return img
    except Exception as e:
        logger.warning(f"Failed to load {path.name} with OpenCV: {e}")
        return load_image_via_pil(path)


def load_image_via_pil(path: Path) -> Optional[np.ndarray]:
    """Load an image via PIL and convert to OpenCV BGR format."""
    try:
        pil_img = Image.open(path)
        pil_img = pil_img.convert("RGB")
        arr = np.array(pil_img)
        return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    except Exception as e:
        logger.warning(f"Failed to load {path.name} via PIL: {e}")
        return None


def load_image_pil(path: Path) -> Optional[Image.Image]:
    """Load an image using PIL. Returns PIL Image or None on failure."""
    try:
        img = Image.open(path)
        img.load()  # Force load to catch corrupt files
        return img.convert("RGB")
    except Exception as e:
        logger.warning(f"Failed to load {path.name} with PIL: {e}")
        return None
