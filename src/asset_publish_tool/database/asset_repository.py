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
