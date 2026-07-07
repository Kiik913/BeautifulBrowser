"""
Bookmarks - Manage bookmarks with folders
"""

from PySide6.QtCore import Qt, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTreeView, QLineEdit, QLabel, QMenu, QInputDialog,
                               QMessageBox, QFileDialog)

from database import Database
from utils import resource_path


class BookmarksDialog(QDialog):
    """Dialog to manage bookmarks"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Bookmarks")
        self.resize(700, 450)

        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search bookmarks...")
        self.search_edit.textChanged.connect(self.filter_bookmarks)
        toolbar.addWidget(self.search_edit)

        self.add_btn = QPushButton("Add Bookmark")
        self.add_btn.clicked.connect(self.add_bookmark)
        toolbar.addWidget(self.add_btn)

        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.import_bookmarks)
        toolbar.addWidget(self.import_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_bookmarks)
        toolbar.addWidget(self.export_btn)

        layout.addLayout(toolbar)

        # Tree view
        self.tree_view = QTreeView()
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        self.model = QStandardItemModel(0, 2, self)
        self.model.setHorizontalHeaderLabels(["Name", "URL"])
        self.proxy_model = QSortFilterProxyModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(0)
        self.tree_view.setModel(self.proxy_model)

        layout.addWidget(self.tree_view)

        self.load_bookmarks()

    def load_bookmarks(self):
        self.model.removeRows(0, self.model.rowCount())
        bookmarks = self.db.get_all_bookmarks()
        for url, title, folder in bookmarks:
            name_item = QStandardItem(title or url)
            name_item.setData(url, Qt.UserRole)
            url_item = QStandardItem(url)
            folder_item = QStandardItem(folder or "Default")
            self.model.appendRow([name_item, url_item, folder_item])

        self.tree_view.setColumnWidth(0, 300)
        self.tree_view.setColumnWidth(1, 300)

    def filter_bookmarks(self, text: str):
        self.proxy_model.setFilterRegExp(text)

    def add_bookmark(self):
        url, ok = QInputDialog.getText(self, "Add Bookmark", "Enter URL:")
        if ok and url:
            title, ok2 = QInputDialog.getText(self, "Add Bookmark", "Enter title (optional):")
            folder, ok3 = QInputDialog.getText(self, "Add Bookmark", "Folder name (optional, e.g. 'Bookmarks Bar'):")
            if ok2 and ok3:
                self.db.add_bookmark(url, title, folder if folder else None)
                self.load_bookmarks()

    def import_bookmarks(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Bookmarks", "", "HTML Files (*.html)")
        if file_path:
            try:
                import bs4
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = bs4.BeautifulSoup(f, 'html.parser')
                    for a in soup.find_all('a'):
                        url = a.get('href')
                        title = a.text.strip()
                        if url and title:
                            self.db.add_bookmark(url, title)
                self.load_bookmarks()
            except ImportError:
                QMessageBox.warning(self, "Error", "BeautifulSoup not installed. Cannot import.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import: {e}")

    def export_bookmarks(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Bookmarks", "bookmarks.html", "HTML Files (*.html)")
        if file_path:
            try:
                bookmarks = self.db.get_all_bookmarks()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<html>\n<head>\n<title>Bookmarks</title>\n</head>\n<body>\n")
                    f.write("<h1>Bookmarks</h1>\n<dl>\n")
                    for url, title, folder in bookmarks:
                        if folder:
                            f.write(f"<dt><h3>{folder}</h3></dt>\n")
                        f.write(f"<dt><a href=\"{url}\">{title}</a></dt>\n")
                    f.write("</dl>\n</body>\n</html>")
                QMessageBox.information(self, "Export", "Bookmarks exported successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def show_context_menu(self, pos):
        index = self.tree_view.indexAt(pos)
        if not index.isValid():
            return
        menu = QMenu(self)
        delete_act = menu.addAction("Delete")
        open_act = menu.addAction("Open in New Tab")
        action = menu.exec(self.tree_view.viewport().mapToGlobal(pos))
        if action == delete_act:
            row = self.proxy_model.mapToSource(index).row()
            url = self.model.item(row, 1).text()
            self.db.remove_bookmark(url)
            self.load_bookmarks()
        elif action == open_act:
            url = self.model.item(self.proxy_model.mapToSource(index).row(), 1).text()
            self.parent().tab_widget.new_tab(url)
