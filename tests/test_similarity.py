"""Tests for similarity/clustering modules."""

import numpy as np
import pytest
from pathlib import Path
import cv2


class TestHashClustering:
    def test_identical_images_clustered(self, tmp_path):
        """Identical images should be in the same cluster."""
        from order_block.similarity.hashing import cluster_by_hash

        # Create two identical images
        img = np.ones((100, 100, 3), dtype=np.uint8) * 128
        cv2.rectangle(img, (20, 20), (80, 80), (255, 0, 0), -1)

        path1 = tmp_path / "img1.jpg"
        path2 = tmp_path / "img2.jpg"
        cv2.imwrite(str(path1), img)
        cv2.imwrite(str(path2), img)

        labels = cluster_by_hash([path1, path2], threshold=10)
        assert labels[0] == labels[1]
        assert labels[0] != -1

    def test_different_images_not_clustered(self, tmp_path):
        """Very different images should not be clustered."""
        from order_block.similarity.hashing import cluster_by_hash

        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255
        cv2.rectangle(img1, (10, 10), (90, 90), (255, 255, 255), -1)

        path1 = tmp_path / "black.jpg"
        path2 = tmp_path / "white.jpg"
        cv2.imwrite(str(path1), img1)
        cv2.imwrite(str(path2), img2)

        labels = cluster_by_hash([path1, path2], threshold=5)
        # They should either both be -1 or in different clusters
        assert labels[0] == -1 or labels[1] == -1 or labels[0] != labels[1]


class TestDBSCANClustering:
    def test_similar_embeddings_clustered(self):
        """Similar embeddings should be in the same cluster."""
        from order_block.similarity.clustering import cluster_embeddings

        rng = np.random.RandomState(42)
        # Create two clusters of similar embeddings
        cluster1 = rng.randn(3, 512) + np.array([1.0] * 512)
        cluster2 = rng.randn(3, 512) + np.array([-1.0] * 512)
        # Normalize
        cluster1 = cluster1 / np.linalg.norm(cluster1, axis=1, keepdims=True)
        cluster2 = cluster2 / np.linalg.norm(cluster2, axis=1, keepdims=True)

        embeddings = np.vstack([cluster1, cluster2])
        labels = cluster_embeddings(embeddings, eps=0.5, min_samples=2)

        # First 3 should be same cluster, last 3 same cluster, different from each other
        assert labels[0] == labels[1] == labels[2]
        assert labels[3] == labels[4] == labels[5]
        assert labels[0] != labels[3]

    def test_unique_embeddings(self):
        """Very different embeddings should be marked as unique (-1)."""
        from order_block.similarity.clustering import cluster_embeddings

        # Create very spread out embeddings
        embeddings = np.eye(5, 512)  # Orthogonal vectors
        labels = cluster_embeddings(embeddings, eps=0.1, min_samples=2)

        assert all(l == -1 for l in labels)
