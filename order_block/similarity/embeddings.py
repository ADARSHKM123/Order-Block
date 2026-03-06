"""CLIP embedding extraction for image similarity."""

import logging
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image
from tqdm import tqdm

logger = logging.getLogger("order_block")


def extract_embeddings(
    image_paths: List[Path],
    batch_size: int = 32,
    model_name: str = "openai/clip-vit-base-patch32",
) -> np.ndarray:
    """Extract CLIP embeddings for a list of images.

    Returns numpy array of shape (n_images, 512).
    """
    import torch
    from transformers import CLIPProcessor, CLIPModel

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading CLIP model on {device}...")

    model = CLIPModel.from_pretrained(model_name)
    processor = CLIPProcessor.from_pretrained(model_name)
    model = model.to(device)
    model.eval()

    all_embeddings = []
    failed_indices = []

    logger.info(f"Extracting embeddings for {len(image_paths)} images (batch_size={batch_size})...")

    for i in tqdm(range(0, len(image_paths), batch_size), desc="Extracting embeddings", unit="batch"):
        batch_paths = image_paths[i:i + batch_size]
        batch_images = []
        batch_valid_indices = []

        for j, path in enumerate(batch_paths):
            try:
                img = Image.open(path).convert("RGB")
                batch_images.append(img)
                batch_valid_indices.append(i + j)
            except Exception as e:
                logger.warning(f"Could not load {path.name} for embedding: {e}")
                failed_indices.append(i + j)

        if not batch_images:
            continue

        with torch.no_grad():
            inputs = processor(images=batch_images, return_tensors="pt", padding=True)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            outputs = model.get_image_features(**inputs)
            # Normalize embeddings
            embeddings = outputs / outputs.norm(dim=-1, keepdim=True)
            all_embeddings.append(embeddings.cpu().numpy())

    if not all_embeddings:
        logger.error("No embeddings could be extracted!")
        return np.zeros((len(image_paths), 512))

    embeddings_matrix = np.vstack(all_embeddings)

    # Handle failed images by inserting zero vectors
    if failed_indices:
        full_matrix = np.zeros((len(image_paths), embeddings_matrix.shape[1]))
        valid_idx = 0
        for i in range(len(image_paths)):
            if i not in failed_indices:
                full_matrix[i] = embeddings_matrix[valid_idx]
                valid_idx += 1
        embeddings_matrix = full_matrix

    logger.info(f"Extracted {embeddings_matrix.shape[0]} embeddings ({len(failed_indices)} failures)")
    return embeddings_matrix
