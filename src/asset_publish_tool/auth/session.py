CURRENT_USER = None


def set_current_user(username: str, role: str):
    global CURRENT_USER

    CURRENT_USER = {
        "username": username,
        "role": role,
    }


def clear_current_user():
    global CURRENT_USER
    CURRENT_USER = None


def get_current_user():
    return CURRENT_USER


def get_current_user_role():
    if not CURRENT_USER:
        return None

    return CURRENT_USER.get("role")
