from google.cloud import storage
import os
import logging

LOGGER = logging.getLogger(__name__)

def upload_files(bucket_name: str, source_directory: str, destination_blob_prefix: str) -> None:
    """Uploads all files in a directory to the bucket.

    Args:
        bucket_name: The name of the GCS bucket.
        source_directory: The local directory to upload.
        destination_blob_prefix: The GCS destination blob prefix.
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        for dirpath, _, filenames in os.walk(source_directory):
            for filename in filenames:
                local_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(local_path, source_directory)
                blob_path = os.path.join(destination_blob_prefix, relative_path)
                
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(local_path)
                LOGGER.info(f"File {local_path} uploaded to {blob_path}.")
    except Exception as e:
        LOGGER.error(f"An error occurred during GCS upload: {e}")
        raise
