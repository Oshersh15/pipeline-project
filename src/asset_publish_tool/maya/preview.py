from pathlib import Path

import maya.cmds as cmds


def _get_model_panel():
    panel = cmds.getPanel(withFocus=True)

    if panel and cmds.getPanel(typeOf=panel) == "modelPanel":
        return panel

    panels = cmds.getPanel(type="modelPanel") or []
    if panels:
        return panels[0]

    raise RuntimeError("No model panel found for preview capture.")


def _collect_mesh_transforms(obj):
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
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    previous_selection = cmds.ls(selection=True, long=True) or []

    panel = _get_model_panel()
    previous_grid_state = cmds.modelEditor(panel, query=True, grid=True)

    preview_group = None

    try:
        preview_group = _create_normalised_preview_group(obj)

        if not preview_group:
            raise RuntimeError(f"No mesh found for preview capture: {obj}")

        cmds.hide(all=True)
        cmds.showHidden(preview_group)

        children = (
            cmds.listRelatives(
                preview_group,
                allDescendents=True,
                fullPath=True,
            )
            or []
        )

        for child in children:
            if cmds.objectType(child) == "transform":
                cmds.showHidden(child)

        cmds.select(preview_group, replace=True)

        cmds.setFocus(panel)
        cmds.modelEditor(panel, edit=True, grid=False)

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
        if preview_group and cmds.objExists(preview_group):
            cmds.delete(preview_group)

        cmds.showHidden(all=True)

        if panel and cmds.getPanel(typeOf=panel) == "modelPanel":
            cmds.modelEditor(panel, edit=True, grid=previous_grid_state)

        if previous_selection:
            cmds.select(previous_selection, replace=True)
        else:
            cmds.select(clear=True)

    return str(output_path)
