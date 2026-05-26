"""
Role definitions and permission utilities for the asset publishing tool.

Roles control access to validation, publishing, asset viewing,
and administrative functionality.
"""

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
    """
    Check whether a role has a specific permission.

    Args:
        role (str): Role name to evaluate.
        permission (str): Permission identifier to check.

    Returns:
        bool: True if the role contains the requested permission,
        otherwise False.
    """
    return permission in ROLE_PERMISSIONS.get(role, set())
