import numpy as np
import pytest

from src.smart_agriculture import features


def test_pick_band_idx_within_tolerance():
    """Cost guard: ensure we short-circuit if requested band is present."""
    wavelengths = np.array([500, 531, 570, 670, 800], dtype=float)
    idx = features.pick_band_idx(wavelengths, 531, tol=1.0)
    assert idx == 1


def test_pick_band_idx_raises_when_outside_tolerance():
    """Cost guard: refuse expensive downstream work if target band missing."""
    wavelengths = np.array([500, 531, 570], dtype=float)
    with pytest.raises(ValueError):
        features.pick_band_idx(wavelengths, 800, tol=5.0)


def test_ndvi_pri_ndwi_computations_are_bounded():
    """Ensure vegetation indices stay numerically stable to avoid re-runs."""
    assert features.ndvi(0.2, 0.8) == pytest.approx(0.6 / 1.0, rel=1e-6)
    assert features.pri(0.4, 0.2) == pytest.approx(0.2 / 0.6, rel=1e-6)
    assert features.ndwi(0.9, 0.4) == pytest.approx(0.5 / 1.3, rel=1e-6)
