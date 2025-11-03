"""Command-line interface entry point for SmartAgriculture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


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
    config = load_sample_configuration(Path("configs/sample_config.json"))
    print(generate_insight(config))


if __name__ == "__main__":
    main()
