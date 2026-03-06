"""Processing service wrapping the existing pipeline with progress callbacks."""

import asyncio
import json
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional

from order_block.file_manager import create_output_structure, transfer_file, ensure_dir
from order_block.pipeline import _analyze_single, determine_category
from order_block.reporter import (
    write_best_picks_report,
    write_cluster_report,
    write_quality_report,
    write_summary,
)
from order_block.utils import discover_images

logger = logging.getLogger("order_block.server")

ProgressCallback = Callable[[dict], Coroutine[Any, Any, None]]


class ProcessingService:
    """Wraps the order_block pipeline with async progress reporting."""

    def __init__(self):
        self._cancel_flag = False

    def cancel(self):
        self._cancel_flag = True

    async def run_pipeline(
        self,
        input_dir: str,
        output_dir: str,
        settings: dict,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> dict:
        """Run the full pipeline with progress events.

        Returns dict with results, clusters, cluster_assignments, best_picks, summary.
        """
        self._cancel_flag = False
        input_path = Path(input_dir)
        output_path = Path(output_dir)

        async def emit(event: dict):
            if progress_callback:
                try:
                    await progress_callback(event)
                except Exception:
                    pass

        # Discover images
        images = discover_images(input_path)
        if not images:
            await emit({"type": "error", "message": "No images found in input directory"})
            return {"results": [], "clusters": {}, "cluster_assignments": [], "best_picks": [], "summary": {}}

        await emit({"type": "session_info", "image_count": len(images)})

        # Phase 1: Quality Assessment
        await emit({"type": "phase_start", "phase": "quality", "total": len(images)})
        results = await self._run_phase1(
            images, output_path, settings, emit
        )

        if self._cancel_flag:
            await emit({"type": "cancelled"})
            return {"results": results, "clusters": {}, "cluster_assignments": [], "best_picks": [], "summary": {}}

        quality_counts = {"good": 0, "blurry": 0, "overexposed": 0, "underexposed": 0}
        for r in results:
            quality_counts[r["category"]] += 1

        await emit({
            "type": "phase_complete",
            "phase": "quality",
            "stats": quality_counts,
        })

        # Phase 2: Clustering (if enabled)
        clusters = {}
        cluster_assignments = []
        if settings.get("cluster", True) and len(results) > 0:
            await emit({"type": "phase_start", "phase": "clustering", "total": len(results)})
            cluster_assignments, clusters = await self._run_phase2(
                input_path, output_path, results, settings, emit
            )
            num_unique = sum(1 for a in cluster_assignments if a["cluster_id"] == "unique")
            await emit({
                "type": "phase_complete",
                "phase": "clustering",
                "stats": {"clusters": len(clusters), "unique": num_unique},
            })

        # Phase 3: Best Pick Selection
        best_picks = []
        if clusters:
            await emit({"type": "phase_start", "phase": "best_picks", "total": len(clusters)})
            best_picks = await self._run_phase3(
                output_path, results, clusters, cluster_assignments, settings, emit
            )
            await emit({
                "type": "phase_complete",
                "phase": "best_picks",
                "stats": {"count": len(best_picks)},
            })

        summary = {
            "total": len(images),
            **quality_counts,
            "errors": len(images) - len(results),
            "num_clusters": len(clusters) if clusters else None,
            "num_unique": sum(1 for a in cluster_assignments if a["cluster_id"] == "unique") if cluster_assignments else None,
            "num_best_picks": len(best_picks) if best_picks else None,
        }

        await emit({"type": "pipeline_complete", "summary": summary})

        return {
            "results": results,
            "clusters": clusters,
            "cluster_assignments": cluster_assignments,
            "best_picks": best_picks,
            "summary": summary,
        }

    async def _run_phase1(
        self,
        images: List[Path],
        output_dir: Path,
        settings: dict,
        emit: ProgressCallback,
    ) -> List[dict]:
        """Run quality assessment with progress reporting."""
        blur_thresh = settings.get("blur_threshold", 100.0)
        over_thresh = settings.get("overexposure_threshold", 220.0)
        under_thresh = settings.get("underexposure_threshold", 40.0)
        workers = settings.get("workers", 4)
        move = settings.get("move", False)
        use_clusters = settings.get("cluster", True)

        dirs = create_output_structure(output_dir, include_clusters=use_clusters)

        work_items = [
            (str(img), blur_thresh, over_thresh, under_thresh)
            for img in images
        ]

        results = []
        errors = 0
        loop = asyncio.get_event_loop()

        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_analyze_single, item): item for item in work_items}
            completed = 0
            for future in as_completed(futures):
                if self._cancel_flag:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                completed += 1
                item = futures[future]
                image_name = Path(item[0]).name

                try:
                    outcome = future.result()
                except Exception as e:
                    errors += 1
                    logger.error(f"Error processing {image_name}: {e}")
                    await emit({
                        "type": "progress",
                        "phase": "quality",
                        "current": completed,
                        "total": len(futures),
                        "image": image_name,
                        "status": "error",
                    })
                    continue

                if outcome is None:
                    errors += 1
                    await emit({
                        "type": "progress",
                        "phase": "quality",
                        "current": completed,
                        "total": len(futures),
                        "image": image_name,
                        "status": "error",
                    })
                    continue

                result, score = outcome
                category = determine_category(result)
                result["category"] = category
                results.append(result)

                # Transfer file
                src = Path(result["original_path"])
                if use_clusters:
                    dest_key = f"quality_{category}"
                else:
                    dest_key = category
                transfer_file(src, dirs[dest_key], move=move)

                await emit({
                    "type": "progress",
                    "phase": "quality",
                    "current": completed,
                    "total": len(futures),
                    "image": image_name,
                    "category": category,
                    "score": score,
                    "status": "ok",
                })

        # Write reports
        write_quality_report(output_dir, results)
        counts = {"good": 0, "blurry": 0, "overexposed": 0, "underexposed": 0}
        for r in results:
            counts[r["category"]] += 1
        write_summary(
            output_dir,
            total=len(images),
            good=counts["good"],
            blurry=counts["blurry"],
            overexposed=counts["overexposed"],
            underexposed=counts["underexposed"],
            errors=errors,
        )

        return results

    async def _run_phase2(
        self,
        input_dir: Path,
        output_dir: Path,
        results: List[dict],
        settings: dict,
        emit: ProgressCallback,
    ):
        """Run clustering with progress reporting."""
        fast = settings.get("fast", False)

        await emit({
            "type": "progress",
            "phase": "clustering",
            "current": 1,
            "total": 3,
            "step": "loading_model" if not fast else "computing_hashes",
        })

        if fast:
            from order_block.similarity.hashing import cluster_by_hash
            cluster_labels = cluster_by_hash(
                [Path(r["original_path"]) for r in results],
                threshold=settings.get("hash_threshold", 15),
            )
        else:
            from order_block.similarity.embeddings import extract_embeddings
            from order_block.similarity.clustering import cluster_embeddings

            await emit({
                "type": "progress",
                "phase": "clustering",
                "current": 1,
                "total": 3,
                "step": "extracting_embeddings",
            })

            image_paths = [Path(r["original_path"]) for r in results]
            embeddings = extract_embeddings(
                image_paths,
                batch_size=settings.get("batch_size", 32),
            )

            await emit({
                "type": "progress",
                "phase": "clustering",
                "current": 2,
                "total": 3,
                "step": "clustering",
            })

            cluster_labels = cluster_embeddings(
                embeddings,
                eps=settings.get("similarity_threshold", 0.25),
                min_samples=settings.get("min_cluster_size", 2),
            )

        await emit({
            "type": "progress",
            "phase": "clustering",
            "current": 3,
            "total": 3,
            "step": "organizing_files",
        })

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

        write_cluster_report(output_dir, cluster_assignments)

        # Update summary
        quality_counts = {"good": 0, "blurry": 0, "overexposed": 0, "underexposed": 0}
        for r in results:
            quality_counts[r["category"]] += 1
        num_unique = sum(1 for l in cluster_labels if l == -1)

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

        return cluster_assignments, clusters

    async def _run_phase3(
        self,
        output_dir: Path,
        results: List[dict],
        clusters: Dict[int, List[dict]],
        cluster_assignments: List[dict],
        settings: dict,
        emit: ProgressCallback,
    ) -> List[dict]:
        """Run best pick selection."""
        from order_block.selection.best_pick import select_best_picks

        dirs = create_output_structure(output_dir, include_clusters=True, include_best_picks=True)
        picks = select_best_picks(results, clusters)

        for pick in picks:
            src = Path(pick["original_path"])
            transfer_file(src, dirs["best_picks"], move=False)

        write_best_picks_report(output_dir, picks)

        # Update summary
        quality_counts = {"good": 0, "blurry": 0, "overexposed": 0, "underexposed": 0}
        for r in results:
            quality_counts[r["category"]] += 1
        num_unique = sum(1 for a in cluster_assignments if a["cluster_id"] == "unique")

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
            num_best_picks=len(picks),
        )

        await emit({
            "type": "progress",
            "phase": "best_picks",
            "current": len(picks),
            "total": len(picks),
        })

        return picks
