from pymongo.errors import OperationFailure

from asset_publish_tool.auth import login as login_module


class FakeDatabase:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def command(self, command_name):
        if self.should_fail:
            raise OperationFailure("Invalid credentials")

        return {"ok": 1}


def test_login_returns_false_when_username_missing():
    result = login_module.login("", "password123")

    assert result is False


def test_login_returns_false_when_password_missing():
    result = login_module.login("test_user", "")

    assert result is False


def test_login_returns_false_when_mongodb_authentication_fails(monkeypatch):
    def fake_get_database(username=None, password=None):
        return FakeDatabase(should_fail=True)

    monkeypatch.setattr(login_module, "get_database", fake_get_database)

    result = login_module.login("test_user", "wrong_password")

    assert result is False


def test_login_returns_false_when_user_has_no_role(monkeypatch):
    def fake_get_database(username=None, password=None):
        return FakeDatabase()

    monkeypatch.setattr(login_module, "get_database", fake_get_database)
    monkeypatch.setattr(login_module, "get_user_role", lambda username, db: None)

    result = login_module.login("test_user", "password123")

    assert result is False


def test_login_sets_session_when_credentials_and_role_are_valid(monkeypatch):
    captured_user = {}

    def fake_get_database(username=None, password=None):
        return FakeDatabase()

    def fake_set_current_user(username, role):
        captured_user["username"] = username
        captured_user["role"] = role

    monkeypatch.setattr(login_module, "get_database", fake_get_database)
    monkeypatch.setattr(login_module, "get_user_role", lambda username, db: "artist")
    monkeypatch.setattr(login_module, "set_current_user", fake_set_current_user)

    result = login_module.login("test_user", "password123")

    assert result is True
    assert captured_user["username"] == "test_user"
    assert captured_user["role"] == "artist"
