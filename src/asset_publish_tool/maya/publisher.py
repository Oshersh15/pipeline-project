from pathlib import Path

import maya.cmds as cmds

from asset_publish_tool.core.validator import (
    load_validation_rules,
    validate_scene_object,
)
from asset_publish_tool.maya.scene_utils import (
    get_expanded_scene_selection,
    get_mesh_transforms_from_selection,
)


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
        result = validate_scene_object(clean_obj_name, rules)
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
        result = validate_scene_object(clean_obj_name, rules)

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

        # -------------------------------------------------------------
        # CURRENT EXPORT BACKEND: OBJ
        # -------------------------------------------------------------
        # The system supports multiple object types (models, cameras, lights),
        # but the current export backend writes OBJ files.
        #
        # OBJ is suitable for geometry (meshes), but does not support
        # cameras, lights, or full scene data.
        #
        # Therefore:
        # - Models are exported as OBJ
        # - Cameras and lights are detected and validated but skipped
        #
        # This section can later be extended with a USD exporter
        # to support full scene publishing.
        # -------------------------------------------------------------

        if asset_type != "model":
            summary["skipped"].append(
                {
                    "name": obj,
                    "reason": "Detected and validated, but current OBJ export backend only supports model assets",
                    "errors": [],
                }
            )
            continue

        obj_export_file = version_path / f"{asset_name}.obj"
        usd_export_file = version_path / f"{asset_name}.usd"

        # Ensure OBJ plugin is loaded
        if not cmds.pluginInfo("objExport", query=True, loaded=True):
            cmds.loadPlugin("objExport")

        cmds.select(obj, replace=True)

        # Export as OBJ (simple geometry)
        cmds.file(
            str(obj_export_file),
            force=True,
            options="groups=1;ptgroups=1;materials=1;smoothing=1;normals=1",
            type="OBJexport",
            exportSelected=True,
        )

        # Export as USD (main pipeline format)
        cmds.file(
            str(usd_export_file),
            force=True,
            type="USD Export",
            exportSelected=True,
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
            },
        )

        metadata_file = version_path / "metadata.json"
        write_metadata(asset, metadata_file)

        summary["published"].append(
            {
                "name": asset_name,
                "type": asset_type,
                "version": version,
                "path": str(version_path),
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
