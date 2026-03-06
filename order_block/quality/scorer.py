"""Composite quality score calculation."""

from .analyzer import QualityMetrics


def compute_quality_score(metrics: QualityMetrics) -> float:
    """Compute a composite quality score (0-100).

    Weights:
      - Sharpness (Laplacian variance, normalized): 50%
      - Exposure quality (distance from ideal): 30%
      - Noise level (inverse, normalized): 20%
    """
    # Sharpness score (0-100)
    # Laplacian variance: 0 = totally blurry, ~500+ = very sharp
    sharpness_score = min(metrics.sharpness_laplacian / 5.0, 100.0)

    # Exposure score (0-100)
    # Ideal brightness range: 80-180
    brightness = metrics.brightness_mean
    if 80 <= brightness <= 180:
        exposure_score = 100.0
    elif brightness < 80:
        exposure_score = max(0.0, (brightness / 80.0) * 100.0)
    else:  # brightness > 180
        exposure_score = max(0.0, ((255 - brightness) / 75.0) * 100.0)

    # Penalize low histogram spread (low std dev with extreme brightness)
    if metrics.brightness_std < 30 and (brightness < 60 or brightness > 200):
        exposure_score *= 0.7

    # Noise score (0-100, inverse — lower noise = higher score)
    # MAD typically ranges 0-20 for normal images
    noise_score = max(0.0, 100.0 - (metrics.noise_estimate * 5.0))

    # Weighted composite
    score = (sharpness_score * 0.50) + (exposure_score * 0.30) + (noise_score * 0.20)
    return round(min(max(score, 0.0), 100.0), 1)
