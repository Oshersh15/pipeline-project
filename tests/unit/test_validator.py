from asset_publish_tool.core.validator import validate_scene_object


def test_valid_model_name_passes():
    rules = {
        "scene_object_rules": {
            "model": {
                "name_pattern": ".*_model$",
                "export_to_usd": True,
                "required_checks": [
                    "lowercase_name",
                    "no_spaces",
                    "valid_characters",
                ],
            }
        }
    }

    result = validate_scene_object(
        object_name="chair_model",
        rules=rules,
        maya_object_type="model",
    )

    assert result["valid"] is True
    assert result["type"] == "model"
    assert result["export_to_usd"] is True
    assert result["errors"] == []


def test_uppercase_model_name_fails():
    rules = {
        "scene_object_rules": {
            "model": {
                "name_pattern": ".*_model$",
                "export_to_usd": True,
                "required_checks": [
                    "lowercase_name",
                    "no_spaces",
                    "valid_characters",
                ],
            }
        }
    }

    result = validate_scene_object(
        object_name="Chair_model",
        rules=rules,
        maya_object_type="model",
    )

    assert result["valid"] is False
    assert result["type"] == "model"
    assert result["export_to_usd"] is True
    assert "Name must be lowercase." in result["errors"]


def test_uppercase_allowed_when_rule_disabled():
    rules = {
        "scene_object_rules": {
            "model": {
                "name_pattern": ".*_model$",
                "export_to_usd": True,
                "required_checks": [
                    "no_spaces",
                    "valid_characters",
                ],
            }
        }
    }

    result = validate_scene_object(
        object_name="Chair_model",
        rules=rules,
        maya_object_type="model",
    )

    assert result["valid"] is True
    assert result["type"] == "model"
    assert result["export_to_usd"] is True
    assert result["errors"] == []


def test_model_name_with_wrong_suffix_fails():
    rules = {
        "scene_object_rules": {
            "model": {
                "name_pattern": ".*_model$",
                "export_to_usd": True,
                "required_checks": [
                    "lowercase_name",
                    "no_spaces",
                    "valid_characters",
                ],
            }
        }
    }

    result = validate_scene_object(
        object_name="chair_geo",
        rules=rules,
        maya_object_type="model",
    )

    assert result["valid"] is False
    assert "Object name does not match any known type pattern." in result["errors"]


def test_name_type_mismatch_fails():
    rules = {
        "scene_object_rules": {
            "model": {
                "name_pattern": ".*_model$",
                "export_to_usd": True,
                "required_checks": [
                    "lowercase_name",
                    "no_spaces",
                    "valid_characters",
                ],
            },
            "camera": {
                "name_pattern": ".*_camera$",
                "export_to_usd": True,
                "required_checks": [
                    "lowercase_name",
                    "no_spaces",
                    "valid_characters",
                ],
            },
        }
    }

    result = validate_scene_object(
        object_name="chair_camera",
        rules=rules,
        maya_object_type="model",
    )

    assert result["valid"] is False
    assert (
        "Name suggests 'camera', but Maya object type is 'model'." in result["errors"]
    )
