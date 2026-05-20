import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt

from gui.theme import apply_theme
from gui.controllers.app_controller import AppController


def _exception_hook(exc_type, exc_value, exc_tb):
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    app = QApplication.instance()
    if app:
        QMessageBox.critical(
            None,
            "Unexpected Error",
            f"An unexpected error occurred and the application may be unstable.\n\n"
            f"{exc_type.__name__}: {exc_value}\n\n"
            f"Please check the logs for details.",
        )
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def run_app():
    sys.excepthook = _exception_hook

    app = QApplication(sys.argv)
    app.setApplicationName("SEBI RA Automation")
    app.setApplicationDisplayName("SEBI RA Automation Software")
    app.setOrganizationName("SEBI RA")
    app.setStyle("Fusion")

    apply_theme("dark")

    controller = AppController()

    from gui.app import MainWindow
    window = MainWindow(controller)
    window.setMinimumSize(1024, 600)
    window.resize(1280, 800)
    window.show()

    exit_code = app.exec()
    sys.exit(exit_code)
