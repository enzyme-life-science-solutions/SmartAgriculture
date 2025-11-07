#!/usr/bin/env python3
"""
WHY: Automates the hyperspectral pipeline regression to keep it a traceable test
unit (IEC 62304), enforce reflectance sanity checks that mitigate calibration
hazards (ISO 14971), and run entirely on local paths with no secrets or network
calls (ISO/IEC 27001).
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.smart_agriculture import config


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
OUT_DIR = (REPO_ROOT / config.OUT_DIR).resolve()
REPORTS_DIR = (REPO_ROOT / config.REPORTS).resolve()
TRACE_LOG = REPORTS_DIR / "trace_log.txt"
META_REQUIRED_COLUMNS = ["hdr_path", "bil_path", "sensor", "is_ref", "timepoint", "file_name"]
SPECTRUM_REQUIRED_COLUMNS = [
    "band_idx",
    "wavelength_nm",
    "refl_norm",
    "sensor",
    "timepoint",
    "ref_file",
    "norm_mode_used", # Added
]


class SelfCheckError(RuntimeError):
    """Raised when the pipeline validation fails."""


@dataclass
class MetaStats:
    rows: int
    sensor_counts: Dict[str, int]
    timepoint_counts: Dict[str, int]


@dataclass
class SpectraStats:
    files: List[Path]
    total_rows: int
    per_sensor_mean: Dict[str, float]
    norm_mode_counts: Dict[str, int] = field(default_factory=dict)


def _ensure_directories() -> None:
    """Make sure audit paths exist before running anything."""
    for path in (OUT_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def _run_pipeline_script(script_name: str) -> None:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise SelfCheckError(f"Required script missing: {script_path}")

    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH", "")
    repo_path = str(REPO_ROOT)
    env["PYTHONPATH"] = repo_path if not existing_path else f"{repo_path}:{existing_path}"
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=REPO_ROOT, env=env)


def _validate_meta(meta_path: Path) -> MetaStats:
    df = pd.read_csv(meta_path)
    if df.empty:
        raise SelfCheckError("hsi_meta.csv is empty; rerun parse_inventory with valid raw data.")

    missing_cols = [col for col in META_REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise SelfCheckError(f"hsi_meta.csv missing required columns: {', '.join(missing_cols)}")

    non_ref = df[df["is_ref"] == 0]
    if non_ref.empty:
        raise SelfCheckError("No non-cloth samples found in hsi_meta.csv")

    sensor_counts = non_ref["sensor"].str.upper().value_counts().to_dict()
    if not sensor_counts.get("VISNIR", 0) > 0 or not sensor_counts.get("SWIR", 0) > 0:
        raise SelfCheckError("Need at least one non-cloth VISNIR and SWIR sample.")

    timepoint_counts = non_ref["timepoint"].value_counts().to_dict()
    return MetaStats(
        rows=int(len(df.index)),
        sensor_counts={k: int(v) for k, v in sensor_counts.items()},
        timepoint_counts={k: int(v) for k, v in timepoint_counts.items()},
    )


def _validate_spectra() -> SpectraStats:
    spectra_files = sorted(OUT_DIR.glob("*_spectrum.csv"))
    if len(spectra_files) < 3:
        raise SelfCheckError(f"Found fewer than 3 *_spectrum.csv files. Re-run export_spectra.py.")

    sensor_means: Dict[str, List[float]] = {}
    total_rows = 0
    norm_mode_counts = Counter()

    for csv_path in spectra_files:
        # Read header to find norm_mode_used
        with open(csv_path, "r", encoding="utf-8") as f:
            first_line = f.readline()
            if "Normalization mode used" in first_line:
                mode_from_header = first_line.split(":")[-1].strip()
            else:
                mode_from_header = "UNKNOWN"

        df = pd.read_csv(csv_path, comment="#")
        missing_cols = [col for col in SPECTRUM_REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise SelfCheckError(f"{csv_path.name} missing columns: {', '.join(missing_cols)}")

        # Verify norm_mode_used column is consistent
        modes_in_col = df["norm_mode_used"].unique()
        if len(modes_in_col) != 1 or modes_in_col[0] != mode_from_header:
            raise SelfCheckError(f"Inconsistent norm_mode_used in {csv_path.name}. Header: {mode_from_header}, Column: {modes_in_col}")
        
        norm_mode = modes_in_col[0]
        norm_mode_counts[norm_mode] += 1

        refl = df["refl_norm"].to_numpy(dtype=float, copy=False)
        if not np.isfinite(refl).all():
            raise SelfCheckError(f"{csv_path.name} contains NaN or Inf reflectance values.")

        # Range checks based on normalization mode
        if norm_mode in ("CLOTH", "BASELINE"):
            if np.any((refl < 0.0) | (refl > 2.0)):
                raise SelfCheckError(f"{csv_path.name} (mode: {norm_mode}) has reflectance outside [0, 2.0].")
        elif norm_mode == "ZSCORE":
            if np.any((refl < 0.0) | (refl > 1.0)):
                raise SelfCheckError(f"{csv_path.name} (mode: {norm_mode}) has reflectance outside [0, 1.0].")

        sensor = df["sensor"].iloc[0]
        sensor_means.setdefault(sensor, []).append(float(np.nanmean(refl)))
        total_rows += len(df.index)

    per_sensor_mean = {sensor: float(np.mean(means)) for sensor, means in sensor_means.items()}

    return SpectraStats(
        files=spectra_files,
        per_sensor_mean=per_sensor_mean,
        total_rows=total_rows,
        norm_mode_counts=dict(norm_mode_counts),
    )


def _format_counts(items: Dict[str, int]) -> str:
    if not items:
        return "{}"
    ordered = ", ".join(f"'{k}': {v}" for k, v in sorted(items.items()))
    return f"{{{ordered}}}"


def _write_trace(status: str, meta_rows: int, spectra_count: int, modes: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    line = f"{timestamp},self_check,status={status},meta_rows={meta_rows},spectra_count={spectra_count},modes={_format_counts(modes)}\n"
    with TRACE_LOG.open("a", encoding="utf-8") as handle:
        handle.write(line)


def main() -> int:
    _ensure_directories()

    errors: List[str] = []
    warnings: List[str] = []

    try:
        # We don't run the scripts automatically anymore, we just check the output
        # _run_pipeline_script("parse_inventory.py")
        # _run_pipeline_script("export_spectra.py")
        
        meta_path = OUT_DIR / "hsi_meta.csv"
        if not meta_path.exists():
             raise SelfCheckError("Missing hsi_meta.csv. Run scripts/parse_inventory.py first.")

        meta_stats = _validate_meta(meta_path)
        spectra_stats = _validate_spectra()

        # Validation based on NORM_MODE
        norm_mode_config = config.NORM_MODE
        if norm_mode_config == "CLOTH" and spectra_stats.norm_mode_counts.get("CLOTH", 0) == 0:
            errors.append("NORM_MODE is CLOTH, but no spectra were processed using CLOTH normalization.")

        if norm_mode_config == "BASELINE":
            baseline_files = list(OUT_DIR.glob("baseline_*.csv"))
            if not baseline_files:
                errors.append("NORM_MODE is BASELINE, but no baseline_{sensor}.csv file was found.")

        if norm_mode_config == "AUTO":
            total_files = len(spectra_stats.files)
            zscore_files = spectra_stats.norm_mode_counts.get("ZSCORE", 0)
            if total_files > 0 and (zscore_files / total_files) > 0.25:
                warnings.append(f"{(zscore_files / total_files):.0%} of files used ZSCORE fallback. Check lighting conditions.")

        if errors:
            raise SelfCheckError("\n".join(errors))

        status = "PASS"
        report_lines = [
            "SELF-CHECK REPORT",
            f"status={status}",
            f"meta_rows={meta_stats.rows}",
            f"spectra_files={len(spectra_stats.files)}",
            f"sensors={_format_counts(meta_stats.sensor_counts)}",
            f"timepoints={_format_counts(meta_stats.timepoint_counts)}",
            f"norm_modes_used={_format_counts(spectra_stats.norm_mode_counts)}",
        ]
        print("\n".join(report_lines))
        if warnings:
            print("\nWARNINGS:")
            for warn in warnings:
                print(f"- {warn}")

        _write_trace(status, meta_stats.rows, len(spectra_stats.files), spectra_stats.norm_mode_counts)
        return 0

    except SelfCheckError as exc:
        status = "FAIL"
        print("SELF-CHECK REPORT")
        print(f"status={status}")
        print(f"error={exc}")
        _write_trace(status, meta_rows=0, spectra_count=0, modes={})
        return 1


if __name__ == "__main__":
    sys.exit(main())