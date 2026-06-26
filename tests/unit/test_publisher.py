import importlib
import sys
import types

import pytest


def install_fake_maya(monkeypatch):
    fake_cmds = types.SimpleNamespace()
    fake_maya = types.SimpleNamespace(cmds=fake_cmds)

    monkeypatch.setitem(sys.modules, "maya", fake_maya)
    monkeypatch.setitem(sys.modules, "maya.cmds", fake_cmds)

    return fake_cmds


def import_publisher_with_fake_maya(monkeypatch):
    install_fake_maya(monkeypatch)
    install_fake_usd_utils(monkeypatch)

    import asset_publish_tool.maya.publisher as publisher

    return importlib.reload(publisher)


def install_fake_usd_utils(monkeypatch):
    fake_usd_utils = types.SimpleNamespace(
        process_exported_usd=lambda *args, **kwargs: {
            "success": True,
            "errors": [],
            "warnings": [],
        }
    )

    monkeypatch.setitem(
        sys.modules,
        "asset_publish_tool.usd.usd_utils",
        fake_usd_utils,
    )


def test_publish_selected_objects_raises_when_no_user_session(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "get_current_user_role",
        lambda: None,
    )

    with pytest.raises(PermissionError, match="No authenticated user session"):
        publisher.publish_selected_objects()


def test_publish_selected_objects_raises_when_user_lacks_permission(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "get_current_user_role",
        lambda: "viewer",
    )

    monkeypatch.setattr(
        publisher,
        "has_permission",
        lambda role, permission: False,
    )

    with pytest.raises(
        PermissionError, match="does not have permission to publish assets"
    ):
        publisher.publish_selected_objects()
