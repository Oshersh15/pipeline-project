import importlib.util

# PySide6 → fallback to PySide2
if importlib.util.find_spec("PySide6"):
    from PySide6 import QtWidgets
    from shiboken6 import wrapInstance
else:
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui

from asset_publish_tool.maya.publisher import (
    publish_selected_objects,
    validate_selected_objects,
)
from asset_publish_tool.maya.scene_utils import fix_selected_object_names


def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class PipelineToolWindow(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)

        self.setWindowTitle("Asset Publish Tool")
        self.setMinimumWidth(450)
        self.setMinimumHeight(320)

        self.build_ui()
        self.connect_signals()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        self.validate_button = QtWidgets.QPushButton("Validate Selected Objects")
        self.fix_button = QtWidgets.QPushButton("Fix Invalid Names")
        self.publish_button = QtWidgets.QPushButton("Publish Selected Objects")

        self.output = QtWidgets.QTextEdit()
        self.output.setReadOnly(True)

        layout.addWidget(self.validate_button)
        layout.addWidget(self.fix_button)
        layout.addWidget(self.publish_button)
        layout.addWidget(self.output)

    def connect_signals(self):
        self.validate_button.clicked.connect(self.run_validation)
        self.fix_button.clicked.connect(self.run_fix_names)
        self.publish_button.clicked.connect(self.run_publish)

    def run_fix_names(self):
        results = fix_selected_object_names()

        output = "Fix Names Result\n"
        output += "=" * 30 + "\n\n"

        for result in results:
            output += f"{result['old_name']} -> {result['new_name']}\n"

        self.output.setText(output)

    def run_validation(self):
        results = validate_selected_objects()

        valid_count = sum(1 for r in results if r["valid"])
        invalid_count = len(results) - valid_count

        output = "Validation Result\n"
        output += "=" * 30 + "\n\n"

        output += f"Valid: {valid_count}\n"
        output += f"Invalid: {invalid_count}\n\n"

        for result in results:
            output += (
                f"{result['name']} → {result['type']} → Valid: {result['valid']}\n"
            )

            if result["errors"]:
                for error in result["errors"]:
                    output += f"   - {error}\n"

            output += "\n"

        self.output.setText(output)

    def run_publish(self):
        summary = publish_selected_objects()

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

        self.output.setText(output)


window = None


def show_ui():
    global window

    try:
        window.close()
        window.deleteLater()
    except Exception:
        pass

    window = PipelineToolWindow()
    window.show()
