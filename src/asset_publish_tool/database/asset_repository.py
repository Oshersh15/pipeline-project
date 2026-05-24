import io
import zipfile
from pathlib import Path

import gridfs
from bson import ObjectId

from asset_publish_tool.database.connection import get_database


def get_assets_collection():
    """
    Return the MongoDB collection used to store published asset metadata.

    Returns:
        Collection: MongoDB collection containing asset metadata documents.
    """
    db = get_database()
    return db["assets"]


def save_asset(asset_data):
    """
    Save a published asset metadata document to MongoDB.

    Args:
        asset_data (dict): Metadata describing the published asset, including
            name, asset type, version, author, export paths, and package ID.

    Returns:
        str: MongoDB document ID for the saved asset metadata.
    """
    collection = get_assets_collection()
    result = collection.insert_one(asset_data)
    return str(result.inserted_id)


def get_all_assets():
    """
    Retrieve all published asset metadata documents from MongoDB.

    Returns:
        list: List of MongoDB asset metadata documents.
    """
    collection = get_assets_collection()
    return list(collection.find())


def delete_asset(asset_id, package_file_id=None):
    """
    Delete a published asset from MongoDB and optionally remove its GridFS package.

    Args:
        asset_id (str): MongoDB document ID for the asset metadata.
        package_file_id (str, optional): GridFS file ID for the stored asset package.

    Returns:
        bool: True if the asset metadata document was deleted, otherwise False.
    """
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


def create_publish_package(version_path):
    """
    Create an in-memory zip package from a published asset version folder.

    Args:
        version_path (str | Path): Folder containing exported files and metadata
            for one published asset version.

    Returns:
        io.BytesIO: In-memory zip archive ready to be stored in GridFS.
    """
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
    """
    Store a published asset package in MongoDB GridFS.

    Args:
        zip_buffer (io.BytesIO): In-memory zip package created from the publish folder.
        package_name (str): Filename to assign to the stored GridFS package.

    Returns:
        ObjectId: GridFS file ID for the stored package.
    """
    db = get_database()
    fs = gridfs.GridFS(db)

    file_id = fs.put(
        zip_buffer,
        filename=package_name,
    )

    return file_id


def extract_publish_package(package_file_id, output_dir):
    """
    Extract a stored GridFS asset package into a local folder.

    Args:
        package_file_id (str): GridFS file ID for the stored package.
        output_dir (str | Path): Local folder where the package should be extracted.

    Returns:
        Path: Path to the extracted package folder.
    """
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
    """
    Retrieve a published asset package from GridFS and extract it into the local cache.

    The cache path is built using the asset type, asset name, and version so that
    retrieved packages are organised consistently for use by Maya, Houdini, or
    other DCC applications.

    Args:
        metadata (dict): MongoDB asset document containing name, type, version,
            and package_file_id.
        cache_root (str | Path): Root folder for the local asset cache.

    Returns:
        Path: Folder containing the extracted asset package.

    Raises:
        ValueError: If the asset metadata does not contain a package_file_id.
    """
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


def store_file(file_path, filename=None):
    """
    Store an individual file in MongoDB GridFS.

    Args:
        file_path (str | Path): Local file path to store.
        filename (str, optional): Filename to use in GridFS. If omitted, the
            source filename is used.

    Returns:
        ObjectId: GridFS file ID for the stored file.
    """
    file_path = Path(file_path)

    db = get_database()
    fs = gridfs.GridFS(db)

    with open(file_path, "rb") as file:
        file_id = fs.put(file, filename=filename or file_path.name)

    return file_id


def load_binary_file(file_path):
    """
    Read a local file as binary data.

    Args:
        file_path (str | Path): Path to the file.

    Returns:
        bytes: Binary contents of the file.
    """
    with open(file_path, "rb") as file:
        return file.read()


def get_next_asset_version(asset_name, asset_type):
    """
    Calculate the next available publish version for an asset.

    Args:
        asset_name (str): Name of the asset.
        asset_type (str): Type/category of the asset.

    Returns:
        str: Next version string, or v001 if no matching asset is found.
    """
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
