import re

import maya.cmds as cmds


def clean_name(name):
    # Remove Maya path if object is part of a hierarchy
    short_name = name.split("|")[-1]

    # Remove namespace if the object has one
    short_name = short_name.split(":")[-1]

    # Convert to lowercase
    clean = short_name.lower()

    # Replace spaces and invalid characters with underscores
    clean = re.sub(r"[^a-z0-9_]+", "_", clean)

    # Remove repeated underscores
    clean = re.sub(r"_+", "_", clean)

    # Remove underscores from start/end
    clean = clean.strip("_")

    return clean


def detect_maya_object_type(obj):
    shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []

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


def build_suggested_name(obj):
    clean = clean_name(obj)
    detected_type = detect_maya_object_type(obj)

    if detected_type == "unknown":
        return clean

    suffix = f"_{detected_type}"

    # If it already has the correct suffix, keep it
    if clean.endswith(suffix):
        return clean

    # Handle names like main_camera1 -> main_1_camera
    for known_type in ["model", "light", "camera", "rig"]:
        match = re.match(rf"^(.*)_{known_type}(\d+)$", clean)

        if match:
            base_name = match.group(1)
            number = match.group(2)
            clean = f"{base_name}_{number}"
            break

    # Remove known wrong suffixes, e.g. chair_light -> chair
    for existing_suffix in ["_model", "_light", "_camera", "_rig"]:
        if clean.endswith(existing_suffix):
            clean = clean[: -len(existing_suffix)]

    return f"{clean}{suffix}"


def make_unique_name(suggested_name, current_obj=None):
    current_long = None

    if current_obj:
        current_match = cmds.ls(current_obj, long=True) or []
        if current_match:
            current_long = current_match[0]

    matches = cmds.ls(suggested_name, long=True) or []

    # Ignore the object itself
    matches = [match for match in matches if match != current_long]

    if not matches:
        return suggested_name, ""

    match = re.match(r"^(.*?)(?:_(\d+))?_(model|camera|light|rig)$", suggested_name)

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
        matches = cmds.ls(unique_name, long=True) or []
        matches = [match for match in matches if match != current_long]

        if not matches:
            return (
                unique_name,
                f"'{suggested_name}' already exists, so renamed to '{unique_name}' instead.",
            )

        counter += 1


def fix_object_name(obj):
    original_short_name = obj.split("|")[-1].split(":")[-1]
    current_clean_name = clean_name(obj)

    detected_type = detect_maya_object_type(obj)

    if detected_type == "unknown":
        return None, "Unsupported object type, skipped."

    suggested_name = build_suggested_name(obj)

    # Skip only if the actual Maya name is already exactly correct
    if original_short_name == suggested_name:
        return None, "Name already valid, skipped."

    unique_name, reason = make_unique_name(suggested_name, current_obj=obj)

    new_name = cmds.rename(obj, unique_name)
    return new_name, reason


def fix_selected_object_names():
    selection = get_expanded_scene_selection()

    if not selection:
        print("No objects selected.")
        return []

    renamed = []

    for obj in selection:
        detected_type = detect_maya_object_type(obj)

        if detected_type == "unknown":
            continue

        old_name = obj
        new_name, reason = fix_object_name(obj)

        if not new_name:
            continue

        renamed.append(
            {
                "old_name": old_name,
                "new_name": new_name,
                "reason": reason,
            }
        )

        print(f"Renamed: {old_name} -> {new_name}")

        if reason:
            print(f"Reason: {reason}")

    return renamed


def get_mesh_transforms_from_selection():
    selection = cmds.ls(selection=True, long=True)

    if not selection:
        print("No objects selected.")
        return []

    mesh_transforms = []

    for item in selection:
        # If the selected item itself is a mesh transform, include it
        shapes = cmds.listRelatives(item, shapes=True, fullPath=True) or []

        for shape in shapes:
            if cmds.objectType(shape) == "mesh":
                mesh_transforms.append(item)
                break

        # Also search inside groups / nested hierarchies
        child_shapes = (
            cmds.listRelatives(item, allDescendents=True, type="mesh", fullPath=True)
            or []
        )

        for shape in child_shapes:
            parent = cmds.listRelatives(shape, parent=True, fullPath=True)

            if parent:
                mesh_transforms.append(parent[0])

    # Remove duplicates while keeping order
    unique_meshes = []
    for mesh in mesh_transforms:
        if mesh not in unique_meshes:
            unique_meshes.append(mesh)

    return unique_meshes


def get_expanded_scene_selection():
    selection = cmds.ls(selection=True, long=True) or []

    if not selection:
        return []

    expanded = []

    for obj in selection:
        # If user selected a shape, use its parent transform
        if cmds.objectType(obj) != "transform":
            parent = cmds.listRelatives(obj, parent=True, fullPath=True)
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
                parent = cmds.listRelatives(descendant, parent=True, fullPath=True)
                if parent:
                    expanded.append(parent[0])

    return list(dict.fromkeys(expanded))
