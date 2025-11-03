import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile

from smart_agriculture.pipelines import gcs_utils


class GcsUtilsTest(unittest.TestCase):
    @patch("enzyme_tech.gcs_utils.storage.Client")
    def test_upload_files(self, mock_storage_client):
        # Arrange
        mock_bucket = MagicMock()
        mock_storage_client.return_value.bucket.return_value = mock_bucket

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy files
            with open(os.path.join(tmpdir, "file1.txt"), "w") as f:
                f.write("file1 content")
            os.makedirs(os.path.join(tmpdir, "subdir"))
            with open(os.path.join(tmpdir, "subdir", "file2.txt"), "w") as f:
                f.write("file2 content")

            # Act
            gcs_utils.upload_files("my-bucket", tmpdir, "my-prefix")

            # Assert
            mock_storage_client.return_value.bucket.assert_called_with("my-bucket")
            self.assertEqual(mock_bucket.blob.call_count, 2)
            mock_bucket.blob.assert_any_call("my-prefix/file1.txt")
            mock_bucket.blob.assert_any_call("my-prefix/subdir/file2.txt")


if __name__ == "__main__":
    unittest.main()
