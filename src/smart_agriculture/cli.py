"""Command-line interface entry point for SmartAgriculture."""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from smart_agriculture import config, dataset_sync, inventory
from smart_agriculture.pipelines import gcs_utils


def load_sample_configuration(config_path: Path) -> dict[str, Any]:
    """Load configuration data from a JSON file if it exists."""
    if not config_path.exists():
        return {"insight": "No configuration found. Using defaults."}

    with config_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def generate_insight(config_data: dict[str, Any]) -> str:
    """Produce a placeholder insight from the configuration."""
    base = config_data.get("insight", "Welcome to SmartAgriculture!")
    farm_name = config_data.get("farm_name")
    if farm_name:
        return f"{base} Target farm: {farm_name}."
    return base


def process_insight(input_dir: str, out_dir: str) -> None:
    """Process the insight data."""
    input_path = Path(input_dir)
    output_path = Path(out_dir)
    output_path.mkdir(exist_ok=True)
    with open(output_path / "file_list.txt", "w") as f:
        for file_path in input_path.glob("**/*"):
            f.write(f"{file_path.name}\n")
    logging.info(f"Processed data from {input_dir} and saved results to {out_dir}")


def main() -> None:
    """Run the sample CLI."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="SmartAgriculture CLI")
    subparsers = parser.add_subparsers(dest="command")

    parser_insight = subparsers.add_parser("insight", help="Generate a placeholder insight.")
    parser_insight.add_argument("--input_dir", default=config.DATA_DIR, help="Input directory for insight generation.")
    parser_insight.add_argument("--out_dir", default=config.OUT_DIR, help="Output directory for insight generation.")

    parser_upload = subparsers.add_parser("upload", help="Upload a directory to GCS.")
    parser_upload.add_argument("source_directory", nargs="?", default=config.OUT_DIR, help="Local directory to upload.")
    parser_upload.add_argument("destination_blob_prefix", help="GCS destination blob prefix.")

    parser_sync = subparsers.add_parser(
        "sync-data",
        help="Sync the tomato leaf dataset to the configured Cloud Storage bucket.",
    )
    parser_sync.add_argument(
        "--dataset-dir",
        default=config.DATA_DIR,
        help="Override the dataset directory (default: %(default)s).",
    )
    parser_sync.add_argument(
        "--bucket",
        default=config.GCS_BUCKET,
        help="Override the target bucket (default: %(default)s).",
    )
    parser_sync.add_argument(
        "--destination-prefix",
        default=dataset_sync.DEFAULT_DESTINATION_PREFIX,
        help="Override the GCS prefix (default: %(default)s).",
    )

    parser_inventory = subparsers.add_parser(
        "parse-inventory",
        help="Parse the hyperspectral inventory and generate metadata.",
    )
    parser_inventory.add_argument(
        "--data-dir",
        default=config.DATA_DIR,
        help="Override the data directory (default: %(default)s).",
    )
    parser_inventory.add_argument(
        "--out-dir",
        default=config.OUT_DIR,
        help="Override the output directory (default: %(default)s).",
    )

    args = parser.parse_args()

    try:
        if args.command == "insight":
            process_insight(args.input_dir, args.out_dir)
        elif args.command == "upload":
            gcs_utils.upload_files(
                config.GCS_BUCKET, args.source_directory, args.destination_blob_prefix
            )
        elif args.command == "sync-data":
            dataset_sync.sync_tomato_leaf_dataset(
                dataset_dir=args.dataset_dir,
                bucket_name=args.bucket,
                destination_prefix=args.destination_prefix,
            )
        elif args.command == "parse-inventory":
            inventory.parse_inventory(data_dir=args.data_dir, out_dir=args.out_dir)
        else:
            parser.print_help()
    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
