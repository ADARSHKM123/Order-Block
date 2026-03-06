"""Tests for the end-to-end pipeline."""

import csv
from pathlib import Path

import cv2
import numpy as np
import pytest

from order_block.pipeline import run_phase1, determine_category
from order_block.utils import setup_logging


@pytest.fixture
def sample_images(tmp_path):
    """Create a set of sample test images."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    # Good image (sharp, well-exposed)
    good = np.zeros((200, 200, 3), dtype=np.uint8)
    for i in range(0, 200, 4):
        for j in range(0, 200, 4):
            if (i // 4 + j // 4) % 2 == 0:
                good[i:i+4, j:j+4] = [180, 180, 180]
            else:
                good[i:i+4, j:j+4] = [80, 80, 80]
    cv2.imwrite(str(input_dir / "good.jpg"), good)

    # Blurry image
    blurry = cv2.GaussianBlur(good.copy(), (31, 31), 15)
    cv2.imwrite(str(input_dir / "blurry.jpg"), blurry)

    # Overexposed
    bright = np.ones((200, 200, 3), dtype=np.uint8) * 240
    cv2.imwrite(str(input_dir / "bright.jpg"), bright)

    # Underexposed
    dark = np.ones((200, 200, 3), dtype=np.uint8) * 15
    cv2.imwrite(str(input_dir / "dark.jpg"), dark)

    return input_dir


@pytest.fixture
def output_dir(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    setup_logging(output)
    return output


class TestPhase1Pipeline:
    def test_basic_sorting(self, sample_images, output_dir):
        results = run_phase1(
            input_dir=sample_images,
            output_dir=output_dir,
            workers=1,
        )
        assert len(results) == 4

        categories = {r["filename"]: r["category"] for r in results}
        # Solid-color images are also detected as blurry (low Laplacian variance),
        # and blur check has priority, so they may be classified as blurry
        assert categories["blurry.jpg"] == "blurry"
        assert categories["good.jpg"] == "good"
        # bright/dark solid images have no detail so are blurry too
        assert categories["bright.jpg"] in ("overexposed", "blurry")
        assert categories["dark.jpg"] in ("underexposed", "blurry")

    def test_csv_report_generated(self, sample_images, output_dir):
        run_phase1(input_dir=sample_images, output_dir=output_dir, workers=1)

        report = output_dir / "quality_report.csv"
        assert report.exists()

        with open(report, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 4
        assert "quality_score" in rows[0]

    def test_summary_generated(self, sample_images, output_dir):
        run_phase1(input_dir=sample_images, output_dir=output_dir, workers=1)

        summary = output_dir / "summary.txt"
        assert summary.exists()
        content = summary.read_text()
        assert "Total images processed: 4" in content

    def test_files_copied(self, sample_images, output_dir):
        run_phase1(input_dir=sample_images, output_dir=output_dir, workers=1)

        # Original files should still exist (copy mode)
        assert (sample_images / "good.jpg").exists()

        # At least some output folders should have files
        all_output_files = list(output_dir.rglob("*.jpg"))
        assert len(all_output_files) == 4

    def test_move_mode(self, sample_images, output_dir, tmp_path):
        # Create copies to move (so we don't lose test fixtures)
        move_input = tmp_path / "move_input"
        move_input.mkdir()
        import shutil
        for f in sample_images.iterdir():
            shutil.copy2(str(f), str(move_input / f.name))

        run_phase1(
            input_dir=move_input,
            output_dir=output_dir,
            workers=1,
            move=True,
        )

        # Original files should be gone
        remaining = list(move_input.glob("*.jpg"))
        assert len(remaining) == 0

    def test_empty_directory(self, tmp_path, output_dir):
        empty = tmp_path / "empty"
        empty.mkdir()
        results = run_phase1(input_dir=empty, output_dir=output_dir, workers=1)
        assert len(results) == 0

    def test_custom_thresholds(self, sample_images, output_dir):
        # Very permissive thresholds - nothing should be overexposed or underexposed
        results = run_phase1(
            input_dir=sample_images,
            output_dir=output_dir,
            blur_threshold=0.01,
            overexposure_threshold=255,
            underexposure_threshold=0,
            workers=1,
        )
        categories = [r["category"] for r in results]
        assert "overexposed" not in categories
        assert "underexposed" not in categories


class TestDetermineCategory:
    def test_blurry_priority(self):
        result = {"is_blurry": True, "is_overexposed": True, "is_underexposed": False}
        assert determine_category(result) == "blurry"

    def test_overexposed(self):
        result = {"is_blurry": False, "is_overexposed": True, "is_underexposed": False}
        assert determine_category(result) == "overexposed"

    def test_underexposed(self):
        result = {"is_blurry": False, "is_overexposed": False, "is_underexposed": True}
        assert determine_category(result) == "underexposed"

    def test_good(self):
        result = {"is_blurry": False, "is_overexposed": False, "is_underexposed": False}
        assert determine_category(result) == "good"
