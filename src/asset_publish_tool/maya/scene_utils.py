import re
from pathlib import Path

import maya.cmds as cmds

from asset_publish_tool.core.naming import clean_name
from asset_publish_tool.core.validator import load_validation_rules

# ----------------------------------------------------------------------
# Object type detection
# ----------------------------------------------------------------------


def detect_maya_object_type(obj):
    """
    Detect the publish category of a Maya object based on its shape nodes.

    Supported categories include:
    - model
    - camera
    - light

    Args:
        obj (str): Maya transform object name.

    Returns:
        str: Detected publish type, or "unknown" if unsupported.
    """
    shapes = (
        cmds.listRelatives(
            obj,
            shapes=True,
            fullPath=True,
        )
        or []
    )

    for shape in shapes:
        shape_type = cmds.objectType(shape)

        if shape_type == "mesh":
            return "model"

        if shape_type == "camera":
            return "camera"

        if "Light" in shape_type or shape_type in [
            "light",
            "directionalLight",
            "pointLight",
            "spotLight",
            "areaLight",
        ]:
            return "light"

    return "unknown"


# ----------------------------------------------------------------------
# Validation rule helpers
# ----------------------------------------------------------------------


def pattern_to_suffix(pattern):
    if pattern.startswith(".*") and pattern.endswith("$"):
        return pattern[2:-1]

    return f"_{pattern}"


def get_validation_rules():
    project_root = Path(__file__).resolve().parents[3]
    config_path = project_root / "config" / "validation_rules.json"

    return load_validation_rules(config_path)


def get_suffix_for_type(object_type):
    rules = get_validation_rules()

    object_rule = rules["scene_object_rules"].get(
        object_type,
        {},
    )

    pattern = object_rule.get(
        "name_pattern",
        f".*_{object_type}$",
    )

    return pattern_to_suffix(pattern)


def get_all_configured_suffixes():
    rules = get_validation_rules()

    suffixes = []

    for rule_data in rules["scene_object_rules"].values():
        pattern = rule_data.get("name_pattern", "")
        suffixes.append(pattern_to_suffix(pattern))

    return suffixes


# ----------------------------------------------------------------------
# Selection utilities
# ----------------------------------------------------------------------


def get_expanded_scene_selection():
    """
    Expand the current Maya selection to include nested transform hierarchies.

    Shape selections are automatically converted to their parent transforms.
    Child transforms inside selected groups are also included.

    Returns:
        list: Unique transform objects collected from the expanded selection.
    """
    selection = (
        cmds.ls(
            selection=True,
            long=True,
        )
        or []
    )

    if not selection:
        return []

    expanded = []

    for obj in selection:
        # If user selected a shape, use its parent transform
        if cmds.objectType(obj) != "transform":
            parent = cmds.listRelatives(
                obj,
                parent=True,
                fullPath=True,
            )

            if parent:
                obj = parent[0]

        expanded.append(obj)

        descendants = (
            cmds.listRelatives(
                obj,
                allDescendents=True,
                fullPath=True,
            )
            or []
        )

        for descendant in descendants:
            if cmds.objectType(descendant) == "transform":
                expanded.append(descendant)

            else:
                parent = cmds.listRelatives(
                    descendant,
                    parent=True,
                    fullPath=True,
                )

                if parent:
                    expanded.append(parent[0])

    return list(dict.fromkeys(expanded))


def get_mesh_transforms_from_selection():
    selection = cmds.ls(
        selection=True,
        long=True,
    )

    if not selection:
        print("No objects selected.")
        return []

    mesh_transforms = []

    for item in selection:
        # If the selected item itself is a mesh transform, include it
        shapes = (
            cmds.listRelatives(
                item,
                shapes=True,
                fullPath=True,
            )
            or []
        )

        for shape in shapes:
            if cmds.objectType(shape) == "mesh":
                mesh_transforms.append(item)
                break

        # Also search inside groups / nested hierarchies
        child_shapes = (
            cmds.listRelatives(
                item,
                allDescendents=True,
                type="mesh",
                fullPath=True,
            )
            or []
        )

        for shape in child_shapes:
            parent = cmds.listRelatives(
                shape,
                parent=True,
                fullPath=True,
            )

            if parent:
                mesh_transforms.append(parent[0])

    # Remove duplicates while keeping order
    unique_meshes = []

    for mesh in mesh_transforms:
        if mesh not in unique_meshes:
            unique_meshes.append(mesh)

    return unique_meshes


# ----------------------------------------------------------------------
# Naming utilities
# ----------------------------------------------------------------------


def build_suggested_name(obj):
    """
    Build a cleaned and validated asset name based on configured rules.

    Args:
        obj (str): Maya object name.

    Returns:
        str: Suggested publish-safe object name.
    """
    detected_type = detect_maya_object_type(obj)

    if detected_type == "unknown":
        return clean_name(obj)

    rules = get_validation_rules()

    object_rule = rules["scene_object_rules"].get(
        detected_type,
        {},
    )

    required_checks = object_rule.get(
        "required_checks",
        [],
    )

    clean = clean_name(
        obj,
        required_checks,
    )

    suffix = get_suffix_for_type(detected_type)

    if clean.endswith(suffix):
        return clean

    for known_type in ["model", "light", "camera"]:
        match = re.match(
            rf"^(.*)_{known_type}(\d+)$",
            clean,
        )

        if match:
            base_name = match.group(1)
            number = match.group(2)

            clean = f"{base_name}_{number}"
            break

    for existing_suffix in get_all_configured_suffixes():
        if clean.endswith(existing_suffix):
            clean = clean[: -len(existing_suffix)]

    return f"{clean}{suffix}"


def make_unique_name(suggested_name, current_obj=None):
    """
    Generate a unique Maya object name if the suggested name already exists.

    Args:
        suggested_name (str): Desired object name.
        current_obj (str, optional): Existing Maya object being renamed.

    Returns:
        tuple:
            - str: Unique object name.
            - str: Reason describing any automatic rename adjustment.
    """
    current_long = None

    if current_obj:
        current_match = (
            cmds.ls(
                current_obj,
                long=True,
            )
            or []
        )

        if current_match:
            current_long = current_match[0]

    matches = (
        cmds.ls(
            suggested_name,
            long=True,
        )
        or []
    )

    # Ignore the object itself
    matches = [match for match in matches if match != current_long]

    if not matches:
        return suggested_name, ""

    match = re.match(
        r"^(.*?)(?:_(\d+))?_(model|camera|light)$",
        suggested_name,
    )

    if not match:
        counter = 1

        while True:
            unique_name = f"{suggested_name}_{counter}"

            if not cmds.ls(unique_name, long=True):
                return unique_name, f"'{suggested_name}' already exists."

            counter += 1

    base = match.group(1)
    number = match.group(2)
    suffix = match.group(3)

    counter = int(number) + 1 if number else 2

    while True:
        unique_name = f"{base}_{counter}_{suffix}"

        matches = (
            cmds.ls(
                unique_name,
                long=True,
            )
            or []
        )

        matches = [match for match in matches if match != current_long]

        if not matches:
            return (
                unique_name,
                (
                    f"'{suggested_name}' already exists, "
                    f"so renamed to '{unique_name}' instead."
                ),
            )

        counter += 1


# ----------------------------------------------------------------------
# Name fixing
# ----------------------------------------------------------------------


def fix_object_name(obj):
    """
    Rename a Maya object using the configured naming rules.

    Args:
        obj (str): Maya object to rename.

    Returns:
        tuple:
            - str | None: New Maya object name.
            - str: Result or skip reason.
    """
    original_short_name = obj.split("|")[-1].split(":")[-1]

    detected_type = detect_maya_object_type(obj)

    if detected_type == "unknown":
        return None, "Unsupported object type, skipped."

    suggested_name = build_suggested_name(obj)

    # Skip only if the actual Maya name is already exactly correct
    if original_short_name == suggested_name:
        return None, "Name already valid, skipped."

    unique_name, reason = make_unique_name(
        suggested_name,
        current_obj=obj,
    )

    new_name = cmds.rename(obj, unique_name)

    return new_name, reason


def fix_selected_object_names():
    """
    Apply automatic naming fixes to the expanded Maya selection.

    Returns:
        dict: Summary containing renamed, skipped, and already-valid objects.
    """
    selection = get_expanded_scene_selection()

    results = {
        "renamed": [],
        "already_valid": [],
        "skipped": [],
    }

    if not selection:
        print("No objects selected.")
        return results

    for obj in selection:
        detected_type = detect_maya_object_type(obj)

        if detected_type == "unknown":
            results["skipped"].append(
                {
                    "name": obj,
                    "reason": "Unsupported object type.",
                }
            )
            continue

        original_short_name = obj.split("|")[-1].split(":")[-1]

        suggested_name = build_suggested_name(obj)

        if original_short_name == suggested_name:
            results["already_valid"].append(
                {
                    "name": original_short_name,
                }
            )
            continue

        unique_name, reason = make_unique_name(
            suggested_name,
            current_obj=obj,
        )

        new_name = cmds.rename(obj, unique_name)

        results["renamed"].append(
            {
                "old_name": original_short_name,
                "new_name": new_name,
                "reason": reason,
            }
        )

        print(f"Renamed: {original_short_name} -> {new_name}")

        if reason:
            print(f"Reason: {reason}")

    return results


# ----------------------------------------------------------------------
# Transform validation
# ----------------------------------------------------------------------


def has_frozen_transforms(obj):
    """
    Check whether a Maya transform has frozen translate, rotate, and scale values.

    Args:
        obj (str): Maya transform object name.

    Returns:
        bool: True if transforms are frozen, otherwise False.
    """
    translate_attrs = [
        "translateX",
        "translateY",
        "translateZ",
    ]

    rotate_attrs = [
        "rotateX",
        "rotateY",
        "rotateZ",
    ]

    scale_attrs = [
        "scaleX",
        "scaleY",
        "scaleZ",
    ]

    for attr in translate_attrs + rotate_attrs:
        value = cmds.getAttr(f"{obj}.{attr}")

        if value != 0:
            return False

    for attr in scale_attrs:
        value = cmds.getAttr(f"{obj}.{attr}")

        if value != 1:
            return False

    return True
