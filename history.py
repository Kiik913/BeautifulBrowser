"""
History - History viewer with search and clear options
"""

from PySide6.QtCore import Qt, QDate, QDateTime, QSortFilterProxyModel, QModelIndex
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLineEdit, QMenu, QMessageBox, QHeaderView, QTableView)

from database import Database
from utils import resource_path


class HistoryDialog(QDialog):
    """Dialog to view and manage browsing history"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("History")
        self.resize(700, 450)

        layout = QVBoxLayout(self)

        # Search bar
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search history...")
        self.search_edit.textChanged.connect(self.filter_history)
        search_layout.addWidget(self.search_edit)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all_history)
        search_layout.addWidget(self.clear_btn)

        layout.addLayout(search_layout)

        # History list (table)
        self.history_view = QTableView()
        self.history_view.setAlternatingRowColors(True)
        self.history_view.setSortingEnabled(True)
        self.history_view.horizontalHeader().setStretchLastSection(True)
        self.history_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_view.customContextMenuRequested.connect(self.show_context_menu)
        # Double‑click to open in new tab
        self.history_view.doubleClicked.connect(self.on_double_click)

        self.model = QStandardItemModel(0, 3, self)
        self.model.setHorizontalHeaderLabels(["Title", "URL", "Date"])
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(-1)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.history_view.setModel(self.proxy_model)

        layout.addWidget(self.history_view)

        self.load_history()
        self.update_editing_state()

    def load_history(self):
        self.model.removeRows(0, self.model.rowCount())
        history = self.db.get_history()
        for url, title, timestamp in history:
            title_item = QStandardItem(title or "Untitled")
            title_item.setData(url, Qt.UserRole)
            url_item = QStandardItem(url)
            date_str = QDateTime.fromSecsSinceEpoch(timestamp).toString("yyyy-MM-dd hh:mm")
            date_item = QStandardItem(date_str)
            self.model.appendRow([title_item, url_item, date_item])

        self.history_view.setColumnWidth(0, 250)
        self.history_view.setColumnWidth(1, 300)
        self.history_view.setColumnWidth(2, 150)

    def filter_history(self, text: str):
        self.proxy_model.setFilterRegularExpression(text)

    def clear_all_history(self):
        # Check if editing is allowed
        if not self.is_editing_enabled():
            QMessageBox.warning(
                self,
                "Restricted",
                "History editing is disabled. Enable it in Settings → Privacy → 'Enable history editing'."
            )
            return

        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all history?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.clear_history()
            self.load_history()

    def on_double_click(self, index):
        """Open the selected URL in a new tab"""
        if not index.isValid():
            return
        # Map through proxy model
        source_index = self.proxy_model.mapToSource(index)
        url = self.model.item(source_index.row(), 1).text()
        if url:
            self.parent().tab_widget.new_tab(url)

    def show_context_menu(self, pos):
        index = self.history_view.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        open_act = menu.addAction("Open in New Tab")
        delete_act = menu.addAction("Delete")
        action = menu.exec(self.history_view.viewport().mapToGlobal(pos))

        if action == delete_act:
            if not self.is_editing_enabled():
                QMessageBox.warning(
                    self,
                    "Restricted",
                    "History editing is disabled. Enable it in Settings → Privacy → 'Enable history editing'."
                )
                return
            row = self.proxy_model.mapToSource(index).row()
            url = self.model.item(row, 1).text()
            self.db.delete_history_item(url)
            self.load_history()
        elif action == open_act:
            row = self.proxy_model.mapToSource(index).row()
            url = self.model.item(row, 1).text()
            self.parent().tab_widget.new_tab(url)

    def is_editing_enabled(self):
        """Check the setting from database"""
        return self.db.get_setting("history_editing", "false") == "true"

    def update_editing_state(self):
        """Enable/disable clear button and context menu actions based on setting"""
        enabled = self.is_editing_enabled()
        self.clear_btn.setEnabled(enabled)
        # The context menu actions will be checked in show_context_menu

    def showEvent(self, event):
        """Refresh state when dialog is shown"""
        super().showEvent(event)
        self.update_editing_state()
