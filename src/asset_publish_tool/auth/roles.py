APP_ADMIN = "app_admin"
ARTIST = "artist"
VIEWER = "viewer"


ROLE_PERMISSIONS = {
    APP_ADMIN: {
        "view_assets",
        "validate_assets",
        "publish_assets",
        "manage_users",
    },
    ARTIST: {
        "view_assets",
        "validate_assets",
        "publish_assets",
    },
    VIEWER: {
        "view_assets",
    },
}


def has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
