import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from asset_publish_tool.database import asset_repository


def test_retrieve_asset_to_cache_raises_when_package_file_id_missing(tmp_path):
    metadata = {
        "name": "missing_package_asset",
        "asset_type": "model",
        "version": "v001",
    }

    with pytest.raises(ValueError, match="has no package_file_id"):
        asset_repository.retrieve_asset_to_cache(metadata, tmp_path)


def test_create_publish_package_includes_files_but_ignores_directories(tmp_path):
    version_path = tmp_path / "version"
    version_path.mkdir()

    usd_file = version_path / "asset.usda"
    usd_file.write_text("#usda 1.0")

    metadata_file = version_path / "asset_metadata.json"
    metadata_file.write_text("{}")

    nested_folder = version_path / "nested"
    nested_folder.mkdir()

    nested_file = nested_folder / "ignored.txt"
    nested_file.write_text("ignored")

    zip_buffer = asset_repository.create_publish_package(version_path)

    with zipfile.ZipFile(zip_buffer, mode="r") as zip_file:
        names = zip_file.namelist()

    assert "asset.usda" in names
    assert "asset_metadata.json" in names
    assert "nested/ignored.txt" not in names


def test_load_binary_file_returns_bytes(tmp_path):
    file_path = tmp_path / "preview.png"
    file_path.write_bytes(b"fake_binary_data")

    data = asset_repository.load_binary_file(file_path)

    assert data == b"fake_binary_data"


def test_get_next_asset_version_returns_v001_when_no_existing_asset(monkeypatch):
    fake_collection = SimpleNamespace(
        find_one=lambda query, sort=None: None,
    )

    monkeypatch.setattr(
        asset_repository,
        "get_assets_collection",
        lambda: fake_collection,
    )

    version = asset_repository.get_next_asset_version(
        "test_asset_model",
        "model",
    )

    assert version == "v001"


def test_get_next_asset_version_increments_latest_version(monkeypatch):
    fake_collection = SimpleNamespace(
        find_one=lambda query, sort=None: {"version": "v003"},
    )

    monkeypatch.setattr(
        asset_repository,
        "get_assets_collection",
        lambda: fake_collection,
    )

    version = asset_repository.get_next_asset_version(
        "test_asset_model",
        "model",
    )

    assert version == "v004"
