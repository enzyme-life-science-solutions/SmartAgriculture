"""
Project-wide settings for the Smart Agriculture project.

This file centralizes settings for data paths, processing parameters, and
cloud integration.

Security Note (ISO/IEC 27001): This file contains no secrets or credentials.
"""
from pathlib import Path
import os

# --- Data and I/O ---
# Local-first layout
DATA_DIR=Path("data/tomato_leaf")   # raw HSI (*.hdr/*.bil) live here
OUT_DIR=Path("data_processed")          # processed CSVs
REPORTS  = Path("reports")            # trace logs / metrics
DASH_DIR = Path("dashboards")         # Looker-ready CSVs

GCS_BUCKET=os.getenv("GCS_BUCKET", "genomeservices-smartagri")
HDR_GLOB = "*.hdr"
VIS_TAGS = ("visnir", "vis")
SWIR_TAGS = ("swir",)
LABEL_RULES = {"before inoculation":"Healthy","0dai_2hr":"Early"}
