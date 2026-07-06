"""
Downloads - Download manager with progress, pause, resume
"""

import os
from PySide6.QtCore import Qt, QUrl, QFileInfo
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableWidget, QTableWidgetItem, QProgressBar,
                               QHeaderView, QMenu, QMessageBox, QFileDialog)
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

from database import Database


class DownloadsDialog(QDialog):
    """Dialog to manage active and completed downloads"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.downloads = []
        self.setWindowTitle("Downloads")
        self.resize(700, 400)

        layout = QVBoxLayout(self)

        clear_btn = QPushButton("Clear Completed")
        clear_btn.clicked.connect(self.clear_completed)
        layout.addWidget(clear_btn, alignment=Qt.AlignRight)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["File", "Progress", "Status", "Size", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        self.load_downloads()

    def load_downloads(self):
        pass

    def add_download(self, download: QWebEngineDownloadRequest):
        row = self.table.rowCount()
        self.table.insertRow(row)

        file_name = QFileInfo(download.downloadFileName()).fileName()
        name_item = QTableWidgetItem(file_name)
        self.table.setItem(row, 0, name_item)

        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        self.table.setCellWidget(row, 1, progress_bar)

        status_item = QTableWidgetItem("Downloading")
        self.table.setItem(row, 2, status_item)

        size_item = QTableWidgetItem("")
        self.table.setItem(row, 3, size_item)

        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(5)

        pause_btn = QPushButton("⏸")
        pause_btn.setFixedSize(25, 25)
        pause_btn.setToolTip("Pause")
        action_layout.addWidget(pause_btn)

        cancel_btn = QPushButton("✕")
        cancel_btn.setFixedSize(25, 25)
        cancel_btn.setToolTip("Cancel")
        action_layout.addWidget(cancel_btn)

        open_btn = QPushButton("📂")
        open_btn.setFixedSize(25, 25)
        open_btn.setToolTip("Open File")
        open_btn.setEnabled(False)
        action_layout.addWidget(open_btn)

        self.table.setCellWidget(row, 4, action_widget)

        download.downloadProgress.connect(lambda received, total, row=row, progress_bar=progress_bar, size_item=size_item:
                                          self.update_progress(received, total, row, progress_bar, size_item))
        download.finished.connect(lambda row=row, download=download, open_btn=open_btn, status_item=status_item:
                                  self.download_finished(row, download, open_btn, status_item))
        download.stateChanged.connect(lambda state, row=row, pause_btn=pause_btn, status_item=status_item:
                                      self.download_state_changed(state, row, pause_btn, status_item))

        self.table.setProperty(f"download_{row}", download)

    def update_progress(self, received: int, total: int, row: int, progress_bar: QProgressBar, size_item: QTableWidgetItem):
        progress = int(received / total * 100) if total > 0 else 0
        progress_bar.setValue(progress)
        size_str = self.format_size(total) if total > 0 else "Unknown"
        size_item.setText(size_str)

    def format_size(self, size: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def download_finished(self, row: int, download: QWebEngineDownloadRequest, open_btn: QPushButton, status_item: QTableWidgetItem):
        status_item.setText("Completed")
        open_btn.setEnabled(True)
        open_btn.clicked.connect(lambda: self.open_file(download.downloadFileName()))

    def download_state_changed(self, state, row: int, pause_btn: QPushButton, status_item: QTableWidgetItem):
        if state == QWebEngineDownloadRequest.DownloadState.DownloadPaused:
            pause_btn.setText("▶")
            pause_btn.setToolTip("Resume")
            status_item.setText("Paused")
        elif state == QWebEngineDownloadRequest.DownloadState.Downloading:
            pause_btn.setText("⏸")
            pause_btn.setToolTip("Pause")
            status_item.setText("Downloading")
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            pass
        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            status_item.setText("Cancelled")
            pause_btn.setEnabled(False)

    def open_file(self, file_path: str):
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def clear_completed(self):
        rows_to_remove = []
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 2)
            if status_item and status_item.text() in ["Completed", "Cancelled"]:
                rows_to_remove.append(row)
        for row in reversed(rows_to_remove):
            self.table.removeRow(row)
