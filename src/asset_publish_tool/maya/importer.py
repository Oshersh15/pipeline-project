import tempfile
from pathlib import Path

import maya.cmds as cmds

from asset_publish_tool.database.asset_repository import (
    extract_publish_package,
)


def import_asset_package(package_file_id):
    temp_dir = Path(tempfile.mkdtemp(prefix="asset_import_"))

    extract_publish_package(
        package_file_id=package_file_id,
        output_dir=temp_dir,
    )

    usd_files = list(temp_dir.glob("*.usd"))
    usda_files = list(temp_dir.glob("*.usda"))

    usd_candidates = usd_files + usda_files

    if not usd_candidates:
        raise RuntimeError("No USD/USDa file found in extracted package.")

    usd_file = usd_candidates[0]

    cmds.file(
        str(usd_file),
        i=True,
        type="USD Import",
        ignoreVersion=True,
    )

    return str(usd_file)
