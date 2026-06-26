from pathlib import Path

import pytest

from asset_publish_tool.core.asset import Asset
from asset_publish_tool.core.metadata import read_metadata, write_metadata


def make_test_asset() -> Asset:
    return Asset(
        name="test_asset_model",
        asset_type="model",
        source_scene=Path("/project/scenes/test_asset.ma"),
        version="v001",
        publish_path="/tmp/publish/test_asset_model/v001",
        author="pytest_user",
        exports={
            "usd": "/tmp/publish/test_asset_model/v001/test_asset_model.usda",
            "obj": "/tmp/publish/test_asset_model/v001/test_asset_model.obj",
        },
    )


def test_asset_to_dict_returns_serialisable_metadata():
    asset = make_test_asset()

    data = asset.to_dict()

    assert data["name"] == "test_asset_model"
    assert data["asset_type"] == "model"
    assert data["source_scene"] == "/project/scenes/test_asset.ma"
    assert data["version"] == "v001"
    assert data["publish_path"] == "/tmp/publish/test_asset_model/v001"
    assert data["author"] == "pytest_user"
    assert data["exports"]["usd"].endswith(".usda")
    assert "created_at" in data
    assert "package_file_id" not in data
    assert "preview_image" not in data


def test_asset_to_dict_handles_missing_paths():
    asset = Asset(
        name="test_asset_model",
        asset_type="model",
        source_scene=None,
        version="v001",
        publish_path=None,
        author="pytest_user",
    )

    data = asset.to_dict()

    assert data["source_scene"] is None
    assert data["publish_path"] is None


def test_asset_to_mongo_dict_includes_gridfs_and_preview_data():
    asset = make_test_asset()
    asset.package_file_id = "gridfs_file_id_123"
    asset.preview_image = b"fake_preview_bytes"

    data = asset.to_mongo_dict()

    assert data["package_file_id"] == "gridfs_file_id_123"
    assert data["preview_image"] == b"fake_preview_bytes"


def test_write_metadata_creates_parent_directory_and_json_file(tmp_path):
    asset = make_test_asset()
    metadata_path = tmp_path / "nested" / "folder" / "asset_metadata.json"

    write_metadata(asset, metadata_path)

    assert metadata_path.exists()

    data = read_metadata(metadata_path)

    assert data["name"] == "test_asset_model"
    assert data["asset_type"] == "model"
    assert data["version"] == "v001"
    assert data["author"] == "pytest_user"


def test_read_metadata_raises_file_not_found_for_missing_file(tmp_path):
    missing_file = tmp_path / "missing_metadata.json"

    with pytest.raises(FileNotFoundError, match="Metadata file not found"):
        read_metadata(missing_file)
