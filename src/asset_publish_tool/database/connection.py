from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "asset_publish_tool_db"


def get_client():
    client = MongoClient(MONGO_URI)
    return client


def get_database():
    client = get_client()
    db = client[DATABASE_NAME]
    return db


if __name__ == "__main__":
    database = get_database()
    print(database.name)
