from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from gui.theme import get_color
from services.update_service import download_release, launch_updater, get_updater_exe_path
from utils.logger import setup_logger

logger = setup_logger("UpdateCheckerDialog")


class _DownloadWorker(QThread):
    progress = Signal(int, int)
    finished_download = Signal(object)

    def __init__(self, url, dest_path, parent=None):
        super().__init__(parent)
        self._url = url
        self._dest_path = dest_path

    def run(self):
        try:
            result = download_release(
                self._url, self._dest_path, progress_callback=self._on_progress
            )
            self.finished_download.emit(result)
        except Exception as e:
            logger.error(f"Download worker error: {e}", exc_info=True)
            self.finished_download.emit(None)

    def _on_progress(self, downloaded, total):
        self.progress.emit(downloaded, total)


class UpdateCheckerDialog(QDialog):
    update_ready_to_install = Signal(str)

    def __init__(self, current_version, latest_version, release_notes, download_url, parent=None):
        super().__init__(parent)
        self._current_version = current_version
        self._latest_version = latest_version
        self._release_notes = release_notes or ""
        self._download_url = download_url
        self._downloaded_path = None
        self._downloading = False

        self.setWindowTitle("Update Available")
        self.setMinimumWidth(520)
        self.setMinimumHeight(320)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Update Available")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet(
            f"color: {get_color('accent')}; background: transparent;"
        )
        layout.addWidget(title)

        version_label = QLabel(
            f"Current version: {self._current_version}  →  New version: {self._latest_version}"
        )
        version_label.setFont(QFont("Segoe UI", 12))
        version_label.setStyleSheet(
            f"color: {get_color('text_primary')}; background: transparent;"
        )
        layout.addWidget(version_label)

        notes_title = QLabel("Release Notes:")
        notes_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        notes_title.setStyleSheet(
            f"color: {get_color('text_secondary')}; background: transparent;"
        )
        layout.addWidget(notes_title)

        self._notes_area = QTextEdit()
        self._notes_area.setReadOnly(True)
        self._notes_area.setFont(QFont("Segoe UI", 11))
        self._notes_area.setPlainText(self._release_notes if self._release_notes else "No release notes available.")
        self._notes_area.setMinimumHeight(120)
        layout.addWidget(self._notes_area, 1)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._progress_bar.setFormat("%p%")
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(
            f"color: {get_color('text_secondary')}; background: transparent; font-size: 11px;"
        )
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._skip_btn = QPushButton("Skip This Update")
        self._skip_btn.setObjectName("ghost")
        self._skip_btn.setCursor(Qt.PointingHandCursor)
        self._skip_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._skip_btn)

        btn_row.addStretch()

        self._download_btn = QPushButton("Download & Install")
        self._download_btn.setObjectName("success")
        self._download_btn.setMinimumWidth(170)
        self._download_btn.setCursor(Qt.PointingHandCursor)
        self._download_btn.clicked.connect(self._on_download)
        if not self._download_url:
            self._download_btn.setEnabled(False)
            self._download_btn.setToolTip("No downloadable asset found for this release.")
        btn_row.addWidget(self._download_btn)

        layout.addLayout(btn_row)

    def _on_download(self):
        if not self._download_url:
            return

        self._downloading = True
        self._download_btn.setEnabled(False)
        self._download_btn.setText("Downloading...")
        self._skip_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._status_label.setVisible(True)
        self._status_label.setText("Downloading update...")

        self._worker = _DownloadWorker(self._download_url, None, parent=self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_download.connect(self._on_download_complete)
        self._worker.start()

    def _on_progress(self, downloaded, total):
        if total > 0:
            pct = int(downloaded * 100 / total)
            self._progress_bar.setValue(pct)
            mb_dl = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self._progress_bar.setFormat(f"{pct}%  ({mb_dl:.1f} / {mb_total:.1f} MB)")
        else:
            self._progress_bar.setRange(0, 0)
            mb_dl = downloaded / (1024 * 1024)
            self._progress_bar.setFormat(f"Downloading... {mb_dl:.1f} MB")

    def _on_download_complete(self, result):
        self._downloading = False
        if result is not None:
            self._downloaded_path = result
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setValue(100)
            self._progress_bar.setFormat("Download complete!")
            can_auto_install = get_updater_exe_path() is not None
            if can_auto_install:
                msg = (
                    f"Update downloaded to:\n{result}\n\n"
                    "Click Close to quit the application and apply the update."
                )
            else:
                msg = (
                    f"Update downloaded to:\n{result}\n\n"
                    "Restart the application manually to apply the update."
                )
            self._status_label.setText(msg)
            self._status_label.setStyleSheet(
                f"color: {get_color('success')}; background: transparent; font-size: 11px;"
            )
            self._download_btn.setText("Downloaded")
            self._skip_btn.setText("Close")
            self._skip_btn.setEnabled(True)
            self._skip_btn.clicked.disconnect(self.reject)
            self._skip_btn.clicked.connect(self._on_install_and_close)
        else:
            self._progress_bar.setRange(0, 100)
            self._progress_bar.setVisible(False)
            self._status_label.setVisible(True)
            self._status_label.setText("Download failed. Please try again later.")
            self._status_label.setStyleSheet(
                f"color: {get_color('danger')}; background: transparent; font-size: 11px;"
            )
            self._download_btn.setEnabled(True)
            self._download_btn.setText("Download & Install")
            self._skip_btn.setEnabled(True)

    def _on_install_and_close(self):
        if self._downloaded_path:
            can_auto_install = get_updater_exe_path() is not None
            if can_auto_install:
                launched = launch_updater(self._downloaded_path)
                if launched:
                    self.update_ready_to_install.emit(str(self._downloaded_path))
                    self.accept()
                    return
                logger.warning("Failed to launch updater, falling back to manual install")
        self.accept()

    def reject(self):
        if self._downloading:
            return
        super().reject()

    def closeEvent(self, event):
        if self._downloading:
            event.ignore()
            return
        super().closeEvent(event)

    def get_downloaded_path(self) -> Path | None:
        return self._downloaded_path