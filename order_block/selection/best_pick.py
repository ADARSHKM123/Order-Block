"""Best image selection per cluster."""

import logging
from typing import Dict, List

logger = logging.getLogger("order_block")


def select_best_picks(
    all_results: List[dict],
    clusters: Dict[int, List[dict]],
) -> List[dict]:
    """Select the best image from each cluster + all unique images.

    For each cluster:
      - Rank by quality_score
      - If top 2 are within 5 points, prefer higher sharpness_laplacian

    Returns list of pick dicts with selection metadata.
    """
    picks = []

    # Best pick from each cluster
    for cluster_id, members in sorted(clusters.items()):
        if not members:
            continue

        ranked = sorted(members, key=lambda r: r["quality_score"], reverse=True)
        best = ranked[0]
        reason = f"highest quality score ({best['quality_score']})"

        # Tiebreaker: if top 2 are within 5 points, prefer sharper image
        if len(ranked) >= 2:
            second = ranked[1]
            if best["quality_score"] - second["quality_score"] <= 5:
                if second["sharpness_laplacian"] > best["sharpness_laplacian"]:
                    best = second
                    reason = (
                        f"sharpness tiebreaker "
                        f"(score={best['quality_score']}, "
                        f"sharpness={best['sharpness_laplacian']})"
                    )

        picks.append({
            "filename": best["filename"],
            "original_path": best["original_path"],
            "source": f"group_{cluster_id + 1:03d}",
            "cluster_id": cluster_id,
            "quality_score": best["quality_score"],
            "selection_reason": reason,
        })

    # Add all unique images (not in any cluster)
    clustered_paths = set()
    for members in clusters.values():
        for m in members:
            clustered_paths.add(m["original_path"])

    for result in all_results:
        if result["original_path"] not in clustered_paths:
            picks.append({
                "filename": result["filename"],
                "original_path": result["original_path"],
                "source": "unique",
                "cluster_id": -1,
                "quality_score": result["quality_score"],
                "selection_reason": "unique image (no similar matches)",
            })

    logger.info(
        f"Selected {len(picks)} best picks "
        f"({len(clusters)} from clusters, "
        f"{len(picks) - len(clusters)} unique)"
    )
    return picks
