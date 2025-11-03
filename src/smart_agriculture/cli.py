"""Command-line interface entry point for SmartAgriculture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from smart_agriculture.pipelines import gcs_utils


def load_sample_configuration(config_path: Path) -> dict[str, Any]:
    """Load configuration data from a JSON file if it exists."""
    if not config_path.exists():
        return {"insight": "No configuration found. Using defaults."}

    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def generate_insight(config: dict[str, Any]) -> str:
    """Produce a placeholder insight from the configuration."""
    base = config.get("insight", "Welcome to SmartAgriculture!")
    farm_name = config.get("farm_name")
    if farm_name:
        return f"{base} Target farm: {farm_name}."
    return base


def main() -> None:
    """Run the sample CLI."""
    parser = argparse.ArgumentParser(description="SmartAgriculture CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Insight command
    parser_insight = subparsers.add_parser("insight", help="Generate a placeholder insight.")

    # GCS upload command
    parser_upload = subparsers.add_parser("upload", help="Upload a directory to GCS.")
    parser_upload.add_argument("bucket_name", help="GCS bucket name.")
    parser_upload.add_argument("source_directory", help="Local directory to upload.")
    parser_upload.add_argument("destination_blob_prefix", help="GCS destination blob prefix.")

    args = parser.parse_args()

    if args.command == "insight":
        config = load_sample_configuration(Path("../configs/sample_config.json"))
        print(generate_insight(config))
    elif args.command == "upload":
        gcs_utils.upload_files(
            args.bucket_name, args.source_directory, args.destination_blob_prefix
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
