"""
Export normalized spectra from ENVI hyperspectral cubes (VISNIR/SWIR) to CSV.

Compliance rationale:
- IEC 62304: This script is a software unit with defined inputs (HSI cubes, config)
  and outputs (normalized CSVs, logs), enabling isolated testing and traceability.
  The choice of normalization is a documented configuration item.
- ISO 14971: The normalization fallback logic is a risk control measure to handle
  variable lighting conditions when a primary calibration reference (cloth) is
  not available, ensuring data usability and reducing measurement uncertainty.
- ISO/IEC 27001: The script processes no personal data, secrets, or credentials,
  and operates on a local-first file layout, minimizing security risks.
"""

import csv
import logging
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import spectral as spy

from src.smart_agriculture import config

# --- Configuration ---
META_CSV = config.OUT_DIR / "hsi_meta.csv"
OUT_DIR = config.OUT_DIR
REPORTS_DIR = config.REPORTS
NORM_MODE = config.NORM_MODE
BASELINE_RULE = config.BASELINE_RULE

# --- Setup ---
OUT_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

if not logging.getLogger().handlers:
    logging.basicConfig(
        filename=REPORTS_DIR / "trace_log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
LOGGER = logging.getLogger(__name__)


# --- Data Loading ---
def _load_cube(hdr_path: str):
    """Load ENVI cube and wavelengths."""
    img = spy.open_image(hdr_path)
    cube = img.load()
    try:
        wl = np.array(list(map(float, img.metadata.get("wavelength", []))))
        if wl.size != cube.shape[-1]:
            wl = np.arange(cube.shape[-1], dtype=float)
    except Exception:
        wl = np.arange(cube.shape[-1], dtype=float)
    return cube, wl


def _mean_spectrum(cube: np.ndarray) -> np.ndarray:
    """Compute mean reflectance across spatial dimensions."""
    return np.nanmean(cube, axis=(0, 1))


# --- Normalization Strategies ---
def _normalize_cloth(sample_spec: np.ndarray, ref_spec: np.ndarray) -> np.ndarray:
    """Normalize reflectance by cloth reference."""
    eps = 1e-9
    return np.clip(sample_spec / np.maximum(ref_spec, eps), 0, 2.0)


def _normalize_baseline(sample_spec: np.ndarray, baseline_spec: np.ndarray) -> np.ndarray:
    """Normalize reflectance by a healthy baseline spectrum."""
    eps = 1e-9
    return np.clip(sample_spec / np.maximum(baseline_spec, eps), 0, 2.0)


def _normalize_zscore(sample_spec: np.ndarray) -> np.ndarray:
    """Per-cube z-score normalization, rescaled to [0, 1]."""
    mean = np.nanmean(sample_spec)
    std = np.nanstd(sample_spec)
    if std < 1e-9:
        return np.zeros_like(sample_spec)
    z_spec = (sample_spec - mean) / std
    # Rescale to [0, 1]
    min_z, max_z = np.nanmin(z_spec), np.nanmax(z_spec)
    if max_z - min_z < 1e-9:
        return np.full_like(sample_spec, 0.5)
    return (z_spec - min_z) / (max_z - min_z)


def _get_baseline_spectrum(meta_df: pd.DataFrame, sensor: str, wavelengths: np.ndarray) -> np.ndarray | None:
    """
    Compute and persist the mean baseline spectrum for a given sensor.
    The baseline is the average of all D0 samples for that sensor.
    """
    baseline_path = OUT_DIR / f"baseline_{sensor}.csv"
    if baseline_path.exists():
        df = pd.read_csv(baseline_path)
        return df["refl_mean"].values

    baseline_samples = meta_df[
        (meta_df["sensor"] == sensor) &
        (meta_df["timepoint"] == BASELINE_RULE) &
        (meta_df["is_ref"] == 0)
    ]

    if baseline_samples.empty:
        LOGGER.warning("No baseline samples (D0) found for sensor %s", sensor)
        return None

    all_specs = []
    for _, row in baseline_samples.iterrows():
        try:
            cube, _ = _load_cube(row["hdr_path"])
            all_specs.append(_mean_spectrum(cube))
        except Exception as e:
            LOGGER.error("Failed to load baseline cube %s: %s", row["hdr_path"], e)

    if not all_specs:
        return None

    mean_baseline_spec = np.nanmean(np.array(all_specs), axis=0)

    # Persist for reuse and audit
    df = pd.DataFrame({
        "band_idx": range(len(wavelengths)),
        "wavelength_nm": wavelengths,
        "refl_mean": mean_baseline_spec
    })
    df.to_csv(baseline_path, index=False)
    LOGGER.info("Computed and saved baseline for sensor %s to %s", sensor, baseline_path)

    return mean_baseline_spec


def _pick_ref_cloth(df: pd.DataFrame, row: pd.Series) -> str | None:
    """Pick matching cloth reference (same sensor/timepoint) or fallback to any cloth."""
    same_tp = df[(df["sensor"] == row["sensor"]) & (df["timepoint"] == row["timepoint"]) & (df["is_ref"] == 1)]
    if not same_tp.empty:
        return same_tp.iloc[0]["hdr_path"]
    any_cloth = df[(df["sensor"] == row["sensor"]) & (df["is_ref"] == 1)]
    if not any_cloth.empty:
        return any_cloth.iloc[0]["hdr_path"]
    return None


def main():
    if not META_CSV.exists():
        raise FileNotFoundError(f"Missing meta CSV: {META_CSV}. Run scripts/parse_inventory.py first.")

    meta = pd.read_csv(META_CSV)
    samples = meta[meta["is_ref"] == 0].reset_index(drop=True)
    written = 0
    logs = []

    # Pre-compute baselines for all sensors present in the dataset
    all_sensors = samples["sensor"].unique()
    baselines = {}
    for sensor in all_sensors:
        # Need a sample wavelength array to save the baseline
        first_sample = samples[samples["sensor"] == sensor].iloc[0]
        try:
            _, wl = _load_cube(first_sample["hdr_path"])
            baselines[sensor] = _get_baseline_spectrum(meta, sensor, wl)
        except Exception as e:
            LOGGER.error("Could not compute baseline for sensor %s: %s", sensor, e)
            baselines[sensor] = None


    for _, r in samples.iterrows():
        hdr_path = r["hdr_path"]
        norm_mode_used = "NONE"
        ref_file_used = "NONE"
        spec_n = None

        try:
            cube_s, wl = _load_cube(hdr_path)
            spec_s = _mean_spectrum(cube_s)

            # --- AUTO Mode Resolution ---
            if NORM_MODE == "AUTO":
                ref_hdr = _pick_ref_cloth(meta, r)
                if ref_hdr:
                    norm_mode_used = "CLOTH"
                elif baselines.get(r["sensor"]) is not None:
                    norm_mode_used = "BASELINE"
                else:
                    norm_mode_used = "ZSCORE"
            else:
                norm_mode_used = NORM_MODE


            # --- Normalization Execution ---
            if norm_mode_used == "CLOTH":
                ref_hdr = _pick_ref_cloth(meta, r)
                if ref_hdr:
                    cube_r, _ = _load_cube(ref_hdr)
                    spec_ref = _mean_spectrum(cube_r)
                    spec_n = _normalize_cloth(spec_s, spec_ref)
                    ref_file_used = Path(ref_hdr).name
                else:
                    # This can happen if NORM_MODE="CLOTH" but no ref is available
                    LOGGER.warning("CLOTH mode requested but no reference found for %s. Skipping normalization.", hdr_path)
                    spec_n = np.clip(spec_s, 0, np.percentile(spec_s, 99.9)) # fallback to clipped raw
                    norm_mode_used = "NONE"

            elif norm_mode_used == "BASELINE":
                baseline_spec = baselines.get(r["sensor"])
                if baseline_spec is not None:
                    spec_n = _normalize_baseline(spec_s, baseline_spec)
                    ref_file_used = f"BASELINE_{r['sensor']}"
                else:
                    LOGGER.warning("BASELINE mode requested but no baseline found for sensor %s. Skipping normalization for %s.", r["sensor"], hdr_path)
                    spec_n = np.clip(spec_s, 0, np.percentile(spec_s, 99.9))
                    norm_mode_used = "NONE"

            elif norm_mode_used == "ZSCORE":
                spec_n = _normalize_zscore(spec_s)
                ref_file_used = "ZSCORE"

            else: # NONE or other
                 spec_n = np.clip(spec_s, 0, np.percentile(spec_s, 99.9))


            # --- Output ---
            out_path = OUT_DIR / f"{Path(hdr_path).stem}_spectrum.csv"
            with out_path.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                # Write header comment
                f.write(f"# Normalization mode used: {norm_mode_used}\n")
                w.writerow(["band_idx", "wavelength_nm", "refl_norm", "sensor", "timepoint", "ref_file", "norm_mode_used"])
                if spec_n is not None:
                    for i, (wav, val) in enumerate(zip(wl, spec_n)):
                        w.writerow([i, float(wav), float(val), r["sensor"], r["timepoint"], ref_file_used, norm_mode_used])

            written += 1
            logs.append(f"OK,{Path(hdr_path).name},{r['sensor']},{r['timepoint']},{ref_file_used},{norm_mode_used},{out_path.name}")
            print(f"[OK] {out_path.name} (mode: {norm_mode_used})")

        except Exception as e:
            logs.append(f"ERR,{Path(hdr_path).name},{r['sensor']},{r['timepoint']},-,{e},-")
            print(f"[ERR] {hdr_path}: {e}")

    # --- Logging ---
    trace = f"{datetime.now(timezone.utc).isoformat()}Z,export_spectra,written={written},src={META_CSV},norm_mode_config={NORM_MODE}\n"
    (REPORTS_DIR / "trace_log.txt").open("a", encoding="utf-8").write(trace)

    log_header = "status,file,sensor,timepoint,ref_file_used,norm_mode_used,out_path\n"
    (REPORTS_DIR / "export_spectra_run.csv").open("w", encoding="utf-8").write(
        log_header + "\n".join(logs)
    )

    print(f"[DONE] spectra -> {OUT_DIR}, files: {written}")


if __name__ == "__main__":
    main()