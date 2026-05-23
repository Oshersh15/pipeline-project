from asset_publish_tool.auth.roles import has_permission


def test_viewer_cannot_publish():

    assert has_permission("viewer", "publish_assets") is False


def test_artist_can_publish():

    assert has_permission("artist", "publish_assets") is True


def test_admin_can_manage_users():

    assert has_permission("app_admin", "manage_users") is True
