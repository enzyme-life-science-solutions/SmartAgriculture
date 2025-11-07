"""
Dataset synchronization helpers for SmartAgriculture hyperspectral data.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from smart_agriculture import config
from smart_agriculture.pipelines import gcs_utils

LOGGER = logging.getLogger(__name__)  # WHAT: Module logger keeps sync traces in one stream for easier ops triage.
DEFAULT_DESTINATION_PREFIX = "datasets/tomato_leaf"  # WHAT: Canonical folder structure so every run lands in the same prefix.


def sync_tomato_leaf_dataset(
    *,
    dataset_dir: Optional[Path | str] = None,
    bucket_name: Optional[str] = None,
    destination_prefix: str = DEFAULT_DESTINATION_PREFIX,
) -> Path:
    """
    Upload the tomato leaf dataset to Cloud Storage using config defaults.
    """
    # WHAT: Resolve the working dataset path and bucket once so the rest of the function
    # reads top-to-bottom without mental backtracking.
    resolved_dataset_dir = Path(dataset_dir or config.DATA_DIR)  # WHY: Defaults tie back to config.py so auditors can trace dataset lineage (IEC 62304 §5.6).
    resolved_bucket = bucket_name or config.GCS_BUCKET  # WHY: Central bucket reference prevents ad-hoc destinations and enforces least privilege (ISO/IEC 27001).

    if not resolved_dataset_dir.exists():
        # WHY: Explicit failure keeps raw data lineage verifiable (IEC 62304, ISO 13485).
        msg = f"Dataset directory not found: {resolved_dataset_dir}"
        LOGGER.error(msg)
        raise FileNotFoundError(msg)

    LOGGER.info(
        "Syncing tomato leaf dataset from %s to bucket %s with prefix %s",
        resolved_dataset_dir,
        resolved_bucket,
        destination_prefix,
    )

    # WHAT: Delegate the actual upload to the shared helper so retries, auth, and logging stay consistent.
    gcs_utils.upload_files(
        resolved_bucket,
        str(resolved_dataset_dir),
        destination_prefix,
    )  # WHY: Single entry point enforces least-privilege upload controls (ISO/IEC 27001).

    LOGGER.info("Dataset sync completed.")
    return resolved_dataset_dir
