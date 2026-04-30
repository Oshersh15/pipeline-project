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

    # Remove known wrong suffixes first
    for existing_suffix in ["_model", "_light", "_camera", "_rig"]:
        if clean.endswith(existing_suffix):
            clean = clean[: -len(existing_suffix)]

    return f"{clean}{suffix}"


def fix_object_name(obj):
    suggested_name = build_suggested_name(obj)

    if not suggested_name:
        return None

    new_name = cmds.rename(obj, suggested_name)
    return new_name


def fix_selected_object_names():
    selection = get_mesh_transforms_from_selection()

    if not selection:
        print("No objects selected.")
        return []

    renamed = []

    for obj in selection:
        old_name = obj
        new_name = fix_object_name(obj)

        renamed.append(
            {
                "old_name": old_name,
                "new_name": new_name,
            }
        )

        print(f"Renamed: {old_name} -> {new_name}")

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
    # Keeps the original selection, including cameras and lights.
    # If a selected item is a group, also adds mesh objects inside it.
    selection = cmds.ls(selection=True, long=True)

    if not selection:
        return []

    expanded = []

    for obj in selection:
        expanded.append(obj)

        meshes = (
            cmds.listRelatives(obj, allDescendents=True, type="mesh", fullPath=True)
            or []
        )

        for mesh in meshes:
            parent = cmds.listRelatives(mesh, parent=True, fullPath=True)
            if parent:
                expanded.append(parent[0])

    return list(dict.fromkeys(expanded))
