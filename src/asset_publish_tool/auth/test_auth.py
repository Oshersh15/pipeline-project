from asset_publish_tool.auth.user_manager import create_user
from asset_publish_tool.database.connection import get_database


def run_auth_test():
    db = get_database()

    users = [
        ("admin_test", "admin123", "app_admin"),
        ("artist_test", "artist123", "artist"),
        ("viewer_test", "viewer123", "viewer"),
    ]

    for username, password, role in users:
        created = create_user(
            username=username,
            password=password,
            role=role,
            db=db,
        )

        print(f"{username} created: {created}")


if __name__ == "__main__":
    run_auth_test()
