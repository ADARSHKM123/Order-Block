# Image Sorter

Local-only CLI tool for AI-powered image quality assessment, similarity clustering, and best-pick selection.

## Installation

```bash
cd order-block
pip install -e .
```

For clustering (Phase 2):
```bash
pip install -e ".[clustering]"
```

For Streamlit review UI (Phase 3):
```bash
pip install -e ".[all]"
```

For HEIC/HEIF support:
```bash
pip install -e ".[heic]"
```

## Usage

### Phase 1: Quality Assessment & Sorting

```bash
python -m order_block /path/to/photos --output ./sorted
```

With custom thresholds:
```bash
python -m order_block /path/to/photos --output ./sorted \
  --blur-threshold 120 \
  --overexposure-threshold 210 \
  --underexposure-threshold 50 \
  --workers 8 \
  --verbose
```

### Phase 2: Similarity Clustering

```bash
# CLIP-based clustering (more accurate)
python -m order_block /path/to/photos --output ./sorted --cluster

# Fast mode using perceptual hashing only
python -m order_block /path/to/photos --output ./sorted --cluster --fast

# Custom clustering sensitivity
python -m order_block /path/to/photos --output ./sorted --cluster \
  --similarity-threshold 0.2 \
  --min-cluster-size 2
```

### Phase 3: Review UI

```bash
python -m order_block /path/to/photos --output ./sorted --cluster --review
```

### All Options

| Flag | Default | Description |
|------|---------|-------------|
| `--output` / `-o` | (required) | Output directory |
| `--copy` | yes | Copy files (default) |
| `--move` | no | Move files instead of copying |
| `--blur-threshold` | 100 | Laplacian variance threshold |
| `--overexposure-threshold` | 220 | Brightness upper limit |
| `--underexposure-threshold` | 40 | Brightness lower limit |
| `--workers` | 4 | Parallel processing workers |
| `--cluster` | off | Enable similarity clustering |
| `--fast` | off | Use perceptual hash instead of CLIP |
| `--similarity-threshold` | 0.25 | DBSCAN eps (lower = stricter) |
| `--min-cluster-size` | 2 | Min images per cluster |
| `--batch-size` | 32 | CLIP batch size |
| `--review` | off | Launch Streamlit review UI |
| `--overwrite` | off | Overwrite existing output |
| `--verbose` / `-v` | off | Debug logging |

## Output Structure

### Phase 1 Only
```
output/
├── good/
├── blurry/
├── overexposed/
├── underexposed/
├── quality_report.csv
└── summary.txt
```

### With Clustering (Phase 2+3)
```
output/
├── quality/
│   ├── good/
│   ├── blurry/
│   ├── overexposed/
│   └── underexposed/
├── clusters/
│   ├── group_001/
│   ├── group_002/
│   └── unique/
├── best_picks/
├── quality_report.csv
├── cluster_report.csv
├── best_picks_report.csv
└── summary.txt
```

## Running Tests

```bash
pip install pytest
pytest tests/
```
