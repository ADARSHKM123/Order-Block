"""Streamlit review UI for image sorter results."""

import csv
import sys
from pathlib import Path

import streamlit as st
from PIL import Image


def load_csv(path: Path) -> list[dict]:
    """Load a CSV file into a list of dicts."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def make_thumbnail(image_path: str, max_size: int = 300) -> Image.Image:
    """Load and resize image for thumbnail display."""
    try:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((max_size, max_size))
        return img
    except Exception:
        return None


def main():
    st.set_page_config(page_title="Image Sorter Review", layout="wide")
    st.title("Image Sorter - Review UI")

    # Get output directory from command line args
    if len(sys.argv) > 1:
        output_dir = Path(sys.argv[-1])
    else:
        output_dir = Path(st.text_input("Output directory path:", ""))
        if not output_dir or not output_dir.exists():
            st.warning("Please provide the output directory path.")
            return

    if not output_dir.exists():
        st.error(f"Directory not found: {output_dir}")
        return

    # Load reports
    quality_data = load_csv(output_dir / "quality_report.csv")
    cluster_data = load_csv(output_dir / "cluster_report.csv")
    best_picks_data = load_csv(output_dir / "best_picks_report.csv")

    # Initialize session state for overrides
    if "overrides" not in st.session_state:
        st.session_state.overrides = {}

    # Sidebar filters
    st.sidebar.header("Filters")
    view_mode = st.sidebar.radio(
        "View",
        ["All Clusters", "Quality Categories", "Best Picks"],
    )

    if view_mode == "Quality Categories":
        _show_quality_view(quality_data)
    elif view_mode == "All Clusters":
        _show_clusters_view(cluster_data, quality_data, best_picks_data, output_dir)
    elif view_mode == "Best Picks":
        _show_best_picks_view(best_picks_data, quality_data)


def _show_quality_view(quality_data: list[dict]):
    """Show images grouped by quality category."""
    st.header("Quality Categories")

    category_filter = st.selectbox(
        "Category", ["all", "good", "blurry", "overexposed", "underexposed"]
    )

    filtered = quality_data
    if category_filter != "all":
        filtered = [q for q in quality_data if q.get("category") == category_filter]

    st.write(f"Showing {len(filtered)} images")

    cols = st.columns(4)
    for i, item in enumerate(filtered):
        with cols[i % 4]:
            thumb = make_thumbnail(item["original_path"])
            if thumb:
                st.image(thumb, caption=item["filename"], use_container_width=True)
                st.caption(
                    f"Score: {item.get('quality_score', 'N/A')} | "
                    f"Category: {item.get('category', 'N/A')}"
                )


def _show_clusters_view(
    cluster_data: list[dict],
    quality_data: list[dict],
    best_picks_data: list[dict],
    output_dir: Path,
):
    """Show images grouped by cluster."""
    st.header("Image Clusters")

    if not cluster_data:
        st.info("No clustering data found. Run with --cluster flag first.")
        return

    # Build quality lookup
    quality_map = {q["filename"]: q for q in quality_data}
    best_picks_set = {b["filename"] for b in best_picks_data}

    # Group by cluster
    clusters = {}
    for item in cluster_data:
        cid = item["cluster_id"]
        clusters.setdefault(cid, []).append(item)

    # Show each cluster
    for cluster_id, members in sorted(clusters.items(), key=lambda x: str(x[0])):
        if cluster_id == "unique":
            continue

        with st.expander(f"Cluster {cluster_id} ({len(members)} images)", expanded=True):
            cols = st.columns(min(len(members), 4))
            for i, member in enumerate(members):
                with cols[i % len(cols)]:
                    thumb = make_thumbnail(member["original_path"])
                    if thumb:
                        filename = member["filename"]
                        is_best = filename in best_picks_set
                        override_key = f"cluster_{cluster_id}"

                        # Check for override
                        is_selected = st.session_state.overrides.get(
                            override_key, filename if is_best else None
                        ) == filename

                        border = "2px solid #00ff00" if is_selected else "none"
                        st.image(thumb, use_container_width=True)

                        quality = quality_map.get(filename, {})
                        score = quality.get("quality_score", "N/A")
                        label = f"{'[SELECTED] ' if is_selected else ''}{filename}"
                        st.caption(f"{label}\nScore: {score}")

                        if st.button(
                            "Select" if not is_selected else "Selected",
                            key=f"btn_{cluster_id}_{filename}",
                            disabled=is_selected,
                        ):
                            st.session_state.overrides[override_key] = filename
                            st.rerun()

    # Show unique images
    unique_images = clusters.get("unique", [])
    if unique_images:
        with st.expander(f"Unique Images ({len(unique_images)})", expanded=False):
            cols = st.columns(4)
            for i, member in enumerate(unique_images):
                with cols[i % 4]:
                    thumb = make_thumbnail(member["original_path"])
                    if thumb:
                        quality = quality_map.get(member["filename"], {})
                        st.image(thumb, use_container_width=True)
                        st.caption(
                            f"{member['filename']}\n"
                            f"Score: {quality.get('quality_score', 'N/A')}"
                        )

    # Export button
    st.divider()
    export_dir = st.text_input("Export directory:", str(output_dir / "final_selection"))
    if st.button("Export Selections"):
        _export_selections(
            export_dir, cluster_data, best_picks_data,
            st.session_state.overrides, quality_map
        )
        st.success(f"Exported to {export_dir}")


def _show_best_picks_view(best_picks_data: list[dict], quality_data: list[dict]):
    """Show the auto-selected best picks."""
    st.header("Best Picks")

    if not best_picks_data:
        st.info("No best picks data found.")
        return

    st.write(f"{len(best_picks_data)} images selected")

    cols = st.columns(4)
    for i, pick in enumerate(best_picks_data):
        with cols[i % 4]:
            thumb = make_thumbnail(pick["original_path"])
            if thumb:
                st.image(thumb, use_container_width=True)
                st.caption(
                    f"{pick['filename']}\n"
                    f"Score: {pick.get('quality_score', 'N/A')}\n"
                    f"From: {pick.get('source', 'N/A')}\n"
                    f"Reason: {pick.get('selection_reason', 'N/A')}"
                )


def _export_selections(
    export_dir: str,
    cluster_data: list[dict],
    best_picks_data: list[dict],
    overrides: dict,
    quality_map: dict,
):
    """Export final selections (with overrides applied) to a directory."""
    import shutil

    dest = Path(export_dir)
    dest.mkdir(parents=True, exist_ok=True)

    # Build set of filenames to export
    best_picks_by_cluster = {}
    for pick in best_picks_data:
        cid = pick.get("cluster_id", "unique")
        best_picks_by_cluster[f"cluster_{cid}"] = pick

    # Apply overrides
    selected_files = {}
    for key, pick in best_picks_by_cluster.items():
        override_filename = overrides.get(key)
        if override_filename:
            selected_files[override_filename] = pick["original_path"]
        else:
            selected_files[pick["filename"]] = pick["original_path"]

    # Find original paths for overridden files
    path_map = {item["filename"]: item["original_path"] for item in cluster_data}
    for filename in selected_files:
        if filename in path_map:
            selected_files[filename] = path_map[filename]

    # Copy files
    for filename, original_path in selected_files.items():
        src = Path(original_path)
        if src.exists():
            shutil.copy2(str(src), str(dest / src.name))


if __name__ == "__main__":
    main()
