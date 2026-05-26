"""
Metadata file utilities for published assets.

This module handles reading and writing JSON metadata files
used during the publishing workflow and temporary packaging stage.
"""

import json
from pathlib import Path

from asset_publish_tool.core.asset import Asset


def write_metadata(asset: Asset, metadata_path: Path) -> None:
    """
    Write asset metadata to a JSON file.

    The parent directory is created automatically if it does not exist.

    Args:
        asset (Asset): Asset instance containing publish metadata.
        metadata_path (Path): Output JSON metadata file path.
    """
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    with open(metadata_path, "w") as f:
        json.dump(asset.to_dict(), f, indent=4)


def read_metadata(metadata_path: Path) -> dict:
    """
    Read and return asset metadata from a JSON file.

    Args:
        metadata_path (Path): Path to the metadata JSON file.

    Returns:
        dict: Parsed metadata dictionary.

    Raises:
        FileNotFoundError: If the metadata file does not exist.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, "r") as f:
        return json.load(f)
