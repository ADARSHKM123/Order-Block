"""Tests for quality analysis modules."""

import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from order_block.quality.analyzer import (
    QualityMetrics,
    analyze_image,
    compute_exposure,
    compute_noise,
    compute_sharpness_laplacian,
    compute_sharpness_tenengrad,
)
from order_block.quality.scorer import compute_quality_score


@pytest.fixture
def sharp_image(tmp_path):
    """Create a sharp test image with high-frequency detail."""
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    # Add checkerboard pattern for high sharpness
    for i in range(0, 200, 4):
        for j in range(0, 200, 4):
            if (i // 4 + j // 4) % 2 == 0:
                img[i:i+4, j:j+4] = [200, 200, 200]
    path = tmp_path / "sharp.jpg"
    cv2.imwrite(str(path), img)
    return path


@pytest.fixture
def blurry_image(tmp_path):
    """Create a blurry test image."""
    img = np.ones((200, 200, 3), dtype=np.uint8) * 128
    # Add slight gradient (very little detail)
    for i in range(200):
        img[i, :] = int(125 + 5 * np.sin(i / 50))
    img = cv2.GaussianBlur(img, (31, 31), 10)
    path = tmp_path / "blurry.jpg"
    cv2.imwrite(str(path), img)
    return path


@pytest.fixture
def bright_image(tmp_path):
    """Create an overexposed test image."""
    img = np.ones((200, 200, 3), dtype=np.uint8) * 240
    path = tmp_path / "bright.jpg"
    cv2.imwrite(str(path), img)
    return path


@pytest.fixture
def dark_image(tmp_path):
    """Create an underexposed test image."""
    img = np.ones((200, 200, 3), dtype=np.uint8) * 20
    path = tmp_path / "dark.jpg"
    cv2.imwrite(str(path), img)
    return path


class TestSharpness:
    def test_laplacian_sharp_image(self, sharp_image):
        img = cv2.imread(str(sharp_image), cv2.IMREAD_GRAYSCALE)
        variance = compute_sharpness_laplacian(img)
        assert variance > 100, f"Sharp image should have high Laplacian variance, got {variance}"

    def test_laplacian_blurry_image(self, blurry_image):
        img = cv2.imread(str(blurry_image), cv2.IMREAD_GRAYSCALE)
        variance = compute_sharpness_laplacian(img)
        assert variance < 100, f"Blurry image should have low Laplacian variance, got {variance}"

    def test_tenengrad_sharp_image(self, sharp_image):
        img = cv2.imread(str(sharp_image), cv2.IMREAD_GRAYSCALE)
        score = compute_sharpness_tenengrad(img)
        assert score > 10, f"Sharp image should have high Tenengrad score, got {score}"


class TestExposure:
    def test_normal_exposure(self, sharp_image):
        img = cv2.imread(str(sharp_image), cv2.IMREAD_GRAYSCALE)
        mean, std = compute_exposure(img)
        assert 30 < mean < 230

    def test_overexposed(self, bright_image):
        img = cv2.imread(str(bright_image), cv2.IMREAD_GRAYSCALE)
        mean, std = compute_exposure(img)
        assert mean > 220

    def test_underexposed(self, dark_image):
        img = cv2.imread(str(dark_image), cv2.IMREAD_GRAYSCALE)
        mean, std = compute_exposure(img)
        assert mean < 40


class TestNoise:
    def test_noise_estimation(self, sharp_image):
        img = cv2.imread(str(sharp_image))
        noise = compute_noise(img)
        assert noise >= 0

    def test_noisy_image_higher_estimate(self, tmp_path):
        # Create clean image
        clean = np.ones((200, 200, 3), dtype=np.uint8) * 128
        # Create noisy version
        noisy = clean.copy()
        rng = np.random.RandomState(42)
        noisy = np.clip(noisy.astype(np.int16) + rng.normal(0, 25, noisy.shape).astype(np.int16), 0, 255).astype(np.uint8)

        noise_clean = compute_noise(clean)
        noise_noisy = compute_noise(noisy)
        assert noise_noisy > noise_clean


class TestAnalyzeImage:
    def test_analyze_sharp(self, sharp_image):
        metrics = analyze_image(sharp_image)
        assert metrics is not None
        assert not metrics.is_blurry
        assert not metrics.is_overexposed
        assert not metrics.is_underexposed

    def test_analyze_blurry(self, blurry_image):
        metrics = analyze_image(blurry_image)
        assert metrics is not None
        assert metrics.is_blurry

    def test_analyze_overexposed(self, bright_image):
        metrics = analyze_image(bright_image)
        assert metrics is not None
        assert metrics.is_overexposed

    def test_analyze_underexposed(self, dark_image):
        metrics = analyze_image(dark_image)
        assert metrics is not None
        assert metrics.is_underexposed

    def test_analyze_nonexistent(self, tmp_path):
        result = analyze_image(tmp_path / "nonexistent.jpg")
        assert result is None

    def test_custom_thresholds(self, sharp_image):
        # With very high blur threshold, even a sharp image is "blurry"
        metrics = analyze_image(sharp_image, blur_threshold=999999)
        assert metrics is not None
        assert metrics.is_blurry


class TestQualityScore:
    def test_score_range(self, sharp_image):
        metrics = analyze_image(sharp_image)
        score = compute_quality_score(metrics)
        assert 0 <= score <= 100

    def test_sharp_scores_higher(self, sharp_image, blurry_image):
        sharp_metrics = analyze_image(sharp_image)
        blurry_metrics = analyze_image(blurry_image)
        sharp_score = compute_quality_score(sharp_metrics)
        blurry_score = compute_quality_score(blurry_metrics)
        assert sharp_score > blurry_score

    def test_good_exposure_scores_higher(self, sharp_image, bright_image):
        normal_metrics = analyze_image(sharp_image)
        bright_metrics = analyze_image(bright_image)
        normal_score = compute_quality_score(normal_metrics)
        bright_score = compute_quality_score(bright_metrics)
        assert normal_score > bright_score
