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


def test_publish_animation_cache_raises_when_no_user_session(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "get_current_user",
        lambda: None,
    )

    with pytest.raises(RuntimeError, match="No user is currently logged in"):
        publisher.publish_animation_cache(
            shot_number=10,
            asset_name="heroCharacter",
        )


def test_publish_animation_cache_raises_when_user_lacks_permission(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "get_current_user",
        lambda: {"username": "test_viewer", "role": "viewer"},
    )

    with pytest.raises(
        PermissionError,
        match="does not have permission to publish assets",
    ):
        publisher.publish_animation_cache(
            shot_number=10,
            asset_name="heroCharacter",
        )


@pytest.mark.parametrize("asset_name", ["", "   ", None])
def test_publish_animation_cache_requires_asset_name(monkeypatch, asset_name):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "get_current_user",
        lambda: {"username": "test_artist", "role": "artist"},
    )

    with pytest.raises(ValueError, match="Asset name is required"):
        publisher.publish_animation_cache(
            shot_number=10,
            asset_name=asset_name,
        )


def test_publish_animation_cache_rejects_unsafe_asset_name(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "get_current_user",
        lambda: {"username": "test_artist", "role": "artist"},
    )

    with pytest.raises(ValueError, match="letters, numbers, and underscores"):
        publisher.publish_animation_cache(
            shot_number=10,
            asset_name="../heroCharacter",
        )


def test_publish_animation_cache_rejects_unsafe_department(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "get_current_user",
        lambda: {"username": "test_artist", "role": "artist"},
    )

    with pytest.raises(ValueError, match="Department must start with a letter"):
        publisher.publish_animation_cache(
            shot_number=10,
            asset_name="heroCharacter",
            department="../animation",
        )


def test_publish_animation_cache_raises_when_nothing_selected(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "get_current_user",
        lambda: {"username": "test_artist", "role": "artist"},
    )
    publisher.cmds.ls = lambda selection: []

    with pytest.raises(RuntimeError, match="No objects selected"):
        publisher.publish_animation_cache(
            shot_number=10,
            asset_name="heroCharacter",
        )


def test_resolve_animation_frame_range_uses_maya_playback_range(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)
    publisher.cmds.playbackOptions = (
        lambda query, min=False, max=False: 1001 if min else 1050
    )

    result = publisher._resolve_animation_frame_range()

    assert result == (1001, 1050)


def test_resolve_animation_frame_range_uses_custom_range(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)
    publisher.cmds.playbackOptions = lambda **kwargs: pytest.fail(
        "Maya playback range should not be queried for a custom range."
    )

    result = publisher._resolve_animation_frame_range(-10, 20)

    assert result == (-10, 20)


@pytest.mark.parametrize(
    ("frame_start", "frame_end"),
    [
        (1, None),
        (None, 10),
    ],
)
def test_resolve_animation_frame_range_rejects_incomplete_custom_range(
    monkeypatch, frame_start, frame_end
):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    with pytest.raises(ValueError, match="must be provided together"):
        publisher._resolve_animation_frame_range(frame_start, frame_end)


def test_resolve_animation_frame_range_rejects_reversed_range(monkeypatch):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    with pytest.raises(ValueError, match="greater than or equal"):
        publisher._resolve_animation_frame_range(20, 10)


def test_publish_animation_cache_exports_and_saves_publish(monkeypatch, tmp_path):
    publisher = import_publisher_with_fake_maya(monkeypatch)
    captured = {}

    monkeypatch.setattr(
        publisher,
        "__file__",
        str(tmp_path / "src" / "asset_publish_tool" / "maya" / "publisher.py"),
    )
    monkeypatch.setattr(
        publisher,
        "get_current_user",
        lambda: {"username": "test_artist", "role": "artist"},
    )
    monkeypatch.setattr(
        publisher,
        "get_next_shot_asset_version",
        lambda asset_name, asset_type, shot_name, department: "v003",
    )

    publisher.cmds.ls = lambda selection: [
        "hero_body_root",
        "hero_accessory_root",
    ]
    publisher.cmds.playbackOptions = (
        lambda query, min=False, max=False: 1 if min else 10
    )
    publisher.cmds.pluginInfo = lambda plugin, query, loaded: False
    publisher.cmds.loadPlugin = lambda plugin: captured.update(loaded_plugin=plugin)
    publisher.cmds.file = lambda query, sceneName: "/project/scenes/shot010.ma"

    expected_version_path = (
        tmp_path
        / "tmp_publish_cache"
        / "shots"
        / "shot010"
        / "animation"
        / "heroCharacter"
        / "v003"
    )
    expected_alembic_file = (
        expected_version_path / "shot010_heroCharacter_anim.abc"
    )

    def fake_alembic_export(j):
        captured["alembic_job"] = j
        expected_alembic_file.write_bytes(b"fake alembic")

    publisher.cmds.AbcExport = fake_alembic_export

    def fake_write_metadata(asset, metadata_path):
        captured["asset"] = asset
        captured["metadata_path"] = metadata_path
        metadata_path.write_text("{}")

    monkeypatch.setattr(publisher, "write_metadata", fake_write_metadata)
    monkeypatch.setattr(
        publisher,
        "create_publish_package",
        lambda version_path: captured.update(package_path=version_path) or "package",
    )
    monkeypatch.setattr(
        publisher,
        "store_publish_package",
        lambda package, package_name: "package-id",
    )

    def fake_save_asset(asset_data):
        captured["mongo_data"] = asset_data
        return "mongo-id"

    monkeypatch.setattr(publisher, "save_asset", fake_save_asset)

    result = publisher.publish_animation_cache(
        shot_number=10,
        asset_name="heroCharacter",
    )

    assert captured["loaded_plugin"] == "AbcExport"
    assert captured["alembic_job"] == (
        f'-frameRange 1 10 -dataFormat ogawa -root hero_body_root '
        f'-root hero_accessory_root '
        f'-file "{expected_alembic_file}"'
    )
    assert captured["metadata_path"] == expected_version_path / "metadata.json"
    assert captured["package_path"] == expected_version_path

    expected_metadata = {
        "name": "heroCharacter",
        "asset_type": "shot_animation",
        "source_scene": "/project/scenes/shot010.ma",
        "version": "v003",
        "publish_path": str(expected_version_path),
        "author": "test_artist",
        "department": "animation",
        "shot_name": "shot010",
        "publish_format": "alembic",
        "source_dcc": "maya",
        "target_dcc": "houdini",
        "frame_start": 1,
        "frame_end": 10,
        "scale_to_target": 0.01,
        "exports": {"alembic": str(expected_alembic_file)},
        "package_file_id": "package-id",
    }

    for key, expected_value in expected_metadata.items():
        assert captured["mongo_data"][key] == expected_value

    assert result == {
        "name": "heroCharacter",
        "shot_name": "shot010",
        "department": "animation",
        "version": "v003",
        "frame_start": 1,
        "frame_end": 10,
        "alembic_file": str(expected_alembic_file),
        "package_file_id": "package-id",
        "mongo_id": "mongo-id",
    }


def test_publish_animation_cache_raises_when_alembic_file_is_missing(
    monkeypatch, tmp_path
):
    publisher = import_publisher_with_fake_maya(monkeypatch)

    monkeypatch.setattr(
        publisher,
        "__file__",
        str(tmp_path / "src" / "asset_publish_tool" / "maya" / "publisher.py"),
    )
    monkeypatch.setattr(
        publisher,
        "get_current_user",
        lambda: {"username": "test_artist", "role": "artist"},
    )
    monkeypatch.setattr(
        publisher,
        "get_next_shot_asset_version",
        lambda asset_name, asset_type, shot_name, department: "v001",
    )

    publisher.cmds.ls = lambda selection: ["hero_root"]
    publisher.cmds.playbackOptions = (
        lambda query, min=False, max=False: 1 if min else 10
    )
    publisher.cmds.pluginInfo = lambda plugin, query, loaded: True
    publisher.cmds.AbcExport = lambda j: None

    monkeypatch.setattr(
        publisher,
        "write_metadata",
        lambda asset, metadata_path: pytest.fail(
            "Metadata should not be written after a failed Alembic export."
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="Alembic export did not create the expected file",
    ):
        publisher.publish_animation_cache(
            shot_number=10,
            asset_name="heroCharacter",
        )
