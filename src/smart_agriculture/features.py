
import numpy as np

def pick_band_idx(wavelengths_nm, target_nm):
    """
    Finds the index of the band closest to the target wavelength.
    IEC 62304: This function is a modular and reusable component.
    """
    return np.argmin(np.abs(np.array(wavelengths_nm) - target_nm))

def ndvi(nir, red):
    """
    Calculates the Normalized Difference Vegetation Index (NDVI).
    IEC 62304: This function is a modular and reusable component.
    """
    return (nir - red) / (nir + red)

def pri(b531, b570):
    """
    Calculates the Photochemical Reflectance Index (PRI).
    IEC 62304: This function is a modular and reusable component.
    """
    return (b531 - b570) / (b531 + b570)

def ndwi(nir, swir):
    """
    Calculates the Normalized Difference Water Index (NDWI).
    IEC 62304: This function is a modular and reusable component.
    """
    return (nir - swir) / (nir + swir)
