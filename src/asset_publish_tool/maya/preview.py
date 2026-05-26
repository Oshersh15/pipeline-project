"""
Viewport preview generation utilities for Maya assets.

This module creates isolated viewport previews used during the
publishing workflow. Temporary duplicate geometry is normalised,
framed in the active model panel, and captured as preview images
without modifying the original scene content.
"""

from pathlib import Path

import maya.cmds as cmds


def _get_model_panel():
    """
    Return the active Maya model panel used for viewport capture.
    """
    panel = cmds.getPanel(withFocus=True)

    if panel and cmds.getPanel(typeOf=panel) == "modelPanel":
        return panel

    panels = cmds.getPanel(type="modelPanel") or []
    if panels:
        return panels[0]

    raise RuntimeError("No model panel found for preview capture.")


def _get_panel_camera(panel):
    camera = cmds.modelPanel(panel, query=True, camera=True)

    if cmds.objectType(camera) == "camera":
        parent = cmds.listRelatives(camera, parent=True, fullPath=True)
        if parent:
            return parent[0], camera

    shapes = cmds.listRelatives(camera, shapes=True, fullPath=True) or []
    for shape in shapes:
        if cmds.objectType(shape) == "camera":
            return camera, shape

    return camera, None


def _store_camera_state(panel):
    """
    Store the current viewport camera transform and display settings.

    This allows preview capture to temporarily modify the viewport
    camera while restoring the user's original state afterwards.
    """
    camera_transform, camera_shape = _get_panel_camera(panel)

    state = {
        "camera_transform": camera_transform,
        "camera_shape": camera_shape,
        "matrix": None,
        "focal_length": None,
        "orthographic_width": None,
    }

    if camera_transform and cmds.objExists(camera_transform):
        state["matrix"] = cmds.xform(
            camera_transform,
            query=True,
            matrix=True,
            worldSpace=True,
        )

    if camera_shape and cmds.objExists(camera_shape):
        if cmds.attributeQuery("focalLength", node=camera_shape, exists=True):
            state["focal_length"] = cmds.getAttr(f"{camera_shape}.focalLength")

        if cmds.attributeQuery("orthographicWidth", node=camera_shape, exists=True):
            state["orthographic_width"] = cmds.getAttr(
                f"{camera_shape}.orthographicWidth"
            )

    return state


def _restore_camera_state(state):
    """
    Restore previously stored viewport camera settings.
    """
    camera_transform = state.get("camera_transform")
    camera_shape = state.get("camera_shape")

    if camera_transform and cmds.objExists(camera_transform) and state.get("matrix"):
        cmds.xform(
            camera_transform,
            matrix=state["matrix"],
            worldSpace=True,
        )

    if camera_shape and cmds.objExists(camera_shape):
        if state.get("focal_length") is not None:
            cmds.setAttr(f"{camera_shape}.focalLength", state["focal_length"])

        if state.get("orthographic_width") is not None:
            cmds.setAttr(
                f"{camera_shape}.orthographicWidth",
                state["orthographic_width"],
            )


def _collect_mesh_transforms(obj):
    """
    Collect mesh transform nodes from an object hierarchy.

    This includes both directly assigned mesh shapes and descendant
    mesh objects used for preview generation.
    """
    mesh_transforms = []

    shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
    for shape in shapes:
        if cmds.objectType(shape) == "mesh":
            mesh_transforms.append(obj)
            break

    child_meshes = (
        cmds.listRelatives(
            obj,
            allDescendents=True,
            type="mesh",
            fullPath=True,
        )
        or []
    )

    for mesh_shape in child_meshes:
        parent = cmds.listRelatives(mesh_shape, parent=True, fullPath=True)
        if parent:
            mesh_transforms.append(parent[0])

    return list(dict.fromkeys(mesh_transforms))


def _create_normalised_preview_group(obj):
    """
    Create a temporary normalised duplicate group for preview capture.

    The duplicated geometry is centred and uniformly scaled so assets
    produce consistent viewport previews regardless of original size
    or scene placement.
    """
    mesh_transforms = _collect_mesh_transforms(obj)

    if not mesh_transforms:
        return None

    preview_group = cmds.group(empty=True, name="asset_preview_temp_grp", world=True)

    for mesh in mesh_transforms:
        duplicate = cmds.duplicate(mesh, renameChildren=True)[0]
        cmds.parent(duplicate, preview_group)

    bbox = cmds.exactWorldBoundingBox(preview_group)

    min_x, min_y, min_z, max_x, max_y, max_z = bbox

    centre_x = (min_x + max_x) / 2.0
    centre_y = (min_y + max_y) / 2.0
    centre_z = (min_z + max_z) / 2.0

    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z

    max_size = max(size_x, size_y, size_z)

    if max_size <= 0:
        max_size = 1.0

    cmds.setAttr(
        f"{preview_group}.translate",
        -centre_x,
        -centre_y,
        -centre_z,
        type="double3",
    )

    scale = 5.0 / max_size
    cmds.setAttr(f"{preview_group}.scale", scale, scale, scale, type="double3")

    return preview_group


def capture_viewport_preview(obj, output_path):
    """
    Capture a viewport preview image for a Maya asset.

    The workflow temporarily isolates duplicated geometry in the active
    model panel, frames the asset, captures a playblast image, and then
    restores the original viewport and selection state.

    Args:
        obj (str): Maya object to preview.
        output_path (Path | str): Output preview image path.

    Returns:
        str: Final preview image path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    previous_selection = cmds.ls(selection=True, long=True) or []

    panel = _get_model_panel()
    previous_grid_state = cmds.modelEditor(panel, query=True, grid=True)
    previous_isolate_state = cmds.isolateSelect(panel, query=True, state=True)
    camera_state = _store_camera_state(panel)

    preview_group = None

    try:
        preview_group = _create_normalised_preview_group(obj)

        if not preview_group:
            raise RuntimeError(f"No mesh found for preview capture: {obj}")

        cmds.select(preview_group, replace=True)

        cmds.setFocus(panel)
        cmds.modelEditor(panel, edit=True, grid=False)

        cmds.isolateSelect(panel, state=True)
        cmds.isolateSelect(panel, addSelected=True)

        cmds.viewSet(p=True, fit=True)
        cmds.viewFit()

        cmds.refresh(force=True)

        cmds.playblast(
            completeFilename=str(output_path),
            forceOverwrite=True,
            format="image",
            widthHeight=(512, 512),
            showOrnaments=False,
            frame=cmds.currentTime(query=True),
            viewer=False,
        )

    finally:
        if panel and cmds.getPanel(typeOf=panel) == "modelPanel":
            cmds.isolateSelect(panel, state=previous_isolate_state)
            cmds.modelEditor(panel, edit=True, grid=previous_grid_state)

        _restore_camera_state(camera_state)

        if preview_group and cmds.objExists(preview_group):
            cmds.delete(preview_group)

        if previous_selection:
            cmds.select(previous_selection, replace=True)
        else:
            cmds.select(clear=True)

    return str(output_path)
