import maya.cmds as cmds

from asset_publish_tool.maya.publisher import (
    publish_selected_objects,
    validate_selected_objects,
)
from asset_publish_tool.maya.scene_utils import fix_selected_object_names


def show_ui():
    window_name = "pipelineTool"

    # Delete existing window if open
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    # Create window
    window = cmds.window(window_name, title="Pipeline Tool", widthHeight=(400, 300))

    cmds.columnLayout(adjustableColumn=True)

    # Validate button
    cmds.button(label="Validate Selected Objects", command=lambda _: run_validation())

    # Publish button
    cmds.button(label="Publish Selected Objects", command=lambda _: run_publish())

    # Output area
    cmds.scrollField("outputField", editable=False, wordWrap=True, height=200)

    cmds.button(label="Fix Selected Names", command=lambda _: run_fix_names())

    cmds.showWindow(window)


def run_validation():
    results = validate_selected_objects()

    output = ""

    for result in results:
        output += f"{result['name']} → {result['type']} → Valid: {result['valid']}\n"

        if result["errors"]:
            for err in result["errors"]:
                output += f"   - {err}\n"

        output += "\n"

    cmds.scrollField("outputField", edit=True, text=output)


def run_publish():
    # First run validation
    results = validate_selected_objects()

    # Check if there are invalid objects
    invalid_objects = [r for r in results if not r["valid"]]

    if invalid_objects:
        confirm = cmds.confirmDialog(
            title="Validation Warning",
            message="Some objects are invalid and will be skipped.\nContinue?",
            button=["Yes", "Cancel"],
            defaultButton="Yes",
            cancelButton="Cancel",
            dismissString="Cancel",
        )

        if confirm != "Yes":
            cmds.scrollField("outputField", edit=True, text="Publish cancelled.")
            return

    # Run publish
    summary = publish_selected_objects()

    # Build output
    output = "Publish Summary\n"
    output += "=" * 30 + "\n\n"

    output += f"Published: {len(summary['published'])}\n"
    for item in summary["published"]:
        output += f" - {item['name']} ({item['type']}, {item['version']})\n"
        output += f"   {item['path']}\n"

    output += "\n"
    output += f"Skipped: {len(summary['skipped'])}\n"
    for item in summary["skipped"]:
        output += f" - {item['name']}: {item['reason']}\n"

        for error in item["errors"]:
            output += f"   - {error}\n"

    cmds.scrollField("outputField", edit=True, text=output)


def run_fix_names():
    results = fix_selected_object_names()

    output = ""

    for result in results:
        output += f"{result['old_name']} -> {result['new_name']}\n"

    cmds.scrollField("outputField", edit=True, text=output)
