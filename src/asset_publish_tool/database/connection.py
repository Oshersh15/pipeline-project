from typing import Optional

from pymongo import MongoClient

HOST = "localhost"
PORT = 27017
DATABASE_NAME = "asset_publish_tool_db"


def build_mongo_uri(
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    if username and password:
        return f"mongodb://{username}:{password}@{HOST}:{PORT}/{DATABASE_NAME}"

    return f"mongodb://{HOST}:{PORT}/"


def get_client(
    username: Optional[str] = None,
    password: Optional[str] = None,
):
    uri = build_mongo_uri(username, password)
    client = MongoClient(uri)
    return client


def get_database(
    username: Optional[str] = None,
    password: Optional[str] = None,
):
    client = get_client(username, password)
    db = client[DATABASE_NAME]
    return db


def test_connection(
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> bool:
    try:
        client = get_client(username, password)
        client.admin.command("ping")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False


if __name__ == "__main__":
    database = get_database()
    print(database.name)
