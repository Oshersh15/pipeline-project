import importlib.util
import os
import platform
import subprocess
from pathlib import Path

import maya.cmds as cmds

if importlib.util.find_spec("PySide6"):
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
else:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui

from asset_publish_tool.auth.session import (
    clear_current_user,
    get_current_user,
)
from asset_publish_tool.database.asset_repository import get_all_assets
from asset_publish_tool.maya.publisher import (
    publish_selected_objects,
    validate_selected_objects,
)
from asset_publish_tool.maya.scene_utils import fix_selected_object_names


def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class InitialSetupDialog(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)

        self.setWindowTitle("Initial Setup")
        self.setMinimumWidth(300)

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Admin Username")

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Admin Password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)

        self.message_label = QtWidgets.QLabel("")

        self.create_button = QtWidgets.QPushButton("Create Admin")

        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(
            QtWidgets.QLabel(
                "No admin user exists.\nCreate the initial administrator account."
            )
        )

        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.message_label)
        layout.addWidget(self.create_button)

        self.create_button.clicked.connect(self.create_admin)

    def create_admin(self):
        from asset_publish_tool.auth.user_manager import create_user
        from asset_publish_tool.database.connection import get_database

        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.message_label.setText("Please enter username and password.")
            return

        db = get_database()

        created = create_user(
            username=username,
            password=password,
            role="app_admin",
            db=db,
        )

        if not created:
            self.message_label.setText("User already exists.")
            return

        from asset_publish_tool.auth.login import login

        success = login(username, password)

        if not success:
            self.message_label.setText("Automatic login failed.")
            return

        self.accept()


class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)

        self.setWindowTitle("Asset Publish Login")
        self.setMinimumWidth(300)

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)

        self.message_label = QtWidgets.QLabel("")
        self.message_label.setWordWrap(True)

        self.login_button = QtWidgets.QPushButton("Login")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Log in to Asset Publish Tool"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.message_label)
        layout.addWidget(self.login_button)

        self.login_button.clicked.connect(self.attempt_login)

    def attempt_login(self):
        from asset_publish_tool.auth.login import login

        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.message_label.setText("Please enter a username and password.")
            return

        if login(username, password):
            self.accept()
        else:
            self.message_label.setText("Login failed. Check username/password.")


class PipelineToolWindow(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)

        self.setWindowTitle("Asset Publish Tool")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self.build_ui()
        self.connect_signals()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        current_user = get_current_user()

        username = current_user.get("username", "Unknown")
        role = current_user.get("role", "Unknown")

        self.user_label = QtWidgets.QLabel(f"Logged in as: {username} ({role})")

        self.logout_button = QtWidgets.QPushButton("Logout")

        self.validate_button = QtWidgets.QPushButton("Validate Selected Objects")
        self.fix_button = QtWidgets.QPushButton("Fix Invalid Names")
        self.publish_button = QtWidgets.QPushButton("Publish Selected Objects")
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search published assets...")
        self.open_folder_button = QtWidgets.QPushButton("Open Selected Publish Folder")
        self.open_folder_button.setEnabled(False)
        self.selected_publish_path = ""
        self.output = QtWidgets.QTextEdit()
        self.output.setReadOnly(True)

        self.tabs = QtWidgets.QTabWidget()

        current_user = get_current_user()
        current_role = current_user.get("role") if current_user else None

        self.model_table = self._create_asset_table(show_preview=True)
        self.camera_table = self._create_asset_table(show_preview=False)
        self.light_table = self._create_asset_table(show_preview=False)

        self.tabs.addTab(self.model_table, "Models")
        self.tabs.addTab(self.camera_table, "Cameras")
        self.tabs.addTab(self.light_table, "Lights")

        if current_role == "app_admin":
            self.admin_tab = QtWidgets.QWidget()

            admin_layout = QtWidgets.QVBoxLayout(self.admin_tab)

            self.new_username_input = QtWidgets.QLineEdit()
            self.new_username_input.setPlaceholderText("Username")

            self.new_password_input = QtWidgets.QLineEdit()
            self.new_password_input.setPlaceholderText("Password")
            self.new_password_input.setEchoMode(QtWidgets.QLineEdit.Password)

            self.role_dropdown = QtWidgets.QComboBox()
            self.role_dropdown.addItems(["viewer", "artist", "app_admin"])

            self.create_user_button = QtWidgets.QPushButton("Create User")

            admin_layout.addWidget(QtWidgets.QLabel("Admin Tools"))

            admin_layout.addWidget(self.new_username_input)
            admin_layout.addWidget(self.new_password_input)
            admin_layout.addWidget(self.role_dropdown)
            admin_layout.addWidget(self.create_user_button)

            self.tabs.addTab(self.admin_tab, "Admin")

        layout.addWidget(self.user_label)
        layout.addWidget(self.logout_button)
        layout.addWidget(self.validate_button)
        layout.addWidget(self.fix_button)
        layout.addWidget(self.publish_button)
        layout.addWidget(self.output)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tabs)
        layout.addWidget(self.open_folder_button)

        self.load_published_assets()

    def _create_asset_table(self, show_preview=True):
        table = QtWidgets.QTableWidget()

        if show_preview:
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(
                ["Preview", "Asset Name", "Version", "Publish Path"]
            )
            table.setIconSize(QtCore.QSize(80, 80))
            table.verticalHeader().setDefaultSectionSize(90)
        else:
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels(["Asset Name", "Version", "Publish Path"])
            table.verticalHeader().setDefaultSectionSize(35)

        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        header = table.horizontalHeader()

        for column in range(table.columnCount()):
            if column == table.columnCount() - 1:
                header.setSectionResizeMode(column, QtWidgets.QHeaderView.Stretch)
            else:
                header.setSectionResizeMode(
                    column, QtWidgets.QHeaderView.ResizeToContents
                )

        return table

    def connect_signals(self):
        self.validate_button.clicked.connect(self.run_validation)
        self.fix_button.clicked.connect(self.run_fix_names)
        self.publish_button.clicked.connect(self.run_publish)

        self.open_folder_button.clicked.connect(self.open_selected_publish_folder)
        self.search_bar.textChanged.connect(self.filter_asset_tables)
        self.logout_button.clicked.connect(self.logout)

        self.model_table.itemSelectionChanged.connect(
            lambda: self.on_table_selection_changed(self.model_table, show_preview=True)
        )
        self.camera_table.itemSelectionChanged.connect(
            lambda: self.on_table_selection_changed(
                self.camera_table, show_preview=False
            )
        )

        self.light_table.itemSelectionChanged.connect(
            lambda: self.on_table_selection_changed(
                self.light_table, show_preview=False
            )
        )

        if hasattr(self, "create_user_button"):
            self.create_user_button.clicked.connect(self.create_new_user)

    def create_new_user(self):
        from asset_publish_tool.auth.user_manager import create_user
        from asset_publish_tool.database.connection import get_database

        username = self.new_username_input.text().strip()
        password = self.new_password_input.text()
        role = self.role_dropdown.currentText()

        if not username or not password:
            self.output.setText("Username and password are required.")
            return

        db = get_database()

        created = create_user(
            username=username,
            password=password,
            role=role,
            db=db,
        )

        if not created:
            self.output.setText(f"User '{username}' already exists.")
            return

        self.output.setText(f"Created user '{username}' with role '{role}'.")

        self.new_username_input.clear()
        self.new_password_input.clear()

    def load_published_assets(self):
        self.model_table.setRowCount(0)
        self.camera_table.setRowCount(0)
        self.light_table.setRowCount(0)

        asset_documents = get_all_assets()

        assets_by_key = {}

        for metadata in asset_documents:
            asset_name = metadata.get("name", "")
            asset_type = metadata.get("type", metadata.get("asset_type", ""))

            key = (asset_type, asset_name)

            if key not in assets_by_key:
                assets_by_key[key] = []

            assets_by_key[key].append(metadata)

        for key, versions in assets_by_key.items():
            asset_type, asset_name = key

            versions = sorted(
                versions,
                key=lambda item: item.get("version", ""),
                reverse=True,
            )

            latest_metadata = versions[0]

            if asset_type == "model":
                table = self.model_table
                show_preview = True
            elif asset_type == "camera":
                table = self.camera_table
                show_preview = False
            elif asset_type == "light":
                table = self.light_table
                show_preview = False
            else:
                continue

            row = table.rowCount()
            table.insertRow(row)

            self._populate_asset_table_row(
                table,
                row,
                latest_metadata,
                versions,
                show_preview=show_preview,
            )

    def _populate_asset_table_row(
        self, table, row, metadata, all_versions, show_preview=True
    ):
        asset_name = metadata.get("name", metadata.get("asset_name", ""))
        version = metadata.get("version", "")
        publish_path = metadata.get("publish_path", "")

        if show_preview:
            preview_image = metadata.get("preview_image")

            preview_item = QtWidgets.QTableWidgetItem()

            if preview_image:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(preview_image)

                pixmap = pixmap.scaled(
                    80,
                    80,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )

                icon = QtGui.QIcon(pixmap)
                preview_item.setIcon(icon)
            else:
                preview_item.setText("")

            table.setItem(row, 0, preview_item)

            name_item = QtWidgets.QTableWidgetItem(asset_name)
            name_item.setData(
                QtCore.Qt.UserRole,
                metadata.get("package_file_id"),
            )
            table.setItem(row, 1, name_item)

            version_column = 2
            path_column = 3

        else:
            name_item = QtWidgets.QTableWidgetItem(asset_name)
            name_item.setData(
                QtCore.Qt.UserRole,
                metadata.get("package_file_id"),
            )
            table.setItem(row, 0, name_item)

            version_column = 1
            path_column = 2

        version_dropdown = QtWidgets.QComboBox()

        for version_metadata in all_versions:
            version_dropdown.addItem(
                version_metadata.get("version", ""),
                version_metadata,
            )

        version_dropdown.setCurrentText(version)

        version_dropdown.currentIndexChanged.connect(
            lambda index, table=table, table_row=row, dropdown=version_dropdown, show_preview=show_preview: (
                self._on_version_changed(
                    table,
                    table_row,
                    dropdown,
                    show_preview,
                )
            )
        )

        table.setCellWidget(row, version_column, version_dropdown)
        table.setItem(row, path_column, QtWidgets.QTableWidgetItem(publish_path))

    def _on_version_changed(self, table, row, dropdown, show_preview=True):
        metadata = dropdown.currentData()

        if not metadata:
            return

        publish_path = metadata.get("publish_path", "")

        if show_preview:
            preview_image = metadata.get("preview_image")

            preview_item = QtWidgets.QTableWidgetItem()

            if preview_image:
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(preview_image)

                pixmap = pixmap.scaled(
                    80,
                    80,
                    QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation,
                )

                icon = QtGui.QIcon(pixmap)
                preview_item.setIcon(icon)
            else:
                preview_item.setText("")

            table.setItem(row, 0, preview_item)

            name_item = table.item(row, 1)
            if name_item:
                name_item.setData(
                    QtCore.Qt.UserRole,
                    metadata.get("package_file_id"),
                )

            table.setItem(row, 3, QtWidgets.QTableWidgetItem(publish_path))

        else:
            name_item = table.item(row, 0)
            if name_item:
                name_item.setData(
                    QtCore.Qt.UserRole,
                    metadata.get("package_file_id"),
                )

            table.setItem(row, 2, QtWidgets.QTableWidgetItem(publish_path))

    def find_scene_object_by_asset_name(self, asset_name):
        transforms = cmds.ls(type="transform", long=True) or []

        for obj in transforms:
            short_name = obj.split("|")[-1]
            short_name = short_name.split(":")[-1]

            if short_name == asset_name:
                return obj

        return None

    def on_table_selection_changed(self, table, show_preview=True):
        selected_rows = table.selectionModel().selectedRows()

        if not selected_rows:
            self.selected_publish_path = ""
            self.open_folder_button.setEnabled(False)
            return

        row = selected_rows[0].row()

        if show_preview:
            name_column = 1
            path_column = 3
        else:
            name_column = 0
            path_column = 2

        name_item = table.item(row, name_column)
        path_item = table.item(row, path_column)

        if not name_item or not path_item:
            return

        asset_name = name_item.text()
        publish_path = path_item.text()

        self.selected_publish_path = publish_path
        self.open_folder_button.setEnabled(bool(publish_path))

        matching_object = self.find_scene_object_by_asset_name(asset_name)

        if matching_object:
            cmds.select(matching_object, replace=True)
            self.output.setText(f"Selected scene object: {matching_object}")
        else:
            self.output.setText(
                f"Published asset selected: {asset_name}\n"
                f"No matching object with this name was found in the current Maya scene."
            )

    def open_selected_publish_folder(self):
        if not self.selected_publish_path:
            return

        publish_path = Path(self.selected_publish_path)

        if not publish_path.exists():
            self.output.setText(f"Publish folder does not exist:\n{publish_path}")
            return

        system = platform.system()

        if system == "Darwin":  # macOS
            subprocess.Popen(["open", str(publish_path)])
        elif system == "Windows":
            os.startfile(str(publish_path))
        else:  # Linux
            subprocess.Popen(["xdg-open", str(publish_path)])

        self.output.setText(f"Opened publish folder:\n{publish_path}")

    def filter_asset_tables(self):
        search_text = self.search_bar.text().lower().strip()

        tables = [
            (self.model_table, 1),  # Models: name column
            (self.camera_table, 0),  # Cameras: name column
            (self.light_table, 0),  # Lights: name column
        ]

        for table, name_column in tables:
            for row in range(table.rowCount()):
                name_item = table.item(row, name_column)

                if not name_item:
                    table.setRowHidden(row, False)
                    continue

                asset_name = name_item.text().lower()
                should_hide = search_text not in asset_name

                table.setRowHidden(row, should_hide)

    def run_fix_names(self):
        results = fix_selected_object_names()

        output = "Fix Names Result\n"
        output += "=" * 30 + "\n\n"

        for result in results:
            output += f"{result['old_name']} -> {result['new_name']}\n"

            if result.get("reason"):
                output += f"   Note: {result['reason']}\n"

        self.output.setText(output)

    def run_validation(self):
        try:
            results = validate_selected_objects()
        except PermissionError as e:
            self.output.setText(f"Permission denied:\n{e}")
            return

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
        try:
            summary = publish_selected_objects()
        except PermissionError as e:
            self.output.setText(f"Permission denied:\n{e}")
            return

        output = "Publish Summary\n"
        output += "=" * 30 + "\n\n"

        output += f"Published: {len(summary['published'])}\n"
        for item in summary["published"]:
            output += f" - {item['name']} ({item['type']}, {item['version']})\n"
            output += "   Stored in MongoDB/GridFS\n"

        output += "\n"
        output += f"Warnings: {len(summary.get('warnings', []))}\n"
        for item in summary.get("warnings", []):
            output += f" - {item['name']}: {item['warning']}\n"

        output += "\n"
        output += f"Skipped: {len(summary['skipped'])}\n"
        for item in summary["skipped"]:
            output += f" - {item['name']}: {item['reason']}\n"

            for error in item["errors"]:
                output += f"   - {error}\n"

        self.load_published_assets()
        self.filter_asset_tables()
        self.output.setText(output)

    def logout(self):
        clear_current_user()

        self.close()

        show_ui()


window = None


def show_ui():
    global window
    from asset_publish_tool.auth.user_manager import admin_exists
    from asset_publish_tool.database.connection import get_database

    try:
        window.close()
        window.deleteLater()
    except Exception:
        pass

    db = get_database()

    if not admin_exists(db):
        setup_dialog = InitialSetupDialog()

        if setup_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

    if not get_current_user():
        login_dialog = LoginDialog()

        if login_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

    window = PipelineToolWindow()
    window.show()
