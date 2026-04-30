import json
from pathlib import Path

from asset_publish_tool.core.asset import Asset


def write_metadata(asset: Asset, metadata_path: Path) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    with open(metadata_path, "w") as f:
        json.dump(asset.to_dict(), f, indent=4)


def read_metadata(metadata_path: Path) -> dict:
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    with open(metadata_path, "r") as f:
        return json.load(f)
