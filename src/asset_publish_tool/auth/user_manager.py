from pymongo.database import Database
from pymongo.errors import OperationFailure

from asset_publish_tool.auth.roles import (
    APP_ADMIN,
    ARTIST,
    VIEWER,
)


def get_users_collection(db: Database):
    collection = db["users"]
    collection.create_index("username", unique=True)
    return collection


def create_user(
    username: str,
    password: str,
    role: str,
    db: Database,
) -> bool:
    if not username or not password:
        raise ValueError("username and password are required")

    collection = get_users_collection(db)

    existing_user = collection.find_one({"username": username})

    if existing_user:
        return False

    mongo_role = "read"

    if role in [APP_ADMIN, ARTIST]:
        mongo_role = "readWrite"

    try:
        db.command(
            "createUser",
            username,
            pwd=password,
            roles=[{"role": mongo_role, "db": db.name}],
        )

    except OperationFailure as e:
        print(f"Failed to create MongoDB user: {e}")
        return False

    collection.insert_one(
        {
            "username": username,
            "role": role,
        }
    )

    return True


def get_user_role(username: str, db: Database):
    collection = get_users_collection(db)

    user = collection.find_one({"username": username})

    if not user:
        return None

    return user.get("role")
