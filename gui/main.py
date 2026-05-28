import sys
import traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThreadPool, QTimer

from gui.theme import apply_theme
from gui.controllers.app_controller import AppController
from gui.workers import Worker
from core.config import Config
from services.update_service import check_for_update
from utils.logger import setup_logger

logger = setup_logger("AppStartup")


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


def _check_for_updates(window):
    def _on_update_checked(result):
        if result is None:
            logger.debug("Update check returned no result")
            return
        has_update, latest_version, release_notes, download_url = result
        if has_update:
            from core.version import __version__
            from gui.widgets.update_checker_dialog import UpdateCheckerDialog
            dialog = UpdateCheckerDialog(
                __version__, latest_version, release_notes, download_url, parent=window
            )
            dialog.update_ready_to_install.connect(_on_update_install_ready)
            dialog.exec()

    def _on_update_install_ready(zip_path):
        logger.info(f"Update ready to install: {zip_path}, quitting app...")
        app = QApplication.instance()
        if app:
            app.quit()

    def _on_update_error(err_msg):
        logger.debug(f"Update check error: {err_msg}")

    worker = Worker(check_for_update)
    worker.signals.done.connect(_on_update_checked)
    worker.signals.error.connect(_on_update_error)
    QThreadPool.globalInstance().start(worker)


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

    check_on_startup = Config.get_value("updates", "check_on_startup", True)
    if check_on_startup:
        QTimer.singleShot(2000, lambda: _check_for_updates(window))

    exit_code = app.exec()
    sys.exit(exit_code)
