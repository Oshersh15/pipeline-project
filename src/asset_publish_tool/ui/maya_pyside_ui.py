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

from asset_publish_tool.auth.roles import has_permission
from asset_publish_tool.auth.session import (
    clear_current_user,
    get_current_user,
)
from asset_publish_tool.database.asset_repository import get_all_assets
from asset_publish_tool.maya.importer import import_asset_package
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


def pattern_to_suffix(pattern):
    if pattern.startswith(".*") and pattern.endswith("$"):
        return pattern[2:-1]

    return pattern


def suffix_to_pattern(suffix):
    suffix = suffix.strip()

    if not suffix:
        return ".*$"

    return f".*{suffix}$"


class AdminSettingsDialog(QtWidgets.QDialog):
    def __init__(self, admin_widget, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Admin Settings")
        self.resize(500, 600)

        layout = QtWidgets.QVBoxLayout(self)

        layout.addWidget(admin_widget)


class PipelineToolWindow(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_main_window()):
        super().__init__(parent)

        self.setWindowTitle("Asset Publish Tool")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self.build_ui()
        self.connect_signals()
        self.apply_role_permissions()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        current_user = get_current_user()

        username = current_user.get("username", "Unknown")
        role = current_user.get("role", "Unknown")

        self.user_label = QtWidgets.QLabel(f"Logged in as: {username} ({role})")

        self.logout_button = QtWidgets.QPushButton("Logout")
        self.admin_settings_button = QtWidgets.QPushButton("Admin Settings")

        self.validate_button = QtWidgets.QPushButton("Validate Selected Objects")
        self.fix_button = QtWidgets.QPushButton("Fix Invalid Names")
        self.publish_button = QtWidgets.QPushButton("Publish Selected Objects")
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search published assets...")
        self.import_asset_button = QtWidgets.QPushButton("Import Selected Asset")
        self.import_asset_button.setEnabled(False)
        self.delete_asset_button = QtWidgets.QPushButton("Delete Selected Asset")
        self.delete_asset_button.setEnabled(False)
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
            self.build_admin_settings_ui()

        if hasattr(self, "asset_type_dropdown"):
            if self.asset_type_dropdown.count() > 0:
                self.load_validation_rule_ui(self.asset_type_dropdown.currentText())

        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(self.user_label)
        header_layout.addStretch()

        if current_role == "app_admin":
            header_layout.addWidget(self.admin_settings_button)

        header_layout.addWidget(self.logout_button)

        action_layout = QtWidgets.QHBoxLayout()
        action_layout.addWidget(self.validate_button)
        action_layout.addWidget(self.fix_button)
        action_layout.addWidget(self.publish_button)

        asset_action_layout = QtWidgets.QHBoxLayout()
        asset_action_layout.addWidget(self.import_asset_button)

        if current_role == "app_admin":
            asset_action_layout.addWidget(self.delete_asset_button)

        layout.addLayout(header_layout)
        if current_role in ["artist", "app_admin"]:
            layout.addLayout(action_layout)
        layout.addWidget(self.output)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tabs)
        layout.addLayout(asset_action_layout)

        self.load_published_assets()

    def build_admin_settings_ui(self):
        self.admin_settings_widget = QtWidgets.QWidget()

        admin_layout = QtWidgets.QVBoxLayout(self.admin_settings_widget)
        admin_layout.setSpacing(8)
        admin_layout.setContentsMargins(10, 10, 10, 10)

        self.admin_tabs = QtWidgets.QTabWidget()
        admin_layout.addWidget(self.admin_tabs)

        # -------------------------
        # Users tab
        # -------------------------
        self.users_tab = QtWidgets.QWidget()

        users_layout = QtWidgets.QVBoxLayout(self.users_tab)
        users_layout.setSpacing(6)
        users_layout.setContentsMargins(10, 10, 10, 10)

        self.admin_tabs.addTab(self.users_tab, "Users")

        self.new_username_input = QtWidgets.QLineEdit()
        self.new_username_input.setPlaceholderText("Username")

        self.new_password_input = QtWidgets.QLineEdit()
        self.new_password_input.setPlaceholderText("Password")
        self.new_password_input.setEchoMode(QtWidgets.QLineEdit.Password)

        role_layout = QtWidgets.QHBoxLayout()
        role_layout.setSpacing(6)

        role_layout.addWidget(QtWidgets.QLabel("Role"))

        self.role_dropdown = QtWidgets.QComboBox()
        self.role_dropdown.addItems(["viewer", "artist", "app_admin"])
        self.role_dropdown.setFixedWidth(140)

        role_layout.addWidget(self.role_dropdown)

        role_layout.addStretch()

        users_layout.addWidget(QtWidgets.QLabel("Existing Users"))

        self.users_table = QtWidgets.QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["Username", "Role", "Actions"])

        self.users_table.horizontalHeader().setStretchLastSection(True)

        users_layout.addWidget(self.users_table)
        self.load_users_table()

        users_layout.addSpacing(20)

        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)

        users_layout.addSpacing(12)
        users_layout.addWidget(separator)
        users_layout.addSpacing(20)

        users_layout.addWidget(QtWidgets.QLabel("Create User"))
        self.create_user_button = QtWidgets.QPushButton("Create User")

        users_layout.addWidget(self.new_username_input)
        users_layout.addWidget(self.new_password_input)
        users_layout.addLayout(role_layout)
        users_layout.addWidget(self.create_user_button)

        users_layout.addStretch()

        # -------------------------
        # Validation Rules tab
        # -------------------------
        self.validation_tab = QtWidgets.QWidget()

        validation_layout = QtWidgets.QVBoxLayout(self.validation_tab)
        validation_layout.setSpacing(6)
        validation_layout.setContentsMargins(10, 10, 10, 10)

        self.admin_tabs.addTab(self.validation_tab, "Validation Rules")

        from asset_publish_tool.core.validator import (
            AVAILABLE_VALIDATION_CHECKS,
            load_validation_rules,
        )

        validation_layout.addWidget(QtWidgets.QLabel("Asset Type"))

        self.asset_type_dropdown = QtWidgets.QComboBox()
        validation_layout.addWidget(self.asset_type_dropdown)

        project_root = Path(__file__).resolve().parents[3]
        config_path = project_root / "config" / "validation_rules.json"

        self.validation_rules_path = config_path
        self.validation_rules = load_validation_rules(config_path)

        scene_rules = self.validation_rules["scene_object_rules"]

        for asset_type in scene_rules.keys():
            self.asset_type_dropdown.addItem(asset_type)

        validation_layout.addSpacing(20)

        validation_layout.addWidget(QtWidgets.QLabel("Naming Rules"))

        suffix_layout = QtWidgets.QHBoxLayout()
        suffix_layout.setSpacing(6)

        self.use_default_suffix_checkbox = QtWidgets.QCheckBox(
            "Use default suffix based on Maya object type"
        )
        self.use_default_suffix_checkbox.setChecked(True)

        validation_layout.addWidget(self.use_default_suffix_checkbox)

        custom_suffix_layout = QtWidgets.QHBoxLayout()

        custom_suffix_layout.addWidget(QtWidgets.QLabel("Custom suffix"))

        self.name_pattern_input = QtWidgets.QLineEdit()
        self.name_pattern_input.setPlaceholderText("e.g. _model")

        custom_suffix_layout.addWidget(self.name_pattern_input)

        validation_layout.addLayout(custom_suffix_layout)

        self.validation_checkboxes = {}

        naming_checks = [
            "lowercase_name",
            "no_spaces",
            "valid_characters",
        ]

        asset_checks = [
            "frozen_transforms",
        ]

        for check_name in naming_checks:
            if check_name not in AVAILABLE_VALIDATION_CHECKS:
                continue

            checkbox = QtWidgets.QCheckBox(check_name.replace("_", " ").title())
            self.validation_checkboxes[check_name] = checkbox
            validation_layout.addWidget(checkbox)

        validation_layout.addSpacing(14)
        validation_layout.addWidget(QtWidgets.QLabel("Asset Rules"))

        for check_name in asset_checks:
            if check_name not in AVAILABLE_VALIDATION_CHECKS:
                continue

            checkbox = QtWidgets.QCheckBox(check_name.replace("_", " ").title())
            self.validation_checkboxes[check_name] = checkbox
            validation_layout.addWidget(checkbox)

        self.save_validation_rules_button = QtWidgets.QPushButton(
            "Save Validation Rules"
        )

        validation_layout.addWidget(self.save_validation_rules_button)

        validation_layout.addStretch()

    def show_admin_settings(self):
        dialog = AdminSettingsDialog(
            self.admin_settings_widget,
            parent=self,
        )

        dialog.exec()

    def _create_asset_table(self, show_preview=True):
        table = QtWidgets.QTableWidget()

        if show_preview:
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(
                ["Preview", "Asset Name", "Version", "Publisher", "Published At"]
            )
            table.setIconSize(QtCore.QSize(80, 80))
            table.verticalHeader().setDefaultSectionSize(90)
        else:
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(
                ["Asset Name", "Version", "Publisher", "Published At"]
            )
            table.verticalHeader().setDefaultSectionSize(35)

        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        table.setSortingEnabled(True)

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
        self.search_bar.textChanged.connect(self.filter_asset_tables)
        self.import_asset_button.clicked.connect(self.import_selected_asset)
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

        if hasattr(self, "asset_type_dropdown"):
            self.asset_type_dropdown.currentTextChanged.connect(
                self.load_validation_rule_ui
            )

        if hasattr(self, "save_validation_rules_button"):
            self.save_validation_rules_button.clicked.connect(
                self.save_validation_rules
            )

        if hasattr(self, "use_default_suffix_checkbox"):
            self.use_default_suffix_checkbox.stateChanged.connect(
                self.update_suffix_input_state
            )

        if hasattr(self, "admin_settings_button"):
            self.admin_settings_button.clicked.connect(self.show_admin_settings)

        if hasattr(self, "delete_asset_button"):
            self.delete_asset_button.clicked.connect(self.delete_selected_asset)

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
        self.load_users_table()

    def change_user_role(self, username):
        from asset_publish_tool.auth.user_manager import update_user_role
        from asset_publish_tool.database.connection import get_database

        roles = ["viewer", "artist", "app_admin"]

        new_role, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Change User Role",
            f"Select new role for '{username}':",
            roles,
            0,
            False,
        )

        if not ok:
            return

        db = get_database()

        updated = update_user_role(
            username=username,
            new_role=new_role,
            db=db,
        )

        if not updated:
            self.output.setText(f"Failed to update role for '{username}'.")
            return

        self.output.setText(f"Updated '{username}' to role '{new_role}'.")
        self.load_users_table()

    def delete_user(self, username):
        from asset_publish_tool.auth.session import (
            get_current_user,
        )
        from asset_publish_tool.auth.user_manager import (
            delete_user_by_username,
        )
        from asset_publish_tool.database.connection import (
            get_database,
        )

        current_user = get_current_user()

        if current_user:
            current_username = current_user.get("username")

            if username == current_username:
                self.output.setText("You cannot delete your own account.")
                return

        db = get_database()

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Delete User",
            f"Are you sure you want to delete user '{username}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

        if confirm != QtWidgets.QMessageBox.Yes:
            return

        deleted = delete_user_by_username(
            username,
            db,
        )

        if not deleted:
            self.output.setText(f"Failed to delete user '{username}'.")
            return

        self.output.setText(f"Deleted user '{username}'.")

        self.load_users_table()

    def apply_role_permissions(self):
        current_user = get_current_user()

        if not current_user:
            self.validate_button.setEnabled(False)
            self.fix_button.setEnabled(False)
            self.publish_button.setEnabled(False)
            self.open_folder_button.setEnabled(False)
            return

        role = current_user.get("role")

        can_validate = has_permission(role, "validate_assets")
        can_publish = has_permission(role, "publish_assets")
        can_view = has_permission(role, "view_assets")

        self.validate_button.setEnabled(can_validate)
        self.fix_button.setEnabled(can_validate)
        self.publish_button.setEnabled(can_publish)

        self.search_bar.setEnabled(can_view)
        self.tabs.setEnabled(can_view)

    def load_validation_rule_ui(self, asset_type):
        scene_rules = self.validation_rules["scene_object_rules"]

        rule_data = scene_rules.get(asset_type, {})

        self.name_pattern_input.setText(
            pattern_to_suffix(rule_data.get("name_pattern", ""))
        )

        required_checks = rule_data.get(
            "required_checks",
            [],
        )

        for check_name, checkbox in self.validation_checkboxes.items():
            checkbox.setChecked(check_name in required_checks)

        default_suffix = f"_{asset_type}"
        current_suffix = self.name_pattern_input.text().strip()

        use_default_suffix = current_suffix == default_suffix

        self.use_default_suffix_checkbox.setChecked(use_default_suffix)
        self.update_suffix_input_state()

    def update_suffix_input_state(self):
        use_default = self.use_default_suffix_checkbox.isChecked()

        self.name_pattern_input.setEnabled(not use_default)

    def save_validation_rules(self):
        import json

        asset_type = self.asset_type_dropdown.currentText()

        scene_rules = self.validation_rules["scene_object_rules"]

        if asset_type not in scene_rules:
            self.output.setText(f"Unknown asset type: {asset_type}")
            return

        enabled_checks = []

        for check_name, checkbox in self.validation_checkboxes.items():
            if checkbox.isChecked():
                enabled_checks.append(check_name)

        if self.use_default_suffix_checkbox.isChecked():
            suffix = f"_{asset_type}"
        else:
            suffix = self.name_pattern_input.text().strip()

        scene_rules[asset_type]["name_pattern"] = suffix_to_pattern(suffix)

        scene_rules[asset_type]["required_checks"] = enabled_checks

        with open(self.validation_rules_path, "w") as file:
            json.dump(
                self.validation_rules,
                file,
                indent=2,
            )

        self.output.setText(f"Saved validation rules for '{asset_type}'.")

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
        author = metadata.get("author", "")
        created_at = self.format_timestamp(metadata.get("created_at", ""))

        table.setSortingEnabled(False)

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

            name_column = 1
            version_column = 2
            author_column = 3
            created_at_column = 4

        else:
            name_column = 0
            version_column = 1
            author_column = 2
            created_at_column = 3

        name_item = QtWidgets.QTableWidgetItem(asset_name)
        name_item.setData(QtCore.Qt.UserRole, metadata.get("package_file_id"))
        name_item.setData(
            QtCore.Qt.UserRole + 1,
            str(metadata.get("_id")),
        )
        name_item.setData(QtCore.Qt.UserRole + 1, str(metadata.get("_id")))
        table.setItem(row, name_column, name_item)

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
        table.setItem(row, author_column, QtWidgets.QTableWidgetItem(author))
        table.setItem(row, created_at_column, QtWidgets.QTableWidgetItem(created_at))

        table.setSortingEnabled(True)

    def load_users_table(self):
        from asset_publish_tool.auth.session import get_current_user
        from asset_publish_tool.auth.user_manager import get_all_users
        from asset_publish_tool.database.connection import get_database

        if not hasattr(self, "users_table"):
            return

        db = get_database()
        users = get_all_users(db)

        current_user = get_current_user()
        current_username = current_user.get("username") if current_user else None

        self.users_table.setRowCount(0)

        for user in users:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)

            username = user.get("username", "")
            role = user.get("role", "")

            self.users_table.setItem(
                row,
                0,
                QtWidgets.QTableWidgetItem(username),
            )

            self.users_table.setItem(
                row,
                1,
                QtWidgets.QTableWidgetItem(role),
            )

            actions_button = QtWidgets.QPushButton("⋮")

            if username == current_username:
                actions_button.setEnabled(False)
                actions_button.setToolTip(
                    "You cannot modify your own account while logged in."
                )

            actions_menu = QtWidgets.QMenu(actions_button)

            change_role_action = actions_menu.addAction("Change Role")
            delete_action = actions_menu.addAction("Delete User")

            change_role_action.triggered.connect(
                lambda checked=False, username=username: self.change_user_role(username)
            )

            delete_action.triggered.connect(
                lambda checked=False, username=username: self.delete_user(username)
            )

            actions_button.setMenu(actions_menu)

            self.users_table.setCellWidget(
                row,
                2,
                actions_button,
            )

    def delete_selected_asset(self):
        from asset_publish_tool.database.asset_repository import delete_asset

        current_table = self.tabs.currentWidget()
        selected_rows = current_table.selectionModel().selectedRows()

        if not selected_rows:
            self.output.setText("No published asset selected.")
            return

        row = selected_rows[0].row()

        if current_table == self.model_table:
            name_column = 1
        else:
            name_column = 0

        name_item = current_table.item(row, name_column)

        if not name_item:
            self.output.setText("Could not read selected asset.")
            return

        asset_name = name_item.text()
        package_file_id = name_item.data(QtCore.Qt.UserRole)
        asset_id = name_item.data(QtCore.Qt.UserRole + 1)

        if not asset_id:
            self.output.setText("Selected asset has no MongoDB asset ID.")
            return

        confirm = QtWidgets.QMessageBox.question(
            self,
            "Delete Asset",
            f"Delete asset '{asset_name}' from MongoDB and GridFS?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

        if confirm != QtWidgets.QMessageBox.Yes:
            return

        deleted = delete_asset(
            asset_id=asset_id,
            package_file_id=package_file_id,
        )

        if not deleted:
            self.output.setText(f"Failed to delete asset '{asset_name}'.")
            return

        self.output.setText(f"Deleted asset '{asset_name}' from MongoDB/GridFS.")

        self.load_published_assets()
        self.filter_asset_tables()

    def _on_version_changed(self, table, row, dropdown, show_preview=True):
        metadata = dropdown.currentData()

        if not metadata:
            return

        author = metadata.get("author", "")
        created_at = self.format_timestamp(metadata.get("created_at", ""))

        table.setSortingEnabled(False)

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
            author_column = 3
            created_at_column = 4

        else:
            name_item = table.item(row, 0)
            author_column = 2
            created_at_column = 3

        if name_item:
            name_item.setData(QtCore.Qt.UserRole, metadata.get("package_file_id"))
            name_item.setData(
                QtCore.Qt.UserRole + 1,
                str(metadata.get("_id")),
            )
            name_item.setData(QtCore.Qt.UserRole + 1, str(metadata.get("_id")))

        table.setItem(row, author_column, QtWidgets.QTableWidgetItem(author))
        table.setItem(row, created_at_column, QtWidgets.QTableWidgetItem(created_at))

        table.setSortingEnabled(True)

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
            self.import_asset_button.setEnabled(False)

            if hasattr(self, "delete_asset_button"):
                self.delete_asset_button.setEnabled(False)

            return

        row = selected_rows[0].row()

        if show_preview:
            name_column = 1
        else:
            name_column = 0

        name_item = table.item(row, name_column)

        if not name_item:
            self.import_asset_button.setEnabled(False)

            if hasattr(self, "delete_asset_button"):
                self.delete_asset_button.setEnabled(False)

            return

        asset_name = name_item.text()

        package_file_id = name_item.data(QtCore.Qt.UserRole)
        asset_id = name_item.data(QtCore.Qt.UserRole + 1)

        self.import_asset_button.setEnabled(bool(package_file_id))

        if hasattr(self, "delete_asset_button"):
            self.delete_asset_button.setEnabled(bool(asset_id))

        matching_object = self.find_scene_object_by_asset_name(asset_name)

        if matching_object:
            cmds.select(matching_object, replace=True)
            self.output.setText(f"Selected scene object: {matching_object}")
        else:
            self.output.setText(
                f"Published asset selected: {asset_name}\n"
                f"No matching object with this name was found in the current Maya scene."
            )

    # def open_selected_publish_folder(self):
    #     if not self.selected_publish_path:
    #         return

    #     publish_path = Path(self.selected_publish_path)

    #     if not publish_path.exists():
    #         self.output.setText(f"Publish folder does not exist:\n{publish_path}")
    #         return

    #     system = platform.system()

    #     if system == "Darwin":  # macOS
    #         subprocess.Popen(["open", str(publish_path)])
    #     elif system == "Windows":
    #         os.startfile(str(publish_path))
    #     else:  # Linux
    #         subprocess.Popen(["xdg-open", str(publish_path)])

    #     self.output.setText(f"Opened publish folder:\n{publish_path}")

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

        renamed = results.get("renamed", [])
        already_valid = results.get("already_valid", [])
        skipped = results.get("skipped", [])

        output = "Fix Names Summary\n"
        output += "=" * 30 + "\n\n"

        output += f"Renamed: {len(renamed)}\n"
        output += f"Already Valid: {len(already_valid)}\n"
        output += f"Skipped: {len(skipped)}\n\n"

        if renamed:
            output += "Renamed\n"
            output += "-" * 30 + "\n"

            for item in renamed:
                output += f"{item['old_name']} → {item['new_name']}\n"

                if item.get("reason"):
                    output += f"   - {item['reason']}\n"

            output += "\n"

        if skipped:
            output += "Skipped\n"
            output += "-" * 30 + "\n"

            for item in skipped:
                output += f"{item['name']}\n"
                output += f"   - {item['reason']}\n"

            output += "\n"

        if already_valid:
            output += "Already Valid\n"
            output += "-" * 30 + "\n"

            for item in already_valid:
                output += f" - {item['name']}\n"

        self.output.setText(output)

    def run_validation(self):
        try:
            results = validate_selected_objects()
        except PermissionError as e:
            self.output.setText(f"Permission denied:\n{e}")
            return

        if not results:
            self.output.setText("No valid scene objects were selected for validation.")
            return

        valid_results = [result for result in results if result["valid"]]
        invalid_results = [result for result in results if not result["valid"]]

        output = "Validation Summary\n"
        output += "=" * 30 + "\n\n"

        output += f"Checked: {len(results)}\n"
        output += f"Valid: {len(valid_results)}\n"
        output += f"Invalid: {len(invalid_results)}\n\n"

        if invalid_results:
            output += "Needs Fix\n"
            output += "-" * 30 + "\n"

            for result in invalid_results:
                output += f"{result['name']} ({result['type']})\n"

                for error in result["errors"]:
                    output += f"   - {error}\n"

                output += "\n"

        if valid_results:
            output += "Valid Objects\n"
            output += "-" * 30 + "\n"

            for result in valid_results:
                output += f" - {result['name']} ({result['type']})\n"

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

    def import_selected_asset(self):
        current_table = self.tabs.currentWidget()
        selected_rows = current_table.selectionModel().selectedRows()

        if not selected_rows:
            self.output.setText("No published asset selected.")
            return

        row = selected_rows[0].row()

        if current_table == self.model_table:
            name_column = 1
        else:
            name_column = 0

        name_item = current_table.item(row, name_column)

        if not name_item:
            self.output.setText("Could not read selected asset.")
            return

        package_file_id = name_item.data(QtCore.Qt.UserRole)

        if not package_file_id:
            self.output.setText("Selected asset has no stored package file ID.")
            return

        try:
            imported_file = import_asset_package(package_file_id)
        except Exception as e:
            self.output.setText(f"Import failed:\n{e}")
            return

        self.output.setText(f"Imported asset from:\n{imported_file}")

    def format_timestamp(self, timestamp):
        from datetime import datetime

        if not timestamp:
            return ""

        try:
            dt = datetime.fromisoformat(timestamp)

            return dt.strftime("%d %b %Y %H:%M")

        except Exception:
            return timestamp

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
