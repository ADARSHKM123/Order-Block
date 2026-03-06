"""Perceptual hashing for fast near-duplicate detection."""

import logging
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image
from tqdm import tqdm

logger = logging.getLogger("order_block")


def compute_phash(image_path: Path, hash_size: int = 8):
    """Compute perceptual hash for an image."""
    import imagehash
    try:
        img = Image.open(image_path).convert("RGB")
        return imagehash.phash(img, hash_size=hash_size)
    except Exception as e:
        logger.warning(f"Could not compute hash for {image_path.name}: {e}")
        return None


def cluster_by_hash(
    image_paths: List[Path],
    threshold: int = 10,
) -> List[int]:
    """Cluster images by perceptual hash similarity.

    Uses union-find to group images with hamming distance < threshold.
    Returns list of cluster labels (-1 for unclustered).
    """
    import imagehash

    logger.info(f"Computing perceptual hashes for {len(image_paths)} images...")
    hashes = []
    for path in tqdm(image_paths, desc="Computing hashes", unit="img"):
        hashes.append(compute_phash(path))

    # Union-Find
    n = len(image_paths)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Compare all pairs
    logger.info("Finding near-duplicates...")
    for i in range(n):
        if hashes[i] is None:
            continue
        for j in range(i + 1, n):
            if hashes[j] is None:
                continue
            distance = hashes[i] - hashes[j]
            if distance < threshold:
                union(i, j)

    # Convert to cluster labels
    groups = {}
    labels = [-1] * n
    cluster_id = 0

    for i in range(n):
        if hashes[i] is None:
            continue
        root = find(i)
        if root not in groups:
            groups[root] = cluster_id
            cluster_id += 1
        labels[i] = groups[root]

    # Mark singletons as -1
    from collections import Counter
    label_counts = Counter(l for l in labels if l != -1)
    for i in range(n):
        if labels[i] != -1 and label_counts[labels[i]] < 2:
            labels[i] = -1

    # Re-number clusters sequentially
    old_to_new = {}
    new_id = 0
    final_labels = []
    for l in labels:
        if l == -1:
            final_labels.append(-1)
        else:
            if l not in old_to_new:
                old_to_new[l] = new_id
                new_id += 1
            final_labels.append(old_to_new[l])

    num_clusters = len(old_to_new)
    num_unique = sum(1 for l in final_labels if l == -1)
    logger.info(f"Hash clustering: {num_clusters} clusters, {num_unique} unique images")

    return final_labels
