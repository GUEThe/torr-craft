"""Application entry point."""

import os
import sys

# Keep rendering deterministic in headless / screenshot environments.
os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication

from . import APP_NAME, __version__, icons
from .main_window import MainWindow
from .theme import apply_theme


def create_application(argv=None):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Torr Craft")
    app.setWindowIcon(icons.app_icon())
    apply_theme(app)
    return app


def main(argv=None):
    app = create_application(argv)
    window = MainWindow()
    window.show()
    return app.exec_()
