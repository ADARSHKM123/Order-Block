"""Image quality assessment: blur detection, exposure analysis, noise estimation."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from ..utils import load_image_cv2

logger = logging.getLogger("order_block")


@dataclass
class QualityMetrics:
    """Quality metrics for a single image."""
    filename: str
    original_path: str
    sharpness_laplacian: float
    sharpness_tenengrad: float
    brightness_mean: float
    brightness_std: float
    noise_estimate: float
    is_blurry: bool
    is_overexposed: bool
    is_underexposed: bool


def compute_sharpness_laplacian(gray: np.ndarray) -> float:
    """Compute sharpness using Laplacian variance."""
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return float(laplacian.var())


def compute_sharpness_tenengrad(gray: np.ndarray) -> float:
    """Compute sharpness using Tenengrad (Sobel gradient magnitude)."""
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(gx ** 2 + gy ** 2)
    return float(magnitude.mean())


def compute_exposure(gray: np.ndarray) -> tuple[float, float]:
    """Compute brightness mean and standard deviation."""
    return float(gray.mean()), float(gray.std())


def compute_noise(image: np.ndarray) -> float:
    """Estimate noise using MAD on high-frequency component."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    gray = gray.astype(np.float64)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    high_freq = gray - blurred
    mad = float(np.median(np.abs(high_freq - np.median(high_freq))))
    return mad


def analyze_image(
    image_path: Path,
    blur_threshold: float = 100.0,
    overexposure_threshold: float = 220.0,
    underexposure_threshold: float = 40.0,
) -> Optional[QualityMetrics]:
    """Analyze a single image for quality metrics.

    Returns QualityMetrics or None if the image cannot be loaded.
    """
    image = load_image_cv2(image_path)
    if image is None:
        logger.error(f"Could not load image: {image_path.name}")
        return None

    # Resize large images for faster analysis (keep aspect ratio)
    h, w = image.shape[:2]
    max_dim = 2048
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    sharpness_lap = compute_sharpness_laplacian(gray)
    sharpness_ten = compute_sharpness_tenengrad(gray)
    brightness_mean, brightness_std = compute_exposure(gray)
    noise = compute_noise(image)

    is_blurry = sharpness_lap < blur_threshold
    is_overexposed = brightness_mean > overexposure_threshold
    is_underexposed = brightness_mean < underexposure_threshold

    return QualityMetrics(
        filename=image_path.name,
        original_path=str(image_path),
        sharpness_laplacian=round(sharpness_lap, 2),
        sharpness_tenengrad=round(sharpness_ten, 2),
        brightness_mean=round(brightness_mean, 2),
        brightness_std=round(brightness_std, 2),
        noise_estimate=round(noise, 2),
        is_blurry=is_blurry,
        is_overexposed=is_overexposed,
        is_underexposed=is_underexposed,
    )
