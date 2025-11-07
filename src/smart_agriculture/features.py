"""
Functions for calculating vegetation indices from hyperspectral data.

Compliance:
- IEC 62304: This module is a reusable software unit with defined I/O,
  facilitating modular design and testing. The functions are pure and
  do not depend on global state.
- ISO/IEC 27001: This module does not handle secrets or sensitive data.
"""

import pandas as pd
import numpy as np
from pathlib import Path

from src.smart_agriculture import config

OUT_DIR = config.OUT_DIR

def pick_band_idx(wavelengths_nm: np.ndarray, target_nm: float, tol: float = 10.0) -> int:
    """
    Finds the index of the band closest to the target wavelength within a tolerance.
    """
    diffs = np.abs(wavelengths_nm - target_nm)
    idx = np.argmin(diffs)
    if diffs[idx] > tol:
        raise ValueError(f"No band found within {tol}nm of target {target_nm}nm.")
    return idx

def ndvi(red: float, nir: float) -> float:
    """
    Calculates the Normalized Difference Vegetation Index (NDVI).
    """
    return (nir - red) / (nir + red + 1e-9)

def pri(b531: float, b570: float) -> float:
    """
    Calculates the Photochemical Reflectance Index (PRI).
    """
    return (b531 - b570) / (b531 + b570 + 1e-9)

def ndwi(nir: float, swir: float) -> float:
    """
    Calculates the Normalized Difference Water Index (NDWI).
    """
    return (nir - swir) / (nir + swir + 1e-9)


def compute_indices_from_spectrum_csv(csv_path: Path) -> Path:
    """
    Reads a *_spectrum.csv file, computes vegetation indices, and saves them
    to a new CSV in the data_processed directory.

    This function is mode-agnostic; it operates on the `refl_norm` column
    regardless of how it was generated.
    """
    df = pd.read_csv(csv_path, comment="#")
    wl = df["wavelength_nm"].to_numpy()
    refl = df["refl_norm"].to_numpy()

    # Define bands for indices
    bands = {
        "red": refl[pick_band_idx(wl, 670)],
        "nir": refl[pick_band_idx(wl, 800)],
        "b531": refl[pick_band_idx(wl, 531)],
        "b570": refl[pick_band_idx(wl, 570)],
        "swir": refl[pick_band_idx(wl, 1640)],
    }

    # Calculate indices
    indices = {
        "ndvi": ndvi(bands["red"], bands["nir"]),
        "pri": pri(bands["b531"], bands["b570"]),
        "ndwi": ndwi(bands["nir"], bands["swir"]),
    }

    # Get metadata from the first row
    meta = df.iloc[0]
    output_data = {
        "sensor": meta["sensor"],
        "timepoint": meta["timepoint"],
        "norm_mode_used": meta["norm_mode_used"],
        **indices
    }

    out_stem = csv_path.stem.replace('_spectrum', '')
    out_path = OUT_DIR / f"features_{out_stem}.csv"
    
    pd.DataFrame([output_data]).to_csv(out_path, index=False)
    
    return out_path

if __name__ == '__main__':
    # Example usage:
    # This part is for demonstration and won't run automatically.
    # You would typically call compute_indices_from_spectrum_csv from another script.
    
    # Find a sample spectrum file
    spectrum_files = list(OUT_DIR.glob("*_spectrum.csv"))
    if spectrum_files:
        print(f"Processing {spectrum_files[0]}...")
        feature_file = compute_indices_from_spectrum_csv(spectrum_files[0])
        print(f"Generated feature file: {feature_file}")
        print(pd.read_csv(feature_file).head())
    else:
        print("No spectrum CSV files found in data_processed to generate features from.")