"""
Qt and Maya UI compatibility helpers.

This module centralises PySide2/PySide6 compatibility imports and
provides access to Maya's main window for parenting custom UI windows.
"""

import importlib.util

import maya.OpenMayaUI as omui

if importlib.util.find_spec("PySide6"):
    from PySide6 import QtCore, QtGui, QtWidgets
    from shiboken6 import wrapInstance
else:
    from PySide2 import QtCore, QtGui, QtWidgets
    from shiboken2 import wrapInstance


def get_maya_main_window():
    """
    Return Maya's main window as a Qt widget.

    Returns:
        QtWidgets.QWidget: Maya main window wrapped as a Qt widget.
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
