"""CSV and summary report generation."""

import csv
import logging
from dataclasses import asdict, fields
from pathlib import Path
from typing import Dict, List, Optional

from .quality.analyzer import QualityMetrics

logger = logging.getLogger("order_block")


def write_quality_report(
    output_dir: Path,
    results: List[dict],
) -> Path:
    """Write quality_report.csv with all metrics per image."""
    report_path = output_dir / "quality_report.csv"
    fieldnames = [
        "filename", "original_path", "category", "sharpness_laplacian",
        "sharpness_tenengrad", "brightness_mean", "brightness_std",
        "noise_estimate", "quality_score", "is_blurry", "is_overexposed",
        "is_underexposed",
    ]

    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            # Convert booleans to lowercase strings
            row_copy = dict(row)
            for key in ("is_blurry", "is_overexposed", "is_underexposed"):
                if key in row_copy:
                    row_copy[key] = str(row_copy[key]).lower()
            writer.writerow(row_copy)

    logger.info(f"Quality report written to {report_path}")
    return report_path


def write_cluster_report(
    output_dir: Path,
    cluster_assignments: List[dict],
) -> Path:
    """Write cluster_report.csv with cluster assignments."""
    report_path = output_dir / "cluster_report.csv"
    fieldnames = ["filename", "original_path", "cluster_id", "cluster_folder"]

    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in cluster_assignments:
            writer.writerow(row)

    logger.info(f"Cluster report written to {report_path}")
    return report_path


def write_best_picks_report(
    output_dir: Path,
    picks: List[dict],
) -> Path:
    """Write best_picks_report.csv."""
    report_path = output_dir / "best_picks_report.csv"
    fieldnames = [
        "filename", "original_path", "source", "cluster_id",
        "quality_score", "selection_reason",
    ]

    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in picks:
            writer.writerow(row)

    logger.info(f"Best picks report written to {report_path}")
    return report_path


def write_summary(
    output_dir: Path,
    total: int,
    good: int,
    blurry: int,
    overexposed: int,
    underexposed: int,
    errors: int,
    num_clusters: Optional[int] = None,
    num_unique: Optional[int] = None,
    num_best_picks: Optional[int] = None,
) -> Path:
    """Write summary.txt with quick stats."""
    summary_path = output_dir / "summary.txt"
    lines = [
        "Order Block - Summary Report",
        "=" * 40,
        f"Total images processed: {total}",
        f"  Good:          {good}",
        f"  Blurry:        {blurry}",
        f"  Overexposed:   {overexposed}",
        f"  Underexposed:  {underexposed}",
        f"  Errors:        {errors}",
    ]

    if num_clusters is not None:
        lines.extend([
            "",
            "Clustering Results",
            "-" * 30,
            f"  Clusters found:  {num_clusters}",
            f"  Unique images:   {num_unique}",
        ])

    if num_best_picks is not None:
        lines.extend([
            "",
            "Best Picks",
            "-" * 30,
            f"  Selected:  {num_best_picks}",
        ])

    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info(f"Summary written to {summary_path}")
    return summary_path
