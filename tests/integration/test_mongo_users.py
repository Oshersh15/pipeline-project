from asset_publish_tool.auth.user_manager import (
    create_user,
    delete_user_by_username,
    get_user_role,
    get_users_collection,
    update_user_role,
)
from asset_publish_tool.database.connection import get_database


def test_database_connection_returns_database():
    db = get_database()

    assert db is not None
    assert isinstance(db.name, str)


def test_create_user_returns_true():
    db = get_database()

    username = "pytest_create_user"
    password = "test_password_123"
    role = "viewer"

    delete_user_by_username(username, db)

    created = create_user(
        username=username,
        password=password,
        role=role,
        db=db,
    )

    assert created is True

    delete_user_by_username(username, db)


def test_update_user_role():
    db = get_database()

    username = "pytest_create_user"
    password = "test_password_123"
    role = "viewer"

    delete_user_by_username(username, db)

    create_user(
        username=username,
        password=password,
        role=role,
        db=db,
    )

    new_role = "artist"

    updated = update_user_role(username, new_role, db)
    updated_role = get_user_role(username, db)

    assert updated is True
    assert updated_role == "artist"

    delete_user_by_username(username, db)


def test_delete_user():
    db = get_database()
    collection = get_users_collection(db)

    username = "pytest_create_user"
    password = "test_password_123"
    role = "viewer"

    delete_user_by_username(username, db)

    create_user(
        username=username,
        password=password,
        role=role,
        db=db,
    )

    deleted = delete_user_by_username(username, db)
    user = collection.find_one({"username": username})

    assert deleted is True
    assert user is None
