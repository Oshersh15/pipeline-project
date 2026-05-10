import sys
from pathlib import Path

import maya.cmds as cmds
import maya.mel as mel

MODULE_NAME = "AssetPublishTool"
SHELF_NAME = "AssetPublish"
BUTTON_LABEL = "AssetPublish"


def install_module():
    project_root = Path(__file__).parent

    user_dir = Path(cmds.internalVar(userAppDir=True))
    modules_dir = user_dir / "modules"

    modules_dir.mkdir(parents=True, exist_ok=True)

    mod_file_path = modules_dir / f"{MODULE_NAME}.mod"

    mod_content = f"""+ {MODULE_NAME} 1.0 {project_root}
PYTHONPATH +:= src
"""

    mod_file_path.write_text(mod_content, encoding="utf-8")


def onMayaDroppedPythonFile(*args):  # noqa: N802
    sys.modules.pop("drag_to_maya", None)
    install_module()
    setup_shelf()


def get_button_command():
    launcher_path = Path(__file__).parent / "installer_files" / "launch_ui.py"

    return launcher_path.read_text(encoding="utf-8")


def setup_shelf():
    shelves_layout = mel.eval("$tmpVar=$gShelfTopLevel")

    existing_shelves = (
        cmds.tabLayout(
            shelves_layout,
            query=True,
            childArray=True,
        )
        or []
    )

    if SHELF_NAME in existing_shelves:
        print(f"Shelf '{SHELF_NAME}' already exists.")
    else:
        print(f"Creating shelf '{SHELF_NAME}'.")
        cmds.setParent(shelves_layout)
        cmds.shelfLayout(SHELF_NAME, parent=shelves_layout)
        cmds.tabLayout(
            shelves_layout,
            edit=True,
            tabLabel=(SHELF_NAME, SHELF_NAME),
        )

    button_command = get_button_command()
    existing_button = find_button()
    cmds.setParent(SHELF_NAME)

    if existing_button:
        print("Updating existing shelf button.")
        cmds.shelfButton(
            existing_button,
            edit=True,
            command=button_command,
        )

    else:
        print("Creating new shelf button.")
        cmds.shelfButton(
            label=BUTTON_LABEL,
            command=button_command,
            sourceType="python",
            parent=SHELF_NAME,
            image1=str(get_icon_path()),
            width=25,
            height=25,
        )


def find_button():
    buttons = (
        cmds.shelfLayout(
            SHELF_NAME,
            query=True,
            childArray=True,
        )
        or []
    )

    for button in buttons:
        if cmds.objectTypeUI(button) == "shelfButton":
            label = cmds.shelfButton(
                button,
                query=True,
                label=True,
            )

            if label == BUTTON_LABEL:
                return button

    return None


def get_icon_path():
    return Path(__file__).parent / "icons" / "asset_publish_icon.png"
