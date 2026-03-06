"""CLI argument parsing and orchestration."""

import argparse
import logging
import sys
from pathlib import Path

from .utils import setup_logging
from .pipeline import run_phase1, run_phase2, run_phase3

logger = logging.getLogger("order_block")


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="order-block",
        description="AI-powered image quality assessment, similarity clustering, and best-pick selection.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input directory containing images",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        required=True,
        help="Output directory for sorted images and reports",
    )

    # File handling
    transfer = parser.add_mutually_exclusive_group()
    transfer.add_argument(
        "--copy",
        action="store_true",
        default=True,
        help="Copy files to output (default)",
    )
    transfer.add_argument(
        "--move",
        action="store_true",
        help="Move files instead of copying",
    )

    # Quality thresholds
    parser.add_argument(
        "--blur-threshold",
        type=float,
        default=100.0,
        help="Laplacian variance threshold for blur detection (default: 100)",
    )
    parser.add_argument(
        "--overexposure-threshold",
        type=float,
        default=220.0,
        help="Brightness upper limit for overexposure (default: 220)",
    )
    parser.add_argument(
        "--underexposure-threshold",
        type=float,
        default=40.0,
        help="Brightness lower limit for underexposure (default: 40)",
    )

    # Performance
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers (default: 4)",
    )

    # Phase 2 - Clustering
    parser.add_argument(
        "--cluster",
        action="store_true",
        help="Enable image similarity clustering (Phase 2)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use perceptual hashing instead of CLIP for clustering (faster, less accurate)",
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.25,
        help="DBSCAN eps for clustering sensitivity (default: 0.25, lower = stricter)",
    )
    parser.add_argument(
        "--min-cluster-size",
        type=int,
        default=2,
        help="Minimum images to form a cluster (default: 2)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for CLIP embedding extraction (default: 32)",
    )
    parser.add_argument(
        "--hash-threshold",
        type=int,
        default=15,
        help="Hamming distance threshold for perceptual hash matching in --fast mode "
             "(default: 15, higher = more aggressive grouping, range 1-30)",
    )

    # Phase 3 - Review UI
    parser.add_argument(
        "--review",
        action="store_true",
        help="Launch Streamlit review UI after processing",
    )

    # General
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output directory if it exists",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    # Validate input
    if not args.input.is_dir():
        print(f"Error: Input directory does not exist: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Handle output directory
    if args.output.exists() and not args.overwrite:
        if any(args.output.iterdir()):
            print(
                f"Warning: Output directory '{args.output}' already exists and is not empty. "
                "Use --overwrite to proceed anyway.",
                file=sys.stderr,
            )
            sys.exit(1)

    setup_logging(args.output, verbose=args.verbose)
    logger.info(f"Image Sorter starting...")
    logger.info(f"Input: {args.input}")
    logger.info(f"Output: {args.output}")

    use_move = args.move

    # Phase 1: Quality assessment
    results = run_phase1(
        input_dir=args.input,
        output_dir=args.output,
        blur_threshold=args.blur_threshold,
        overexposure_threshold=args.overexposure_threshold,
        underexposure_threshold=args.underexposure_threshold,
        workers=args.workers,
        move=use_move,
        use_cluster_structure=args.cluster,
    )

    if not results:
        logger.warning("No images were processed. Exiting.")
        sys.exit(0)

    clusters = {}
    cluster_assignments = []

    # Phase 2: Clustering
    if args.cluster:
        cluster_assignments, clusters = run_phase2(
            input_dir=args.input,
            output_dir=args.output,
            results=results,
            fast=args.fast,
            similarity_threshold=args.similarity_threshold,
            min_cluster_size=args.min_cluster_size,
            batch_size=args.batch_size,
            hash_threshold=args.hash_threshold,
        )

        # Phase 3: Best picks
        picks = run_phase3(
            output_dir=args.output,
            results=results,
            clusters=clusters,
            cluster_assignments=cluster_assignments,
            move=use_move,
        )

    # Launch review UI if requested
    if args.review:
        if not args.cluster:
            logger.error("--review requires --cluster flag")
            sys.exit(1)
        try:
            import subprocess
            ui_path = Path(__file__).parent.parent / "ui" / "app.py"
            logger.info("Launching Streamlit review UI...")
            subprocess.run(
                [sys.executable, "-m", "streamlit", "run", str(ui_path),
                 "--", str(args.output)],
            )
        except ImportError:
            logger.error("Streamlit is not installed. Install with: pip install streamlit")
            sys.exit(1)

    logger.info("Done!")
