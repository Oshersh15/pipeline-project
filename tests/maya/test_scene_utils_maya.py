import maya.standalone

maya.standalone.initialize(name="python")

import maya.cmds as cmds

import asset_publish_tool.maya.scene_utils as scene_utils


def test_detect_mesh_transform_as_model():
    cmds.file(new=True, force=True)

    cube, _ = cmds.polyCube(name="test_cube_model")

    detected_type = scene_utils.detect_maya_object_type(cube)

    assert detected_type == "model"


def test_fix_object_name_renames_uppercase_model(monkeypatch):
    cmds.file(new=True, force=True)

    test_rules = {
        "scene_object_rules": {
            "model": {
                "name_pattern": ".*_model$",
                "required_checks": [
                    "lowercase_name",
                    "no_spaces",
                    "valid_characters",
                ],
            }
        }
    }

    monkeypatch.setattr(
        scene_utils,
        "get_validation_rules",
        lambda: test_rules,
    )

    cube, _ = cmds.polyCube(name="TestCube_model")

    new_name, reason = scene_utils.fix_object_name(cube)

    assert new_name == "test_cube_model"
    assert cmds.objExists("test_cube_model")


def test_make_unique_name_prevents_collision(monkeypatch):
    cmds.file(new=True, force=True)

    test_rules = {
        "scene_object_rules": {
            "model": {
                "name_pattern": ".*_model$",
                "required_checks": [
                    "lowercase_name",
                    "no_spaces",
                    "valid_characters",
                ],
            }
        }
    }

    monkeypatch.setattr(
        scene_utils,
        "get_validation_rules",
        lambda: test_rules,
    )

    cube, _ = cmds.polyCube(name="test_cube_model")
    cube_to_rename, _ = cmds.polyCube(name="TestCube_model")
    new_name, reason = scene_utils.fix_object_name(cube_to_rename)

    assert new_name == "test_cube_2_model"


def test_has_frozen_transforms_returns_true_for_clean_object():
    cmds.file(new=True, force=True)

    cube, _ = cmds.polyCube(name="test_cube_model")

    assert scene_utils.has_frozen_transforms(cube) is True


def test_has_frozen_transforms_returns_false_for_translated_object():
    cmds.file(new=True, force=True)

    cube, _ = cmds.polyCube(name="test_cube_model")
    cmds.setAttr(f"{cube}.translateX", 5)

    assert scene_utils.has_frozen_transforms(cube) is False
