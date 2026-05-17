from pymongo.errors import OperationFailure

from asset_publish_tool.auth.session import set_current_user
from asset_publish_tool.auth.user_manager import get_user_role
from asset_publish_tool.database.connection import get_database


def login(username: str, password: str) -> bool:
    if not username or not password:
        return False

    try:
        db = get_database(username=username, password=password)

        # Force MongoDB to actually test the credentials now.
        db.command("ping")

    except OperationFailure as e:
        print(f"Login failed: {e}")
        return False

    except Exception as e:
        print(f"Login error: {e}")
        return False

    role = get_user_role(username, db)

    if not role:
        print(f"Login failed: no app role found for user '{username}'")
        return False

    set_current_user(username, role)
    return True
