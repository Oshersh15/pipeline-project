from asset_publish_tool.database.asset_repository import (
    create_publish_package,
    retrieve_asset_to_cache,
    store_publish_package,
)


def test_retrieve_asset_to_cache_extracts_package(tmp_path):
    publish_folder = tmp_path / "publish"
    publish_folder.mkdir()

    usd_file = publish_folder / "test_asset.usda"
    usd_file.write_text("#usda 1.0")

    metadata_file = publish_folder / "metadata.json"
    metadata_file.write_text('{"name": "test_asset"}')

    package = create_publish_package(publish_folder)

    package_file_id = store_publish_package(
        package,
        "test_asset_v001.zip",
    )

    metadata = {
        "name": "test_asset",
        "type": "model",
        "version": "v001",
        "package_file_id": str(package_file_id),
    }

    cache_root = tmp_path / "asset_cache"

    cache_path = retrieve_asset_to_cache(
        metadata,
        cache_root,
    )

    assert cache_path.exists()
    assert (cache_path / "test_asset.usda").exists()
    assert (cache_path / "metadata.json").exists()
