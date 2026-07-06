"""
Toolbar - Navigation bar with address, buttons, and progress
"""

from PySide6.QtCore import Qt, QUrl, Signal, Slot, QTimer
from PySide6.QtGui import QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLineEdit, QProgressBar,
                               QLabel, QToolButton, QStyle, QComboBox, QMenu)

from browser import Browser
from database import Database
from utils import resource_path, is_url
from widgets import AnimatedButton


class AddressBar(QLineEdit):
    """Custom address bar with lock icon and autocomplete"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Search or enter address...")
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 20px;
                padding: 5px 10px;
                color: palette(text);
                font-size: 14px;
                selection-background-color: #0078d4;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
                background: rgba(255,255,255,0.15);
            }
        """)
        self.returnPressed.connect(self.on_return_pressed)
        self.lock_icon = QLabel(self)
        self.lock_icon.setPixmap(QIcon(resource_path("resources/icons/lock.png")).pixmap(16, 16))
        self.lock_icon.hide()
        self.setTextMargins(25, 0, 0, 0)

    def resizeEvent(self, event):
        self.lock_icon.move(5, (self.height() - 16) // 2)
        super().resizeEvent(event)

    def set_url(self, url: str):
        self.setText(url)
        if url.startswith("https://"):
            self.lock_icon.show()
        else:
            self.lock_icon.hide()

    def on_return_pressed(self):
        text = self.text().strip()
        if text:
            self.parent().load_url(text)


class Toolbar(QWidget):
    """Main toolbar with navigation buttons, address bar, and extras"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.browser: Browser = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)

        # Back
        self.back_btn = AnimatedButton("◀", self)
        self.back_btn.setToolTip("Back")
        self.back_btn.setFixedSize(30, 30)
        self.back_btn.setStyleSheet(self.button_style())
        self.back_btn.clicked.connect(self.go_back)
        layout.addWidget(self.back_btn)

        # Forward
        self.forward_btn = AnimatedButton("▶", self)
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.setFixedSize(30, 30)
        self.forward_btn.setStyleSheet(self.button_style())
        self.forward_btn.clicked.connect(self.go_forward)
        layout.addWidget(self.forward_btn)

        # Refresh/Stop
        self.refresh_stop_btn = AnimatedButton("⟳", self)
        self.refresh_stop_btn.setToolTip("Refresh")
        self.refresh_stop_btn.setFixedSize(30, 30)
        self.refresh_stop_btn.setStyleSheet(self.button_style())
        self.refresh_stop_btn.clicked.connect(self.toggle_refresh_stop)
        layout.addWidget(self.refresh_stop_btn)

        # Home
        self.home_btn = AnimatedButton("🏠", self)
        self.home_btn.setToolTip("Home")
        self.home_btn.setFixedSize(30, 30)
        self.home_btn.setStyleSheet(self.button_style())
        self.home_btn.clicked.connect(self.go_home)
        layout.addWidget(self.home_btn)

        # Address bar
        self.address_bar = AddressBar(self)
        layout.addWidget(self.address_bar, 1)

        # Bookmark button
        self.bookmark_btn = AnimatedButton("☆", self)
        self.bookmark_btn.setToolTip("Bookmark this page")
        self.bookmark_btn.setFixedSize(30, 30)
        self.bookmark_btn.setStyleSheet(self.button_style())
        self.bookmark_btn.clicked.connect(self.toggle_bookmark)
        layout.addWidget(self.bookmark_btn)

        # Menu button
        self.menu_btn = AnimatedButton("⋮", self)
        self.menu_btn.setToolTip("Menu")
        self.menu_btn.setFixedSize(30, 30)
        self.menu_btn.setStyleSheet(self.button_style())
        self.menu_btn.clicked.connect(self.show_main_menu)
        layout.addWidget(self.menu_btn)

    def button_style(self) -> str:
        return """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 15px;
                color: palette(text);
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.2);
            }
        """

    def set_browser(self, browser: Browser):
        """Associate toolbar with a browser instance"""
        if self.browser:
            self.browser.url_changed.disconnect(self.on_url_changed)
            self.browser.load_progress.disconnect(self.on_load_progress)
            self.browser.load_finished.disconnect(self.on_load_finished)
        self.browser = browser
        if browser:
            browser.url_changed.connect(self.on_url_changed)
            browser.load_progress.connect(self.on_load_progress)
            browser.load_finished.connect(self.on_load_finished)
            self.on_url_changed(browser.get_current_url())

    def on_url_changed(self, url: str):
        self.address_bar.set_url(url)
        if self.db and self.browser:
            is_bookmarked = self.db.is_bookmarked(url)
            if is_bookmarked:
                self.bookmark_btn.setText("★")
                self.bookmark_btn.setToolTip("Remove bookmark")
            else:
                self.bookmark_btn.setText("☆")
                self.bookmark_btn.setToolTip("Bookmark this page")

    def on_load_progress(self, progress: int):
        if progress < 100:
            self.refresh_stop_btn.setText("✕")
            self.refresh_stop_btn.setToolTip("Stop")
        else:
            self.refresh_stop_btn.setText("⟳")
            self.refresh_stop_btn.setToolTip("Refresh")

    def on_load_finished(self, ok: bool):
        self.refresh_stop_btn.setText("⟳")
        self.refresh_stop_btn.setToolTip("Refresh")

    def load_url(self, url: str):
        if self.browser:
            self.browser.load(url)

    def go_back(self):
        if self.browser:
            self.browser.go_back()

    def go_forward(self):
        if self.browser:
            self.browser.go_forward()

    def toggle_refresh_stop(self):
        if self.browser:
            if self.browser.is_loading():
                self.browser.stop()
            else:
                self.browser.reload()

    def go_home(self):
        if self.browser:
            self.browser.home()

    def toggle_bookmark(self):
        if self.browser and self.db:
            url = self.browser.get_current_url()
            title = self.browser.get_current_title()
            if self.db.is_bookmarked(url):
                self.db.remove_bookmark(url)
                self.bookmark_btn.setText("☆")
                self.bookmark_btn.setToolTip("Bookmark this page")
            else:
                self.db.add_bookmark(url, title)
                self.bookmark_btn.setText("★")
                self.bookmark_btn.setToolTip("Remove bookmark")

    def show_main_menu(self):
        menu = QMenu(self)
        menu.addAction("New Tab", lambda: self.window().tab_widget.new_tab())
        menu.addAction("New Incognito Tab", lambda: self.window().tab_widget.new_tab(incognito=True))
        menu.addSeparator()
        menu.addAction("History", lambda: self.window().on_sidebar_page_selected("history"))
        menu.addAction("Bookmarks", lambda: self.window().on_sidebar_page_selected("bookmarks"))
        menu.addAction("Downloads", lambda: self.window().on_sidebar_page_selected("downloads"))
        menu.addSeparator()
        menu.addAction("Zoom In", lambda: self.browser and self.browser.zoom_in())
        menu.addAction("Zoom Out", lambda: self.browser and self.browser.zoom_out())
        menu.addAction("Reset Zoom", lambda: self.browser and self.browser.zoom_reset())
        menu.addSeparator()
        menu.addAction("Settings", lambda: self.window().on_sidebar_page_selected("settings"))
        menu.addAction("About", lambda: self.window().on_sidebar_page_selected("about"))
        menu.exec(self.mapToGlobal(self.menu_btn.pos()) + self.menu_btn.rect().bottomLeft())
