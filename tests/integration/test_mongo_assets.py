from pathlib import Path

from asset_publish_tool.database.asset_repository import (
    create_publish_package,
    delete_asset,
    extract_publish_package,
    get_all_assets,
    save_asset,
    store_publish_package,
)


def test_save_asset_metadata_can_be_retrieved():
    asset_data = {
        "name": "pytest_asset_model",
        "type": "model",
        "version": "v001",
        "author": "pytest",
        "created_at": "2026-01-01T10:00:00",
        "package_file_id": None,
    }

    asset_id = save_asset(asset_data)

    assets = get_all_assets()

    matching_assets = [asset for asset in assets if str(asset["_id"]) == asset_id]

    assert len(matching_assets) == 1
    assert matching_assets[0]["name"] == "pytest_asset_model"
    assert matching_assets[0]["version"] == "v001"

    delete_asset(asset_id)


def test_publish_package_can_be_stored_and_extracted(tmp_path):
    version_path = tmp_path / "version"
    version_path.mkdir()

    test_file = version_path / "metadata.json"
    test_file.write_text('{"name": "pytest_asset_model"}')

    package = create_publish_package(version_path)

    package_file_id = store_publish_package(
        package,
        "pytest_asset_model_v001.zip",
    )

    extract_dir = tmp_path / "extracted"

    extract_publish_package(
        package_file_id,
        extract_dir,
    )

    extracted_file = extract_dir / "metadata.json"

    assert extracted_file.exists()
    assert extracted_file.read_text() == '{"name": "pytest_asset_model"}'


def test_delete_asset_removes_metadata():
    asset_data = {
        "name": "pytest_delete_asset_model",
        "type": "model",
        "version": "v001",
        "author": "pytest",
        "created_at": "2026-01-01T10:00:00",
        "package_file_id": None,
    }

    asset_id = save_asset(asset_data)

    deleted = delete_asset(asset_id)

    assets = get_all_assets()

    matching_assets = [asset for asset in assets if str(asset["_id"]) == asset_id]

    assert deleted is True
    assert matching_assets == []
