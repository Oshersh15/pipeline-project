import json
import re
from pathlib import Path

AVAILABLE_VALIDATION_CHECKS = [
    "lowercase_name",
    "no_spaces",
    "valid_characters",
]


class ValidationError(Exception):
    pass


def load_validation_rules(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Validation config not found: {config_path}")

    with open(config_path, "r") as file:
        return json.load(file)


def identify_object_type(object_name: str, rules: dict):
    object_rules = rules["scene_object_rules"]

    for object_type, rule_data in object_rules.items():
        pattern = rule_data["name_pattern"]

        if re.match(pattern, object_name):
            return object_type

    return None


def validate_name_checks(object_name: str, required_checks: list[str]) -> list[str]:
    errors = []

    if not object_name:
        errors.append("Name cannot be empty.")
        return errors

    if "no_spaces" in required_checks and " " in object_name:
        errors.append("Name must not contain spaces.")

    if "lowercase_name" in required_checks and object_name != object_name.lower():
        errors.append("Name must be lowercase.")

    if "valid_characters" in required_checks:
        if not re.match(r"^[A-Za-z0-9_]+$", object_name):
            errors.append("Name can only contain letters, numbers, and underscores.")

    return errors


def validate_scene_object(object_name: str, rules: dict, maya_object_type=None) -> dict:
    errors = []

    name_object_type = identify_object_type(object_name, rules)

    if name_object_type is None:
        errors.append("Object name does not match any known type pattern.")

    if maya_object_type and maya_object_type != "unknown":
        object_type = maya_object_type

        if name_object_type and name_object_type != maya_object_type:
            errors.append(
                f"Name suggests '{name_object_type}', but Maya object type is '{maya_object_type}'."
            )
    else:
        object_type = name_object_type or "unknown"

    if object_type == "unknown":
        return {
            "name": object_name,
            "type": "unknown",
            "valid": False,
            "export_to_usd": False,
            "errors": errors,
        }

    object_rule = rules["scene_object_rules"].get(object_type, {})
    required_checks = object_rule.get("required_checks", [])

    name_errors = validate_name_checks(object_name, required_checks)
    errors.extend(name_errors)

    return {
        "name": object_name,
        "type": object_type,
        "valid": len(errors) == 0,
        "export_to_usd": object_rule.get("export_to_usd", False),
        "errors": errors,
    }
