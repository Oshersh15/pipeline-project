from asset_publish_tool.auth.login import login
from asset_publish_tool.auth.session import clear_current_user, get_current_user
from asset_publish_tool.auth.user_manager import create_user, delete_user_by_username
from asset_publish_tool.database.connection import get_database


def test_login_with_valid_credentials_sets_session():
    db = get_database()

    username = "pytest_login_user"
    password = "test_password_123"
    role = "artist"

    delete_user_by_username(username, db)
    clear_current_user()

    create_user(
        username=username,
        password=password,
        role=role,
        db=db,
    )

    success = login(username, password)

    current_user = get_current_user()

    assert success is True
    assert current_user["username"] == username
    assert current_user["role"] == role

    clear_current_user()
    delete_user_by_username(username, db)
