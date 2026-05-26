"""
User management utilities for authentication and role assignment.

This module handles MongoDB-backed user creation, role retrieval,
role updates, and account management for the publishing system.
"""

from pymongo.database import Database
from pymongo.errors import OperationFailure

from asset_publish_tool.auth.roles import (
    APP_ADMIN,
    ARTIST,
    VIEWER,
)

# ----------------------------------------------------------------------
# User collection helpers
# ----------------------------------------------------------------------


def get_users_collection(db: Database):
    """
    Return the MongoDB collection used for application user management.

    Args:
        db (Database): MongoDB database instance.

    Returns:
        Collection: MongoDB users collection.
    """
    collection = db["users"]

    collection.create_index(
        "username",
        unique=True,
    )

    return collection


def admin_exists(db):
    """
    Check whether an application admin user already exists.

    Args:
        db (Database): MongoDB database instance.

    Returns:
        bool: True if an admin user exists, otherwise False.
    """
    users_collection = db["users"]

    admin = users_collection.find_one({"role": "app_admin"})

    return admin is not None


# ----------------------------------------------------------------------
# User creation
# ----------------------------------------------------------------------


def create_user(
    username: str,
    password: str,
    role: str,
    db: Database,
) -> bool:
    """
    Create a new application user and matching MongoDB database user.

    Application roles are mapped to MongoDB permissions:
    - Viewer -> read
    - Artist -> readWrite
    - App Admin -> readWrite

    Args:
        username (str): Username for the new user.
        password (str): Password for the MongoDB user.
        role (str): Application role name.
        db (Database): MongoDB database instance.

    Returns:
        bool: True if the user was created successfully, otherwise False.

    Raises:
        ValueError: If username or password is missing.
    """
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
            roles=[
                {
                    "role": mongo_role,
                    "db": db.name,
                }
            ],
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


# ----------------------------------------------------------------------
# User queries
# ----------------------------------------------------------------------


def get_user_role(username: str, db: Database):
    """
    Retrieve the application role assigned to a user.

    Args:
        username (str): Username to query.
        db (Database): MongoDB database instance.

    Returns:
        str | None: User role, or None if the user does not exist.
    """
    collection = get_users_collection(db)

    user = collection.find_one({"username": username})

    if not user:
        return None

    return user.get("role")


def get_all_users(db):
    """
    Retrieve all registered application users.

    Args:
        db (Database): MongoDB database instance.

    Returns:
        list: Sorted list of user documents.
    """
    collection = get_users_collection(db)

    return list(
        collection.find(
            {},
            {
                "username": 1,
                "role": 1,
            },
        ).sort("username", 1)
    )


# ----------------------------------------------------------------------
# User management
# ----------------------------------------------------------------------


def update_user_role(username, new_role, db):
    """
    Update the application role assigned to a user.

    Args:
        username (str): Username to update.
        new_role (str): New application role.
        db (Database): MongoDB database instance.

    Returns:
        bool: True if the role was updated successfully.
    """
    collection = get_users_collection(db)

    result = collection.update_one(
        {"username": username},
        {"$set": {"role": new_role}},
    )

    return result.modified_count > 0


def delete_user_by_username(username, db):
    """
    Delete an application user and matching MongoDB database user.

    Args:
        username (str): Username to delete.
        db (Database): MongoDB database instance.

    Returns:
        bool: True if the application user document was deleted.
    """
    collection = get_users_collection(db)

    try:
        db.command("dropUser", username)

    except Exception:
        pass

    result = collection.delete_one({"username": username})

    return result.deleted_count > 0
