from getpass import getpass

from asset_publish_tool.auth.user_manager import create_user
from asset_publish_tool.database.connection import get_database


def create_initial_admin():
    db = get_database()

    username = input("Admin username: ").strip()
    password = getpass("Admin password: ")

    created = create_user(
        username=username,
        password=password,
        role="app_admin",
        db=db,
    )

    if created:
        print(f"Admin user '{username}' created successfully.")
    else:
        print(f"User '{username}' already exists.")


if __name__ == "__main__":
    create_initial_admin()
