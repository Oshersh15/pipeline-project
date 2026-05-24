import io
import zipfile
from pathlib import Path

import gridfs
from bson import ObjectId

from asset_publish_tool.database.connection import get_database


def get_assets_collection():
    db = get_database()
    return db["assets"]


def save_asset(asset_data):
    collection = get_assets_collection()
    result = collection.insert_one(asset_data)
    return str(result.inserted_id)


def get_all_assets():
    collection = get_assets_collection()
    return list(collection.find())


def store_file(file_path, filename=None):
    db = get_database()
    fs = gridfs.GridFS(db)

    with open(file_path, "rb") as file:
        file_id = fs.put(file, filename=filename or file_path.name)

    return file_id


def create_publish_package(version_path):
    version_path = Path(version_path)
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as zip_file:
        for file_path in version_path.iterdir():
            if file_path.is_file():
                zip_file.write(file_path, arcname=file_path.name)

    zip_buffer.seek(0)

    return zip_buffer


def store_publish_package(zip_buffer, package_name):
    db = get_database()
    fs = gridfs.GridFS(db)

    file_id = fs.put(
        zip_buffer,
        filename=package_name,
    )

    return file_id


def extract_publish_package(package_file_id, output_dir):
    db = get_database()
    fs = gridfs.GridFS(db)

    grid_file = fs.get(ObjectId(package_file_id))
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    zip_data = grid_file.read()
    zip_buffer = io.BytesIO(zip_data)

    with zipfile.ZipFile(zip_buffer, mode="r") as zip_file:
        zip_file.extractall(output_path)

    return output_path


def retrieve_asset_to_cache(metadata, cache_root):
    asset_type = metadata.get("type", metadata.get("asset_type", "unknown"))
    asset_name = metadata.get("name", metadata.get("asset_name", "unknown_asset"))
    version = metadata.get("version", "unknown_version")
    package_file_id = metadata.get("package_file_id")

    if not package_file_id:
        raise ValueError(f"Asset '{asset_name}' has no package_file_id.")

    cache_path = Path(cache_root) / asset_type / asset_name / version

    extract_publish_package(
        package_file_id,
        cache_path,
    )

    return cache_path


def load_binary_file(file_path):
    with open(file_path, "rb") as file:
        return file.read()


def get_latest_asset_version(asset_name, asset_type):
    collection = get_assets_collection()
    latest_asset = collection.find_one(
        {
            "name": asset_name,
            "asset_type": asset_type,
        },
        sort=[("version", -1)],
    )
    if not latest_asset:
        return "v001"

    latest_version = latest_asset["version"]

    version_number = int(latest_version.replace("v", ""))
    next_version_number = version_number + 1

    return f"v{next_version_number:03d}"


def delete_asset(asset_id, package_file_id=None):
    db = get_database()
    fs = gridfs.GridFS(db)
    collection = db["assets"]

    if package_file_id:
        try:
            fs.delete(ObjectId(package_file_id))
        except Exception as e:
            print(f"Failed to delete GridFS package: {e}")

    result = collection.delete_one({"_id": ObjectId(asset_id)})

    return result.deleted_count > 0
