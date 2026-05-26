"""
Utility script for creating the initial application administrator.

This script creates the first authenticated admin user for the
asset publishing system using MongoDB-backed credentials.
"""

from getpass import getpass

from asset_publish_tool.auth.user_manager import create_user
from asset_publish_tool.database.connection import get_database


def create_initial_admin():
    """
    Prompt for administrator credentials and create the initial
    application admin account.

    The created user receives the `app_admin` role, which grants
    full access to publishing, validation, asset viewing, and
    user management functionality.
    """
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
