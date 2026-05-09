import json
import re
from pathlib import Path


class ValidationError(Exception):
    pass


# 1. Load config file
def load_validation_rules(config_path: Path) -> dict:
    if not config_path.exists():
        raise FileNotFoundError(f"Validation config not found: {config_path}")

    with open(config_path, "r") as file:
        return json.load(file)


# 2. Identify object type using regex
def identify_object_type(object_name: str, rules: dict):
    object_rules = rules["scene_object_rules"]

    for object_type, rule_data in object_rules.items():
        pattern = rule_data["name_pattern"]

        if re.match(pattern, object_name):
            return object_type

    return None


# 3. Basic name validation
def validate_basic_name_rules(object_name: str) -> list[str]:
    errors = []

    if not object_name:
        errors.append("Name cannot be empty.")

    if " " in object_name:
        errors.append("Name must not contain spaces.")

    if object_name != object_name.lower():
        errors.append("Name must be lowercase.")

    if not re.match(r"^[a-z0-9_]+$", object_name):
        errors.append(
            "Name can only contain lowercase letters, numbers, and underscores."
        )

    return errors


# 4. Full validation per object
def validate_scene_object(object_name: str, rules: dict, maya_object_type=None) -> dict:
    errors = []

    # Type suggested by the object name, e.g. chair_light -> light
    name_object_type = identify_object_type(object_name, rules)

    if name_object_type is None:
        errors.append("Object name does not match any known type pattern.")

    # If Maya type was provided, compare it against the name-based type
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

    # Basic name checks
    name_errors = validate_basic_name_rules(object_name)
    errors.extend(name_errors)

    object_rule = rules["scene_object_rules"].get(object_type, {})

    return {
        "name": object_name,
        "type": object_type,
        "valid": len(errors) == 0,
        "export_to_usd": object_rule.get("export_to_usd", False),
        "errors": errors,
    }
