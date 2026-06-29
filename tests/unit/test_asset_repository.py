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


def test_retrieve_asset_to_cache_uses_shot_structure(monkeypatch, tmp_path):
    extracted_paths = []

    def fake_extract(package_file_id, output_dir):
        extracted_paths.append(output_dir)

    monkeypatch.setattr(
        asset_repository,
        "extract_publish_package",
        fake_extract,
    )

    metadata = {
        "name": "heroCharacter",
        "asset_type": "shot_animation",
        "version": "v001",
        "package_file_id": "abc123",
        "shot_name": "shot010",
        "department": "animation",
    }

    result = asset_repository.retrieve_asset_to_cache(
        metadata,
        tmp_path,
    )

    expected = tmp_path / "shots" / "shot010" / "animation" / "heroCharacter" / "v001"

    assert result == expected
    assert extracted_paths[0] == expected


def test_get_next_shot_asset_version_returns_v001_when_no_existing_publish(monkeypatch):
    captured_query = {}

    def fake_find_one(query, sort=None):
        captured_query.update(query)
        return None

    fake_collection = SimpleNamespace(find_one=fake_find_one)

    monkeypatch.setattr(
        asset_repository,
        "get_assets_collection",
        lambda: fake_collection,
    )

    version = asset_repository.get_next_shot_asset_version(
        "heroCharacter",
        "shot_animation",
        "shot010",
        "animation",
    )

    assert version == "v001"
    assert captured_query == {
        "name": "heroCharacter",
        "asset_type": "shot_animation",
        "shot_name": "shot010",
        "department": "animation",
    }


def test_get_next_shot_asset_version_increments_existing_publish(monkeypatch):
    fake_collection = SimpleNamespace(
        find_one=lambda query, sort=None: {"version": "v007"},
    )

    monkeypatch.setattr(
        asset_repository,
        "get_assets_collection",
        lambda: fake_collection,
    )

    version = asset_repository.get_next_shot_asset_version(
        "heroCharacter",
        "shot_animation",
        "shot010",
        "animation",
    )

    assert version == "v008"
