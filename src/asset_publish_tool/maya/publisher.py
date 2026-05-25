import shutil
from pathlib import Path

import maya.cmds as cmds

from asset_publish_tool.auth.roles import has_permission
from asset_publish_tool.auth.session import (
    get_current_user,
    get_current_user_role,
)
from asset_publish_tool.core.asset import Asset
from asset_publish_tool.core.metadata import write_metadata
from asset_publish_tool.core.validator import (
    load_validation_rules,
    validate_scene_object,
)
from asset_publish_tool.database.asset_repository import (
    create_publish_package,
    get_next_asset_version,
    load_binary_file,
    save_asset,
    store_publish_package,
)
from asset_publish_tool.maya.preview import capture_viewport_preview
from asset_publish_tool.maya.scene_utils import (
    detect_maya_object_type,
    get_expanded_scene_selection,
    has_frozen_transforms,
)
from asset_publish_tool.usd.usd_utils import process_exported_usd

# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------


def validate_selected_objects():
    """
    Validate the current Maya scene selection against configured publish rules.

    Validation includes:
    - naming convention checks
    - object type validation
    - frozen transform validation
    - export eligibility checks

    Returns:
        list: Validation result dictionaries for each processed object.

    Raises:
        PermissionError: If the current user does not have validation permission.
    """
    current_role = get_current_user_role()

    if current_role is None:
        raise PermissionError("No authenticated user session found.")

    if not has_permission(current_role, "validate_assets"):
        raise PermissionError(
            f"Current user role '{current_role}' does not have permission to validate assets."
        )

    project_root = Path(__file__).resolve().parents[3]

    config_path = project_root / "config" / "validation_rules.json"
    rules = load_validation_rules(config_path)

    selection = get_expanded_scene_selection()

    if not selection:
        print("No objects selected.")
        return []

    print(f"Validating {len(selection)} object(s)...\n")

    results = []

    for obj in selection:
        shapes = cmds.listRelatives(obj, shapes=True)

        if not shapes:
            continue

        clean_obj_name = obj.split("|")[-1]
        maya_object_type = detect_maya_object_type(obj)

        result = validate_scene_object(
            clean_obj_name,
            rules,
            maya_object_type,
        )

        object_rule = rules["scene_object_rules"].get(result["type"], {})
        required_checks = object_rule.get("required_checks", [])

        if "frozen_transforms" in required_checks:
            if not has_frozen_transforms(obj):
                result["errors"].append("Object transforms must be frozen.")
                result["valid"] = False

        results.append(result)

        print(f"Object: {result['name']}")
        print(f"Type: {result['type']}")
        print(f"Valid: {result['valid']}")
        print(f"Export to USD: {result['export_to_usd']}")

        if result["errors"]:
            print("Errors:")
            for err in result["errors"]:
                print(f" - {err}")

        print("-" * 30)

    return results


# ----------------------------------------------------------------------
# Material warnings
# ----------------------------------------------------------------------


def get_material_assignment_warnings(obj):
    """
    Check whether a Maya object uses multiple material assignments.

    This is primarily used to warn about potential issues when exporting
    face-assigned materials to USD.

    Args:
        obj (str): Maya transform object name.

    Returns:
        list: Warning messages related to material assignments.
    """
    warnings = []

    shapes = (
        cmds.listRelatives(
            obj,
            shapes=True,
            fullPath=True,
        )
        or []
    )

    for shape in shapes:
        shading_groups = (
            cmds.listConnections(
                shape,
                type="shadingEngine",
            )
            or []
        )

        unique_shading_groups = sorted(set(shading_groups))

        if len(unique_shading_groups) > 1:
            warnings.append(
                (
                    "Multiple material assignments may not fully preserve "
                    "face-assigned materials in USD."
                )
            )

    return warnings


# ----------------------------------------------------------------------
# Publishing
# ----------------------------------------------------------------------


def publish_selected_objects():
    """
    Publish selected Maya scene assets to the asset management system.

    The publishing workflow performs validation, export, USD post-processing,
    metadata generation, package creation, GridFS storage, and MongoDB
    metadata registration.

    Returns:
        dict: Summary containing published assets, skipped assets, and warnings.

    Raises:
        PermissionError: If the current user does not have publish permission.
    """
    current_role = get_current_user_role()

    if current_role is None:
        raise PermissionError("No authenticated user session found.")

    if not has_permission(current_role, "publish_assets"):
        raise PermissionError(
            f"Current user role '{current_role}' does not have permission to publish assets."
        )

    project_root = Path(__file__).resolve().parents[3]

    config_path = project_root / "config" / "validation_rules.json"
    rules = load_validation_rules(config_path)

    selection = get_expanded_scene_selection()

    summary = {
        "published": [],
        "skipped": [],
        "warnings": [],
    }

    if not selection:
        print("No objects selected.")
        return summary

    publish_root = project_root / "tmp_publish_cache"

    for obj in selection:
        shapes = cmds.listRelatives(obj, shapes=True)

        if not shapes:
            continue

        clean_obj_name = obj.split("|")[-1]
        maya_object_type = detect_maya_object_type(obj)

        result = validate_scene_object(
            clean_obj_name,
            rules,
            maya_object_type,
        )

        if not result["valid"]:
            summary["skipped"].append(
                {
                    "name": obj,
                    "reason": "Invalid object",
                    "errors": result["errors"],
                }
            )
            continue

        if not result["export_to_usd"]:
            summary["skipped"].append(
                {
                    "name": obj,
                    "reason": "Not marked for export",
                    "errors": [],
                }
            )
            continue

        asset_type = result["type"]
        asset_name = result["name"]

        material_warnings = get_material_assignment_warnings(obj)

        for warning in material_warnings:
            print(f"Warning: {warning}")

            summary["warnings"].append(
                {
                    "name": asset_name,
                    "warning": warning,
                }
            )

        source_scene = (
            cmds.file(
                query=True,
                sceneName=True,
            )
            or "unsaved_scene"
        )

        current_user = get_current_user()
        author = current_user.get("username", "Unknown")

        version = get_next_asset_version(
            asset_name,
            asset_type,
        )

        version_path = publish_root / asset_type / asset_name / version
        version_path.mkdir(parents=True, exist_ok=True)

        obj_export_file = None
        usd_export_file = version_path / f"{asset_name}.usda"

        cmds.select(obj, replace=True)

        world_matrix = cmds.xform(
            obj,
            query=True,
            matrix=True,
            worldSpace=True,
        )

        if asset_type == "model":
            obj_export_file = version_path / f"{asset_name}.obj"

            if not cmds.pluginInfo(
                "objExport",
                query=True,
                loaded=True,
            ):
                cmds.loadPlugin("objExport")

            cmds.file(
                str(obj_export_file),
                force=True,
                options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
                type="OBJexport",
                exportSelected=True,
            )

        cmds.mayaUSDExport(
            file=str(usd_export_file),
            selection=True,
            exportRoots=[obj],
            shadingMode="useRegistry",
            convertMaterialsTo=["UsdPreviewSurface"],
            exportUVs=True,
            exportColorSets=True,
            defaultUSDFormat="usda",
        )

        usd_text = usd_export_file.read_text(encoding="utf-8")

        if "material:binding" not in usd_text:
            print(
                "Material binding missing after USD export. "
                "Retrying without material conversion."
            )

            cmds.mayaUSDExport(
                file=str(usd_export_file),
                selection=True,
                exportRoots=[obj],
                shadingMode="useRegistry",
                exportUVs=True,
                exportColorSets=True,
                defaultUSDFormat="usda",
            )

        usd_processed = process_exported_usd(
            usd_file=usd_export_file,
            asset_name=asset_name,
            asset_type=asset_type,
            version=version,
            author=author,
            source_scene=source_scene,
            world_matrix=world_matrix,
        )

        if not usd_processed["success"]:
            summary["skipped"].append(
                {
                    "name": obj,
                    "reason": "USD post-processing failed",
                    "errors": usd_processed["errors"],
                }
            )
            continue

        for warning in usd_processed["warnings"]:
            summary["warnings"].append(
                {
                    "name": asset_name,
                    "warning": warning,
                }
            )

        preview_file = version_path / f"{asset_name}_preview.png"

        try:
            capture_viewport_preview(obj, preview_file)
            preview_path = str(preview_file)
            preview_image = load_binary_file(preview_file)

        except Exception as e:
            preview_path = ""
            preview_image = None

            print(f"Preview capture failed for {asset_name}: {e}")

        asset = Asset(
            name=asset_name,
            asset_type=asset_type,
            source_scene=source_scene,
            version=version,
            publish_path=str(version_path),
            author=author,
            exports={
                "obj": str(obj_export_file),
                "usd": str(usd_export_file),
                "preview": preview_path,
            },
            preview_image=preview_image,
        )

        metadata_file = version_path / f"{asset_name}_metadata.json"

        write_metadata(
            asset,
            metadata_file,
        )

        package = create_publish_package(version_path)

        package_name = f"{asset_name}_{version}.zip"

        package_file_id = store_publish_package(
            package,
            package_name,
        )

        asset.package_file_id = str(package_file_id)

        try:
            mongo_id = save_asset(asset.to_mongo_dict())

            print(f"Saved asset metadata to MongoDB: {mongo_id}")

            shutil.rmtree(version_path)

            asset_folder = version_path.parent
            type_folder = asset_folder.parent

            if asset_folder.exists() and not any(asset_folder.iterdir()):
                asset_folder.rmdir()

            if type_folder.exists() and not any(type_folder.iterdir()):
                type_folder.rmdir()

        except Exception as e:
            print(f"MongoDB save failed for {asset_name}: {e}")

        summary["published"].append(
            {
                "name": asset_name,
                "type": asset_type,
                "version": version,
            }
        )

    skipped_objects = [item["name"] for item in summary["skipped"]]

    skipped_objects = [obj for obj in skipped_objects if cmds.objExists(obj)]

    if skipped_objects:
        cmds.select(
            skipped_objects,
            replace=True,
        )
    else:
        cmds.select(clear=True)

    return summary
