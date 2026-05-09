from pathlib import Path

from asset_publish_tool.database.asset_repository import (
    get_latest_asset_version,
)


def get_next_version(publish_root, asset_type, asset_name):
    return get_latest_asset_version(
        asset_name,
        asset_type,
    )
