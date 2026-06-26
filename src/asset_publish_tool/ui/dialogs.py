"""
Dialog windows used by the Asset Publish Tool UI.

This module contains standalone dialogs for initial administrator setup
and user login. Keeping these dialogs separate from the main window helps
keep the primary UI module smaller and easier to maintain.
"""

from asset_publish_tool.ui.compat import QtWidgets, get_maya_main_window


class InitialSetupDialog(QtWidgets.QDialog):
    """
    Dialog used to create the initial administrator account.

    Displayed automatically when no admin user exists in the database.
    """

    def __init__(self, parent=None):
        super().__init__(parent or get_maya_main_window())

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
        """
        Create the first administrator user and log in automatically.
        """
        from asset_publish_tool.auth.login import login
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

        success = login(username, password)

        if not success:
            self.message_label.setText("Automatic login failed.")
            return

        self.accept()


class LoginDialog(QtWidgets.QDialog):
    """
    Authentication dialog for MongoDB-backed user login.
    """

    def __init__(self, parent=None):
        super().__init__(parent or get_maya_main_window())

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
        """
        Validate login fields and authenticate the user.
        """
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
