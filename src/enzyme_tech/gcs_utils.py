"""
Shim that exposes SmartAgriculture GCS helpers through the enzyme_tech namespace.
"""
from google.cloud import storage

from smart_agriculture.pipelines.gcs_utils import upload_files as _upload_files


def upload_files(bucket_name: str, source_directory: str, destination_blob_prefix: str) -> None:
    """
    Delegate to the canonical SmartAgriculture uploader.
    """
    _upload_files(bucket_name, source_directory, destination_blob_prefix)


__all__ = ["storage", "upload_files"]
