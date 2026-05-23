from asset_publish_tool.auth.session import (
    clear_current_user,
    get_current_user,
    get_current_user_role,
    set_current_user,
)


def test_set_current_user_stores_session_data():
    clear_current_user()

    set_current_user(
        username="osher",
        role="artist",
    )

    current_user = get_current_user()

    assert current_user["username"] == "osher"
    assert current_user["role"] == "artist"


def test_clear_current_user_removes_session():
    clear_current_user()

    set_current_user(
        username="osher",
        role="artist",
    )

    clear_current_user()
    cleared = get_current_user()

    assert cleared is None


def test_get_current_user_role_returns_role():
    clear_current_user()

    set_current_user(
        username="osher",
        role="artist",
    )
    current_role = get_current_user_role()

    assert current_role == "artist"


def test_get_current_user_returns_none_when_logged_out():
    clear_current_user()

    log_check = get_current_user()

    assert log_check is None
