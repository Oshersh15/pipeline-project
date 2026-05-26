"""
USD asset import utilities for Maya.

This module handles extraction of published asset packages from
GridFS-backed storage and imports USD assets back into Maya.
"""

import tempfile
from pathlib import Path

import maya.cmds as cmds

from asset_publish_tool.database.asset_repository import (
    extract_publish_package,
)


def import_asset_package(package_file_id):
    """
    Extract and import a published USD asset package into Maya.

    The package is extracted to a temporary directory before the
    contained USD/USDa asset is imported using MayaUSD.

    Args:
        package_file_id (str): GridFS package identifier.

    Returns:
        str: Path to the imported USD/USDa file.

    Raises:
        RuntimeError: If no USD/USDa file exists in the extracted package.
    """
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

    if not cmds.pluginInfo("mayaUsdPlugin", query=True, loaded=True):
        cmds.loadPlugin("mayaUsdPlugin")

    cmds.mayaUSDImport(
        file=str(usd_file),
    )

    return str(usd_file)
