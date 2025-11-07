#!/usr/bin/env bash
#
# Syncs data to/from GCS.
# Docs are part of the dataset contract; README.md files are always synced.
#
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"; BUCKET="${PROJECT_ID}-smartagri"

case "${1:-}" in
  up)
    # -C: checksums, -d: delete, -r: recursive
    gsutil -m rsync -C -r -d data "gs://$BUCKET/data"
    gsutil -m rsync -C -r -d data_processed "gs://$BUCKET/data_processed"
    ;;
  down)
    gsutil -m rsync -C -r -d "gs://$BUCKET/data" data
    gsutil -m rsync -C -r -d "gs://$BUCKET/data_processed" data_processed
    ;;
  *)
    echo "Usage: $0 {up|down}" >&2; exit 2 ;;
esac
