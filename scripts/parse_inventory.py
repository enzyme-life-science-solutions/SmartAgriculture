
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.smart_agriculture import config

RAW_DATA_DIR = Path(config.DATA_DIR)
PROCESSED_DIR = Path(config.OUT_DIR)
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)  # WHY: Shared log destination keeps traceability artifacts centralized (ISO 13485).

if not logging.getLogger().handlers:
    logging.basicConfig(
        filename=REPORTS_DIR / "trace_log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )  # WHY: Consistent log format supports tamper-evident evidence trails (ISO/IEC 27001 A.12.4).

LOGGER = logging.getLogger(__name__)


def _determine_timepoint(filename: str) -> str:
    """
    Infer the sampling timepoint from the filename convention.
    Maps "before inoculation" to "D0" to align with baseline rule.
    """
    # IEC 62304: This function maps a raw filename to a controlled vocabulary.
    if "before inoculation" in filename or "_bi_" in filename:
        return "D0"

    if "2h" in filename:
        return "2h"

    match = re.search(r"(\d+)dai", filename)
    if match:
        return f"D{match.group(1)}"

    # Fallback for other cases, though the data format is expected to be consistent.
    return "UNKNOWN"


def parse_inventory(data_dir: Path = RAW_DATA_DIR, out_dir: Path = PROCESSED_DIR) -> Path:
    """
    Parse the hyperspectral inventory and persist metadata for auditing.

    Data citation: Li, S., 2024. Data from: Hyperspectral Imaging Analysis for Early Detection of
    Tomato Bacterial Leaf Spot Disease. https://doi.org/10.15482/USDA.ADC/26046328.v2
    """
    LOGGER.info("Starting metadata extraction from %s", data_dir)

    if not data_dir.exists():
        # WHY: Deterministic failure surface prevents silent data drift per IEC 62304 risk controls.
        msg = f"Data directory not found: {data_dir}"
        LOGGER.error(msg)
        raise FileNotFoundError(msg)

    out_dir.mkdir(parents=True, exist_ok=True)  # WHY: Pre-creating targets preserves ISO 13485 traceability outputs.

    hdr_files = sorted(data_dir.rglob("*.hdr"))
    if not hdr_files:
        LOGGER.warning("No .hdr files discovered under %s", data_dir)

    metadata: List[Dict[str, Any]] = []
    for hdr_path in hdr_files:
        filename = hdr_path.name
        lower_name = filename.lower()
        upper_name = filename.upper()

        if "VISNIR" in upper_name:
            sensor = "VISNIR"
        elif "SWIR" in upper_name:
            sensor = "SWIR"
        else:
            sensor = "UNKNOWN"

        is_ref = "cloth" in lower_name
        timepoint = _determine_timepoint(lower_name)
        bil_path = hdr_path.with_suffix(".bil")
        if not bil_path.exists():
            LOGGER.warning("Missing .bil pairing for %s", hdr_path)

        metadata.append(
            {
                "hdr_path": str(hdr_path),
                "bil_path": str(bil_path),
                "sensor": sensor,
                "is_ref": is_ref,
                "timepoint": timepoint,
                "file_name": filename,
            }
        )  # WHY: Structured metadata provides device history traceability (ISO 13485 §7.5).

    df = pd.DataFrame(metadata)
    csv_path = out_dir / "hsi_meta.csv"
    df.to_csv(csv_path, index=False)

    d0_count = len(df[df["timepoint"] == "D0"])
    LOGGER.info(f"{d0_count} rows identified as D0 baseline.")

    LOGGER.info("Generated %s with %d records", csv_path, len(df.index))
    print(f"Successfully generated {csv_path}")

    return csv_path


if __name__ == "__main__":
    parse_inventory()
