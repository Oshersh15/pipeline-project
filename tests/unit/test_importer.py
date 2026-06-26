import importlib
import sys
import types
from pathlib import Path

import pytest


def install_fake_maya(monkeypatch):
    fake_cmds = types.SimpleNamespace()
    fake_maya = types.SimpleNamespace(cmds=fake_cmds)

    monkeypatch.setitem(sys.modules, "maya", fake_maya)
    monkeypatch.setitem(sys.modules, "maya.cmds", fake_cmds)

    return fake_cmds


def test_import_asset_package_imports_usda_file(monkeypatch, tmp_path):
    fake_cmds = install_fake_maya(monkeypatch)

    plugin_loaded = {"loaded": False}
    imported_files = []

    def fake_plugin_info(plugin_name, query=True, loaded=True):
        return plugin_loaded["loaded"]

    def fake_load_plugin(plugin_name):
        plugin_loaded["loaded"] = True

    def fake_maya_usd_import(file):
        imported_files.append(file)

    fake_cmds.pluginInfo = fake_plugin_info
    fake_cmds.loadPlugin = fake_load_plugin
    fake_cmds.mayaUSDImport = fake_maya_usd_import

    import asset_publish_tool.maya.importer as importer

    importer = importlib.reload(importer)

    def fake_extract_publish_package(package_file_id, output_dir):
        assert package_file_id == "gridfs_id_123"
        usd_file = Path(output_dir) / "asset.usda"
        usd_file.write_text("#usda 1.0")

    monkeypatch.setattr(
        importer,
        "extract_publish_package",
        fake_extract_publish_package,
    )

    result = importer.import_asset_package("gridfs_id_123")

    assert result.endswith("asset.usda")
    assert plugin_loaded["loaded"] is True
    assert imported_files == [result]


def test_import_asset_package_uses_existing_loaded_plugin(monkeypatch):
    fake_cmds = install_fake_maya(monkeypatch)

    load_plugin_calls = []
    imported_files = []

    fake_cmds.pluginInfo = lambda plugin_name, query=True, loaded=True: True
    fake_cmds.loadPlugin = lambda plugin_name: load_plugin_calls.append(plugin_name)
    fake_cmds.mayaUSDImport = lambda file: imported_files.append(file)

    import asset_publish_tool.maya.importer as importer

    importer = importlib.reload(importer)

    def fake_extract_publish_package(package_file_id, output_dir):
        usd_file = Path(output_dir) / "asset.usd"
        usd_file.write_text("#usda 1.0")

    monkeypatch.setattr(
        importer,
        "extract_publish_package",
        fake_extract_publish_package,
    )

    result = importer.import_asset_package("gridfs_id_456")

    assert result.endswith("asset.usd")
    assert load_plugin_calls == []
    assert imported_files == [result]


def test_import_asset_package_raises_error_when_no_usd_file(monkeypatch):
    fake_cmds = install_fake_maya(monkeypatch)

    fake_cmds.pluginInfo = lambda plugin_name, query=True, loaded=True: True
    fake_cmds.loadPlugin = lambda plugin_name: None
    fake_cmds.mayaUSDImport = lambda file: None

    import asset_publish_tool.maya.importer as importer

    importer = importlib.reload(importer)

    def fake_extract_publish_package(package_file_id, output_dir):
        metadata_file = Path(output_dir) / "asset_metadata.json"
        metadata_file.write_text("{}")

    monkeypatch.setattr(
        importer,
        "extract_publish_package",
        fake_extract_publish_package,
    )

    with pytest.raises(RuntimeError, match="No USD/USDa file found"):
        importer.import_asset_package("gridfs_id_missing_usd")
