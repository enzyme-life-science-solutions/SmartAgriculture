from pathlib import Path

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