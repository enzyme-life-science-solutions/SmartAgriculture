from pathlib import Path
from types import SimpleNamespace

import pytest

from smart_agriculture import dataset_sync


def test_sync_tomato_leaf_dataset_calls_uploader(tmp_path, monkeypatch):
    (tmp_path / "file.txt").write_text("payload")

    called = {}

    def fake_upload(bucket, source, prefix):
        called["bucket"] = bucket
        called["source"] = source
        called["prefix"] = prefix

    monkeypatch.setattr(dataset_sync, "gcs_utils", SimpleNamespace(upload_files=fake_upload))

    dataset_sync.sync_tomato_leaf_dataset(
        dataset_dir=tmp_path,
        bucket_name="my-bucket",
        destination_prefix="my-prefix",
    )

    assert called == {
        "bucket": "my-bucket",
        "source": str(tmp_path),
        "prefix": "my-prefix",
    }


def test_sync_tomato_leaf_dataset_missing_dir_raises(tmp_path):
    missing_dir = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        dataset_sync.sync_tomato_leaf_dataset(dataset_dir=missing_dir, bucket_name="bucket")
