from pathlib import Path


def get_next_version(publish_root, asset_type, asset_name):
    asset_path = publish_root / asset_type / asset_name

    if not asset_path.exists():
        return "v001"

    existing_versions = [
        d.name for d in asset_path.iterdir() if d.is_dir() and d.name.startswith("v")
    ]

    if not existing_versions:
        return "v001"

    latest = sorted(existing_versions)[-1]
    next_number = int(latest.replace("v", "")) + 1

    return f"v{next_number:03d}"
