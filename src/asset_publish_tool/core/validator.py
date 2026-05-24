import json
import re
from pathlib import Path

AVAILABLE_VALIDATION_CHECKS = [
    "lowercase_name",
    "no_spaces",
    "valid_characters",
    "frozen_transforms",
]


class ValidationError(Exception):
    """Raised when validation configuration or validation logic fails."""


# ----------------------------------------------------------------------
# Validation configuration
# ----------------------------------------------------------------------


def load_validation_rules(config_path: Path) -> dict:
    """
    Load validation rules from a JSON configuration file.

    Args:
        config_path (Path): Path to the validation rules JSON file.

    Returns:
        dict: Loaded validation rule data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Validation config not found: {config_path}")

    with open(config_path, "r") as file:
        return json.load(file)


# ----------------------------------------------------------------------
# Object type validation
# ----------------------------------------------------------------------


def identify_object_type(object_name: str, rules: dict):
    """
    Identify an asset type based on configured naming patterns.

    Args:
        object_name (str): Maya object name.
        rules (dict): Loaded validation rules.

    Returns:
        str | None: Matching object type, or None if no pattern matches.
    """
    object_rules = rules["scene_object_rules"]

    for object_type, rule_data in object_rules.items():
        pattern = rule_data["name_pattern"]

        if re.match(pattern, object_name):
            return object_type

    return None


# ----------------------------------------------------------------------
# Name validation
# ----------------------------------------------------------------------


def validate_name_checks(
    object_name: str,
    required_checks: list[str],
) -> list[str]:
    """
    Validate an object name against configured naming checks.

    Args:
        object_name (str): Maya object name.
        required_checks (list[str]): Validation checks to apply.

    Returns:
        list[str]: Validation error messages.
    """
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


# ----------------------------------------------------------------------
# Scene validation
# ----------------------------------------------------------------------


def validate_scene_object(
    object_name: str,
    rules: dict,
    maya_object_type=None,
) -> dict:
    """
    Validate a Maya scene object against configured publish rules.

    Validation includes:
    - naming pattern validation
    - object type matching
    - required naming checks
    - export eligibility

    Args:
        object_name (str): Maya object name.
        rules (dict): Loaded validation rules.
        maya_object_type (str, optional): Detected Maya object type.

    Returns:
        dict: Validation result dictionary containing object type,
        validation state, export eligibility, and error messages.
    """
    errors = []

    name_object_type = identify_object_type(
        object_name,
        rules,
    )

    if name_object_type is None:
        errors.append("Object name does not match any known type pattern.")

    if maya_object_type and maya_object_type != "unknown":
        object_type = maya_object_type

        if name_object_type and name_object_type != maya_object_type:
            errors.append(
                (
                    f"Name suggests '{name_object_type}', "
                    f"but Maya object type is '{maya_object_type}'."
                )
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

    object_rule = rules["scene_object_rules"].get(
        object_type,
        {},
    )

    required_checks = object_rule.get(
        "required_checks",
        [],
    )

    name_errors = validate_name_checks(
        object_name,
        required_checks,
    )

    errors.extend(name_errors)

    return {
        "name": object_name,
        "type": object_type,
        "valid": len(errors) == 0,
        "export_to_usd": object_rule.get(
            "export_to_usd",
            False,
        ),
        "errors": errors,
    }
