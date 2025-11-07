"""
Configuration for the Smart Agriculture project.

This file centralizes settings for data paths, processing parameters, and
compliance-related traceability flags.

- NORM_MODE: Controls the normalization strategy for hyperspectral data.
  This is a risk control measure (ISO 14971) to handle variations in lighting
  conditions when a standard reference (cloth) is unavailable. Traceable to
  IEC 62304, as it defines a critical processing parameter.
- BASELINE_RULE: Defines the timepoint considered the "healthy" baseline for
  normalization.

Security Note (ISO/IEC 27001): This file contains no secrets or credentials.
"""

from pathlib import Path

# --- Normalization Policy ---
# IEC 62304: This setting is a configuration item that determines a critical
# data processing path.
# ISO 14971: This is a risk control measure for inconsistent lighting.
NORM_MODE = "AUTO"        # "AUTO" | "CLOTH" | "BASELINE" | "ZSCORE"
BASELINE_RULE = "D0"      # which timepoint is considered healthy baseline (e.g., "D0")

def is_baseline_timepoint(tp: str) -> bool:
    """Checks if a timepoint matches the healthy baseline rule."""
    return tp == BASELINE_RULE


# --- Data and I/O ---
# Local-first layout
DATA_DIR=Path("data/tomato_leaf")   # raw HSI (*.hdr/*.bil) live here
OUT_DIR=Path("data_processed")          # processed CSVs
REPORTS  = Path("reports")            # trace logs / metrics
DASH_DIR = Path("dashboards")         # Looker-ready CSVs

import os

GCS_BUCKET=os.getenv("GCS_BUCKET", "genomeservices-smartagri")
HDR_GLOB = "*.hdr"
VIS_TAGS = ("visnir", "vis")
SWIR_TAGS = ("swir",)
LABEL_RULES = {"before inoculation":"Healthy","0dai_2hr":"Early"}
