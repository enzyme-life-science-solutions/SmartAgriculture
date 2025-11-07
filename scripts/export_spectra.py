"""
Export normalized spectra from ENVI hyperspectral cubes (VISNIR/SWIR) to CSV.

Compliance rationale:
- IEC 62304: Isolates I/O parsing as a testable and traceable processing unit.
- ISO 14971: Reduces calibration risk by documenting the reference used for each sample.
- ISO/IEC 27001/27018/27701: No credentials, PHI, or network access.

Outputs:
  data_proc/{stem}_spectrum.csv  -&gt; band_idx, wavelength_nm, refl_norm, sensor, timepoint, ref_file
Trace logs:
  reports/trace_log.txt
  reports/export_spectra_run.csv
"""

import csv
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import spectral as spy

from smart_agriculture import config

META_CSV = config.OUT_DIR / "hsi_meta.csv"
OUT_DIR  = config.OUT_DIR
OUT_DIR.mkdir(parents=True, exist_ok=True)
config.REPORTS.mkdir(parents=True, exist_ok=True)


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


def _pick_ref(df: pd.DataFrame, row: pd.Series) -> str | None:
    """Pick matching cloth reference (same sensor/timepoint) or fallback to any cloth."""
    same_tp = df[(df["sensor"] == row["sensor"]) & (df["timepoint"] == row["timepoint"]) & (df["is_ref"] == 1)]
    if not same_tp.empty:
        return same_tp.iloc[0]["hdr_path"]
    any_cloth = df[(df["sensor"] == row["sensor"]) & (df["is_ref"] == 1)]
    if not any_cloth.empty:
        return any_cloth.iloc[0]["hdr_path"]
    return None


def _normalize(sample_spec: np.ndarray, ref_spec: np.ndarray | None) -> np.ndarray:
    """Normalize reflectance by cloth reference."""
    if ref_spec is None:
        # fallback: return clipped raw reflectance
        return np.clip(sample_spec, 0, np.percentile(sample_spec, 99.9))
    eps = 1e-9
    return np.clip(sample_spec / np.maximum(ref_spec, eps), 0, 2.0)


def main():
    if not META_CSV.exists():
        raise FileNotFoundError(f"Missing meta CSV: {META_CSV}. Run scripts/parse_inventory.py first.")

    meta = pd.read_csv(META_CSV)
    samples = meta[meta["is_ref"] == 0].reset_index(drop=True)
    written = 0
    logs = []

    for _, r in samples.iterrows():
        hdr_path = r["hdr_path"]
        try:
            cube_s, wl = _load_cube(hdr_path)
            spec_s = _mean_spectrum(cube_s)

            ref_hdr = _pick_ref(meta, r)
            spec_ref = None
            if ref_hdr:
                cube_r, _ = _load_cube(ref_hdr)
                spec_ref = _mean_spectrum(cube_r)

            spec_n = _normalize(spec_s, spec_ref)

            out = OUT_DIR / f"{Path(hdr_path).stem}_spectrum.csv"
            with out.open("w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["band_idx", "wavelength_nm", "refl_norm", "sensor", "timepoint", "ref_file"])
                for i, (wav, val) in enumerate(zip(wl, spec_n)):
                    w.writerow([i, float(wav), float(val), r["sensor"], r["timepoint"], ref_hdr or "NONE"])

            written += 1
            logs.append(f"OK,{Path(hdr_path).name},{r['sensor']},{r['timepoint']},{Path(ref_hdr).name if ref_hdr else 'NONE'},{out.name}")
            print(f"[OK] {out.name}")

        except Exception as e:
            logs.append(f"ERR,{Path(hdr_path).name},{r['sensor']},{r['timepoint']},-,{e}")
            print(f"[ERR] {hdr_path}: {e}")

    # traceability log
    trace = f"{datetime.now(datetime.UTC).isoformat()}Z,export_spectra,written={written},src={META_CSV}\n"
    (config.REPORTS / "trace_log.txt").open("a", encoding="utf-8").write(trace)
    (config.REPORTS / "export_spectra_run.csv").open("w", encoding="utf-8").write(
        "status,file,sensor,timepoint,ref,out\n" + "\n".join(logs)
    )

    print(f"[DONE] spectra -> {OUT_DIR}, files: {written}")


if __name__ == "__main__":
    main()
