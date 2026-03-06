"""Main pipeline orchestrating all phases."""

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tqdm import tqdm

from .file_manager import create_output_structure, transfer_file, ensure_dir
from .quality.analyzer import QualityMetrics, analyze_image
from .quality.scorer import compute_quality_score
from .reporter import (
    write_best_picks_report,
    write_cluster_report,
    write_quality_report,
    write_summary,
)
from .utils import discover_images

logger = logging.getLogger("order_block")


def _analyze_single(args: tuple) -> Optional[Tuple[dict, float]]:
    """Worker function for parallel quality analysis.

    Takes a tuple of (image_path, blur_thresh, over_thresh, under_thresh).
    Returns (metrics_dict_with_score, quality_score) or None.
    """
    path, blur_thresh, over_thresh, under_thresh = args
    metrics = analyze_image(
        Path(path),
        blur_threshold=blur_thresh,
        overexposure_threshold=over_thresh,
        underexposure_threshold=under_thresh,
    )
    if metrics is None:
        return None
    score = compute_quality_score(metrics)
    result = asdict(metrics)
    result["quality_score"] = score
    return result, score


def determine_category(result: dict) -> str:
    """Determine the quality category for an image."""
    if result["is_blurry"]:
        return "blurry"
    if result["is_overexposed"]:
        return "overexposed"
    if result["is_underexposed"]:
        return "underexposed"
    return "good"


def run_phase1(
    input_dir: Path,
    output_dir: Path,
    blur_threshold: float = 100.0,
    overexposure_threshold: float = 220.0,
    underexposure_threshold: float = 40.0,
    workers: int = 4,
    move: bool = False,
    use_cluster_structure: bool = False,
) -> List[dict]:
    """Run Phase 1: quality assessment and sorting.

    Returns list of result dicts (metrics + quality_score + category).
    """
    images = discover_images(input_dir)
    if not images:
        logger.warning("No images found in the input directory.")
        return []

    dirs = create_output_structure(
        output_dir,
        include_clusters=use_cluster_structure,
        include_best_picks=False,
    )

    # Build worker args
    work_items = [
        (str(img), blur_threshold, overexposure_threshold, underexposure_threshold)
        for img in images
    ]

    results = []
    errors = 0
    counts = {"good": 0, "blurry": 0, "overexposed": 0, "underexposed": 0}

    logger.info(f"Analyzing {len(images)} images with {workers} workers...")

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_analyze_single, item): item for item in work_items}
        with tqdm(total=len(futures), desc="Analyzing quality", unit="img") as pbar:
            for future in as_completed(futures):
                pbar.update(1)
                try:
                    outcome = future.result()
                except Exception as e:
                    errors += 1
                    item = futures[future]
                    logger.error(f"Error processing {Path(item[0]).name}: {e}")
                    continue

                if outcome is None:
                    errors += 1
                    continue

                result, score = outcome
                category = determine_category(result)
                result["category"] = category
                counts[category] += 1
                results.append(result)

                # Transfer file to appropriate folder
                src = Path(result["original_path"])
                if use_cluster_structure:
                    dest_key = f"quality_{category}"
                else:
                    dest_key = category
                transfer_file(src, dirs[dest_key], move=move)

    # Write reports
    write_quality_report(output_dir, results)
    write_summary(
        output_dir,
        total=len(images),
        good=counts["good"],
        blurry=counts["blurry"],
        overexposed=counts["overexposed"],
        underexposed=counts["underexposed"],
        errors=errors,
    )

    logger.info(
        f"Phase 1 complete: {counts['good']} good, {counts['blurry']} blurry, "
        f"{counts['overexposed']} overexposed, {counts['underexposed']} underexposed, "
        f"{errors} errors"
    )
    return results


def run_phase2(
    input_dir: Path,
    output_dir: Path,
    results: List[dict],
    fast: bool = False,
    similarity_threshold: float = 0.25,
    min_cluster_size: int = 2,
    batch_size: int = 32,
    hash_threshold: int = 15,
) -> Tuple[List[dict], Dict[int, List[dict]]]:
    """Run Phase 2: similarity clustering.

    Returns (cluster_assignments, clusters_dict).
    clusters_dict maps cluster_id -> list of result dicts.
    """
    if fast:
        try:
            from .similarity.hashing import cluster_by_hash
        except ImportError:
            logger.error(
                "Fast clustering requires 'imagehash'. "
                "Install with: pip install imagehash"
            )
            raise SystemExit(1)
        cluster_labels = cluster_by_hash(
            [Path(r["original_path"]) for r in results],
            threshold=hash_threshold,
        )
    else:
        try:
            from .similarity.embeddings import extract_embeddings
            from .similarity.clustering import cluster_embeddings
        except ImportError:
            logger.error(
                "CLIP clustering requires 'torch', 'transformers', and 'scikit-learn'. "
                "Install with: pip install torch transformers scikit-learn\n"
                "Or use --fast for lightweight perceptual-hash duplicate detection "
                "(requires: pip install imagehash)"
            )
            raise SystemExit(1)

        image_paths = [Path(r["original_path"]) for r in results]
        embeddings = extract_embeddings(image_paths, batch_size=batch_size)
        cluster_labels = cluster_embeddings(
            embeddings,
            eps=similarity_threshold,
            min_samples=min_cluster_size,
        )

    # Organize into clusters
    dirs = create_output_structure(output_dir, include_clusters=True)
    clusters: Dict[int, List[dict]] = {}
    cluster_assignments = []

    for result, label in zip(results, cluster_labels):
        if label == -1:
            folder_name = "unique"
            dest_dir = dirs["unique"]
        else:
            folder_name = f"group_{label + 1:03d}"
            dest_dir = ensure_dir(output_dir / "clusters" / folder_name)
            clusters.setdefault(label, []).append(result)

        src = Path(result["original_path"])
        transfer_file(src, dest_dir, move=False)

        cluster_assignments.append({
            "filename": result["filename"],
            "original_path": result["original_path"],
            "cluster_id": label if label != -1 else "unique",
            "cluster_folder": folder_name,
        })

    num_unique = sum(1 for l in cluster_labels if l == -1)
    write_cluster_report(output_dir, cluster_assignments)

    # Update summary
    quality_counts = {"good": 0, "blurry": 0, "overexposed": 0, "underexposed": 0}
    for r in results:
        quality_counts[r["category"]] += 1

    write_summary(
        output_dir,
        total=len(results),
        good=quality_counts["good"],
        blurry=quality_counts["blurry"],
        overexposed=quality_counts["overexposed"],
        underexposed=quality_counts["underexposed"],
        errors=0,
        num_clusters=len(clusters),
        num_unique=num_unique,
    )

    logger.info(f"Phase 2 complete: {len(clusters)} clusters, {num_unique} unique images")
    return cluster_assignments, clusters


def run_phase3(
    output_dir: Path,
    results: List[dict],
    clusters: Dict[int, List[dict]],
    cluster_assignments: List[dict],
    move: bool = False,
) -> List[dict]:
    """Run Phase 3: best pick selection.

    Returns list of best pick dicts.
    """
    from .selection.best_pick import select_best_picks

    dirs = create_output_structure(output_dir, include_clusters=True, include_best_picks=True)
    picks = select_best_picks(results, clusters)

    for pick in picks:
        src = Path(pick["original_path"])
        transfer_file(src, dirs["best_picks"], move=False)

    write_best_picks_report(output_dir, picks)

    # Update summary with best picks count
    quality_counts = {"good": 0, "blurry": 0, "overexposed": 0, "underexposed": 0}
    for r in results:
        quality_counts[r["category"]] += 1

    num_unique = sum(1 for a in cluster_assignments if a["cluster_id"] == "unique")
    num_clusters = len(clusters)

    write_summary(
        output_dir,
        total=len(results),
        good=quality_counts["good"],
        blurry=quality_counts["blurry"],
        overexposed=quality_counts["overexposed"],
        underexposed=quality_counts["underexposed"],
        errors=0,
        num_clusters=num_clusters,
        num_unique=num_unique,
        num_best_picks=len(picks),
    )

    logger.info(f"Phase 3 complete: {len(picks)} best picks selected")
    return picks
