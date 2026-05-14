import shutil
from pathlib import Path

import maya.cmds as cmds

from asset_publish_tool.core.validator import (
    load_validation_rules,
    validate_scene_object,
)
from asset_publish_tool.database.asset_repository import (
    create_publish_package,
    load_binary_file,
    save_asset,
    store_publish_package,
)
from asset_publish_tool.maya.preview import capture_viewport_preview
from asset_publish_tool.maya.scene_utils import (
    detect_maya_object_type,
    get_expanded_scene_selection,
    get_mesh_transforms_from_selection,
)
from asset_publish_tool.usd.usd_utils import process_exported_usd


def validate_selected_objects():
    # 1. Load rules
    project_root = (
        Path(__file__).resolve().parents[3]
    )  # gets the main project folder by going up from this file’s location
    config_path = (
        project_root / "config" / "validation_rules.json"
    )  # builds the full path to the JSON config file inside the project
    rules = load_validation_rules(config_path)

    # 2. Get selection from Maya
    selection = get_expanded_scene_selection()

    if not selection:
        print("No objects selected.")
        return []

    print(f"Validating {len(selection)} object(s)...\n")

    results = []

    # 3. Validate each object
    for obj in selection:
        # Skip group-only transforms (objects with no shape nodes)
        shapes = cmds.listRelatives(obj, shapes=True)

        if not shapes:
            continue

        clean_obj_name = obj.split("|")[-1]
        maya_object_type = detect_maya_object_type(obj)
        result = validate_scene_object(clean_obj_name, rules, maya_object_type)
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


def publish_selected_objects():
    from asset_publish_tool.core.asset import Asset
    from asset_publish_tool.core.metadata import write_metadata
    from asset_publish_tool.core.versioning import get_next_version

    project_root = Path(__file__).resolve().parents[3]

    config_path = project_root / "config" / "validation_rules.json"
    rules = load_validation_rules(config_path)

    selection = get_expanded_scene_selection()

    summary = {
        "published": [],
        "skipped": [],
    }

    if not selection:
        print("No objects selected.")
        return summary

    publish_root = project_root / "published_assets"

    for obj in selection:
        # Skip group-only transforms (objects with no shape nodes)
        shapes = cmds.listRelatives(obj, shapes=True)

        if not shapes:
            continue

        clean_obj_name = obj.split("|")[-1]
        maya_object_type = detect_maya_object_type(obj)
        result = validate_scene_object(clean_obj_name, rules, maya_object_type)

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

        version = get_next_version(publish_root, asset_type, asset_name)

        version_path = publish_root / asset_type / asset_name / version
        version_path.mkdir(parents=True, exist_ok=True)

        obj_export_file = None
        usd_export_file = version_path / f"{asset_name}.usd"

        cmds.select(obj, replace=True)

        # Export OBJ only for model assets.
        # OBJ is a geometry format, so cameras and lights should not be exported as OBJ.
        if asset_type == "model":
            obj_export_file = version_path / f"{asset_name}.obj"

            if not cmds.pluginInfo("objExport", query=True, loaded=True):
                cmds.loadPlugin("objExport")

            cmds.file(
                str(obj_export_file),
                force=True,
                options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
                type="OBJexport",
                exportSelected=True,
            )

        # Export USD for all supported asset types.
        # USD can represent models, cameras, and lights, so this is the main pipeline export.
        cmds.file(
            str(usd_export_file),
            force=True,
            type="USD Export",
            exportSelected=True,
        )

        usd_processed = process_exported_usd(
            usd_file=usd_export_file,
            asset_name=asset_name,
            asset_type=asset_type,
            version=version,
            author="osher",
            source_scene=cmds.file(query=True, sceneName=True) or "unsaved_scene",
        )

        if not usd_processed:
            summary["skipped"].append(
                {
                    "name": obj,
                    "reason": "USD post-processing failed",
                    "errors": [],
                }
            )
            continue

        preview_file = version_path / f"{asset_name}_preview.png"

        try:
            capture_viewport_preview(obj, preview_file)
            preview_path = str(preview_file)
            preview_image = load_binary_file(preview_file)
        except Exception as e:
            preview_path = ""
            preview_image = None
            print(f"Preview capture failed for {asset_name}: {e}")

        package = create_publish_package(version_path)

        package_name = f"{asset_name}_{version}.zip"

        package_file_id = store_publish_package(
            package,
            package_name,
        )

        asset = Asset(
            name=asset_name,
            asset_type=asset_type,
            source_scene=cmds.file(query=True, sceneName=True) or "unsaved_scene",
            version=version,
            publish_path=str(version_path),
            author="osher",
            exports={
                "obj": str(obj_export_file),
                "usd": str(usd_export_file),
                "preview": preview_path,
            },
            package_file_id=str(package_file_id),
            preview_image=preview_image,
        )

        metadata_file = version_path / "metadata.json"
        write_metadata(asset, metadata_file)

        try:
            mongo_id = save_asset(asset.to_mongo_dict())
            print(f"Saved asset metadata to MongoDB: {mongo_id}")
            shutil.rmtree(version_path)
            asset_folder = version_path.parent
            asset_type_folder = asset_folder.parent

            if asset_folder.exists() and not any(asset_folder.iterdir()):
                asset_folder.rmdir()

            if asset_type_folder.exists() and not any(asset_type_folder.iterdir()):
                asset_type_folder.rmdir()
        except Exception as e:
            print(f"MongoDB save failed for {asset_name}: {e}")

        summary["published"].append(
            {
                "name": asset_name,
                "type": asset_type,
                "version": version,
            }
        )

    # Reselect only skipped objects (using full Maya paths)
    skipped_objects = [item["name"] for item in summary["skipped"]]

    # Make sure objects still exist
    skipped_objects = [obj for obj in skipped_objects if cmds.objExists(obj)]

    if skipped_objects:
        cmds.select(skipped_objects, replace=True)
    else:
        cmds.select(clear=True)

    return summary
