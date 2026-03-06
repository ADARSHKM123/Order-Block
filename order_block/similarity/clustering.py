"""DBSCAN clustering on image embeddings."""

import logging
from typing import List

import numpy as np
from sklearn.cluster import DBSCAN

logger = logging.getLogger("order_block")


def cluster_embeddings(
    embeddings: np.ndarray,
    eps: float = 0.25,
    min_samples: int = 2,
) -> List[int]:
    """Cluster embeddings using DBSCAN with cosine distance.

    Returns list of cluster labels (-1 for noise/unique).
    """
    logger.info(f"Clustering {embeddings.shape[0]} embeddings (eps={eps}, min_samples={min_samples})...")

    clustering = DBSCAN(
        eps=eps,
        min_samples=min_samples,
        metric="cosine",
    )
    labels = clustering.fit_predict(embeddings)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_unique = int(np.sum(labels == -1))

    logger.info(f"DBSCAN found {n_clusters} clusters, {n_unique} unique images")

    return labels.tolist()
