"""
Session state utilities for authenticated users.

This module stores and manages the currently authenticated user
for the active Maya session.
"""

CURRENT_USER = None


def set_current_user(username: str, role: str):
    """
    Store the currently authenticated user session.

    Args:
        username (str): Authenticated username.
        role (str): Role assigned to the authenticated user.
    """
    global CURRENT_USER

    CURRENT_USER = {
        "username": username,
        "role": role,
    }


def clear_current_user():
    """
    Clear the current authenticated user session.
    """
    global CURRENT_USER
    CURRENT_USER = None


def get_current_user():
    """
    Return the currently authenticated user session.

    Returns:
        dict | None: Current user session dictionary, or None if
        no user is authenticated.
    """
    return CURRENT_USER


def get_current_user_role():
    """
    Return the role of the currently authenticated user.

    Returns:
        str | None: Current user role, or None if no active
        session exists.
    """
    if not CURRENT_USER:
        return None

    return CURRENT_USER.get("role")
