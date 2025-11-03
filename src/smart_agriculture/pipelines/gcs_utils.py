from google.cloud import storage
import os

def upload_files(bucket_name, source_directory, destination_blob_prefix):
    """Uploads all files in a directory to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    for dirpath, _, filenames in os.walk(source_directory):
        for filename in filenames:
            local_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(local_path, source_directory)
            blob_path = os.path.join(destination_blob_prefix, relative_path)
            
            blob = bucket.blob(blob_path)
            blob.upload_from_filename(local_path)
            print(f"File {local_path} uploaded to {blob_path}.")
