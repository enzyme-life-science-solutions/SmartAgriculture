
import unittest
from unittest.mock import patch, mock_open, MagicMock
import pandas as pd
import numpy as np
from pathlib import Path

# Make the script importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

import export_spectra

class TestExportSpectra(unittest.TestCase):

    def setUp(self):
        """Set up test data"""
        self.meta_df = pd.DataFrame({
            'hdr_path': ['/data/sample1.hdr', '/data/ref1.hdr', '/data/sample2.hdr', '/data/ref2.hdr'],
            'sensor': ['vis', 'vis', 'swir', 'swir'],
            'timepoint': ['T1', 'T1', 'T2', 'T1'],
            'is_ref': [0, 1, 0, 1]
        })
        self.sample_row_vis = self.meta_df.iloc[0]
        self.sample_row_swir = self.meta_df.iloc[2]

    def test_pick_ref_matching_timepoint(self):
        """Test that the correct reference is picked when sensor and timepoint match."""
        ref_path = export_spectra._pick_ref(self.meta_df, self.sample_row_vis)
        self.assertEqual(ref_path, '/data/ref1.hdr')

    def test_pick_ref_fallback_sensor(self):
        """Test that a reference with the same sensor is picked when timepoint doesn't match."""
        ref_path = export_spectra._pick_ref(self.meta_df, self.sample_row_swir)
        self.assertEqual(ref_path, '/data/ref2.hdr')

    def test_pick_ref_no_ref(self):
        """Test that None is returned when no reference is available."""
        meta_df_no_ref = self.meta_df[self.meta_df['is_ref'] == 0]
        ref_path = export_spectra._pick_ref(meta_df_no_ref, self.sample_row_vis)
        self.assertIsNone(ref_path)

    def test_normalize_with_ref(self):
        """Test normalization with a reference spectrum."""
        sample_spec = np.array([1.0, 2.0, 3.0])
        ref_spec = np.array([2.0, 2.0, 2.0])
        normalized_spec = export_spectra._normalize(sample_spec, ref_spec)
        np.testing.assert_array_almost_equal(normalized_spec, np.array([0.5, 1.0, 1.5]))

    def test_normalize_no_ref(self):
        """Test normalization without a reference spectrum (fallback)."""
        sample_spec = np.array([1.0, 2.0, 100.0])
        normalized_spec = export_spectra._normalize(sample_spec, None)
        # It should clip at the 99.9th percentile
        self.assertTrue(np.all(normalized_spec <= np.percentile(sample_spec, 99.9)))

    @patch('pathlib.Path.exists', return_value=True)
    @patch('pandas.read_csv')
    @patch('export_spectra._load_cube')
    @patch('builtins.open', new_callable=mock_open)
    @patch('export_spectra.OUT_DIR.mkdir')
    @patch('export_spectra.config.REPORTS.mkdir')
    def test_main_function(self, mock_reports_mkdir, mock_out_dir_mkdir, mock_file_open, mock_load_cube, mock_read_csv, mock_path_exists):
        # Mock Path.open to use the same mock as builtins.open
        with patch('pathlib.Path.open', return_value=mock_file_open.return_value):
            # Setup mocks
            mock_read_csv.return_value = self.meta_df
            mock_load_cube.side_effect = [
                ((np.random.rand(10, 10, 3), np.array([400, 500, 600]))),  # sample1
                ((np.random.rand(10, 10, 3), np.array([400, 500, 600]))),  # ref1
                ((np.random.rand(10, 10, 3), np.array([700, 800, 900]))),  # sample2
                ((np.random.rand(10, 10, 3), np.array([700, 800, 900])))   # ref2
            ]

            # Run the main function
            export_spectra.main()

            # Assertions
            self.assertEqual(mock_file_open.call_count, 4) # 2 for spectra, 2 for logs
            # Check that the output files for the samples were opened
            mock_file_open.assert_any_call(export_spectra.OUT_DIR / 'sample1_spectrum.csv', 'w', newline='', encoding='utf-8')
            mock_file_open.assert_any_call(export_spectra.OUT_DIR / 'sample2_spectrum.csv', 'w', newline='', encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
