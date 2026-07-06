"""
Settings - Full settings dialog with categories
"""

import os
import shutil
import random
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QIcon, QColor, QFont, QPixmap, QDesktopServices
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QLineEdit, QComboBox, QCheckBox, QSpinBox, QTabWidget,
                               QWidget, QFileDialog, QColorDialog, QGroupBox, QFormLayout,
                               QScrollArea, QFrame, QSlider, QListWidget, QListWidgetItem,
                               QApplication, QMessageBox)

from database import Database
from themes import ThemeManager
from utils import resource_path


class SettingsDialog(QDialog):
    """Settings dialog with multiple tabs"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.theme_manager = ThemeManager.instance()
        self.setWindowTitle("Settings")
        self.resize(700, 700)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)

        main_layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                background: transparent;
                border: none;
            }
            QTabBar::tab {
                padding: 8px 15px;
                background: transparent;
                border: none;
                color: palette(text);
            }
            QTabBar::tab:selected {
                background: rgba(255,255,255,0.08);
                border-bottom: 2px solid #0078d4;
            }
        """)

        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "General")

        appearance_tab = self.create_appearance_tab()
        tabs.addTab(appearance_tab, "Appearance")

        privacy_tab = self.create_privacy_tab()
        tabs.addTab(privacy_tab, "Privacy")

        advanced_tab = self.create_advanced_tab()
        tabs.addTab(advanced_tab, "Advanced")

        main_layout.addWidget(tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)

        self.load_settings()

    def create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Startup")
        form = QFormLayout(group)
        self.startup_page_combo = QComboBox()
        self.startup_page_combo.addItems(["Blank Page", "Homepage", "Continue where you left off"])
        form.addRow("On startup:", self.startup_page_combo)

        self.homepage_edit = QLineEdit()
        self.homepage_edit.setPlaceholderText("Enter homepage URL")
        form.addRow("Homepage:", self.homepage_edit)

        layout.addWidget(group)

        group2 = QGroupBox("Search Engine")
        form2 = QFormLayout(group2)
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.addItems(["Google", "DuckDuckGo", "Bing", "Yahoo", "Brave Search"])
        form2.addRow("Default search engine:", self.search_engine_combo)
        layout.addWidget(group2)

        group3 = QGroupBox("Downloads")
        form3 = QFormLayout(group3)
        self.download_path_edit = QLineEdit()
        self.download_path_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_download_folder)
        hbox = QHBoxLayout()
        hbox.addWidget(self.download_path_edit)
        hbox.addWidget(browse_btn)
        form3.addRow("Download location:", hbox)
        layout.addWidget(group3)

        layout.addStretch()
        return widget

    def browse_download_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.download_path_edit.setText(folder)

    def create_appearance_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Theme")
        form = QFormLayout(group)
        self.theme_combo = QComboBox()
        themes = self.theme_manager.get_theme_names()
        self.theme_combo.addItems(themes)
        form.addRow("Theme:", self.theme_combo)

        accent_layout = QHBoxLayout()
        self.accent_color_btn = QPushButton("Choose Color")
        self.accent_color_btn.clicked.connect(self.choose_accent_color)
        self.accent_color_preview = QLabel()
        self.accent_color_preview.setFixedSize(20, 20)
        self.accent_color_preview.setStyleSheet("border: 1px solid #ccc; border-radius: 3px;")
        accent_layout.addWidget(self.accent_color_btn)
        accent_layout.addWidget(self.accent_color_preview)
        form.addRow("Accent color:", accent_layout)

        layout.addWidget(group)

        group2 = QGroupBox("Wallpaper")
        group2.setStyleSheet("""
            QGroupBox {
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: palette(text);
                font-weight: 500;
            }
        """)
        form2 = QFormLayout(group2)

        hbox = QHBoxLayout()
        self.wallpaper_path = QLineEdit()
        self.wallpaper_path.setReadOnly(True)
        wall_btn = QPushButton("Choose File...")
        wall_btn.clicked.connect(self.choose_wallpaper)
        hbox.addWidget(self.wallpaper_path)
        hbox.addWidget(wall_btn)
        form2.addRow("Wallpaper:", hbox)

        self.random_wallpaper_check = QCheckBox("Use random wallpaper on startup")
        form2.addRow(self.random_wallpaper_check)

        slideshow_layout = QHBoxLayout()
        self.slideshow_check = QCheckBox("Enable wallpaper slideshow")
        self.slideshow_check.toggled.connect(self.slideshow_check_toggled)
        slideshow_layout.addWidget(self.slideshow_check)
        self.slideshow_spin = QSpinBox()
        self.slideshow_spin.setRange(1, 60)
        self.slideshow_spin.setValue(5)
        self.slideshow_spin.setEnabled(False)
        slideshow_layout.addWidget(self.slideshow_spin)
        slideshow_layout.addWidget(QLabel("minutes"))
        slideshow_layout.addStretch()
        form2.addRow("Slideshow:", slideshow_layout)

        pexels_layout = QHBoxLayout()
        pexels_label = QLabel("📷 Browse 4K wallpapers:")
        pexels_label.setStyleSheet("color: palette(text);")
        pexels_btn = QPushButton("Open Pexels 4K Wallpapers")
        pexels_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        pexels_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.pexels.com/search/4k%20wallpaper/")))
        pexels_layout.addWidget(pexels_label)
        pexels_layout.addWidget(pexels_btn)
        pexels_layout.addStretch()
        form2.addRow(pexels_layout)

        custom_layout = QHBoxLayout()
        custom_label = QLabel("🎨 Create custom wallpaper:")
        custom_label.setStyleSheet("color: palette(text);")
        custom_btn = QPushButton("Open Custom Wallpaper Generator")
        custom_btn.setStyleSheet("""
            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 5px 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #7C3AED;
            }
        """)
        custom_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://codepen.io/Kavyant-Kumar/pen/EageXvw")))
        custom_layout.addWidget(custom_label)
        custom_layout.addWidget(custom_btn)
        custom_layout.addStretch()
        form2.addRow(custom_layout)

        help_label = QLabel(
            "📖 How to set a custom wallpaper:\n"
            "1. Click \"Open Pexels 4K Wallpapers\" below to browse images.\n"
            "2. Choose a wallpaper you like and download it to your device (right-click/long-press and \"Save image as...\").\n"
            "3. Click the \"Choose File...\" button above and select the downloaded image.\n"
            "4. Your wallpaper will be applied automatically!"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet("""
            QLabel {
                color: palette(text);
                font-size: 12px;
                padding: 10px;
                background: rgba(255,255,255,0.05);
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,0.05);
            }
        """)
        form2.addRow(help_label)

        preview_label = QLabel("No wallpaper selected")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setFixedHeight(120)
        preview_label.setStyleSheet("""
            QLabel {
                border: 1px dashed rgba(255,255,255,0.2);
                border-radius: 8px;
                background: rgba(255,255,255,0.05);
                color: palette(text);
            }
        """)
        self.wallpaper_preview = preview_label
        form2.addRow("Preview:", self.wallpaper_preview)

        layout.addWidget(group2)

        group3 = QGroupBox("Font")
        form3 = QFormLayout(group3)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(9)
        form3.addRow("Font size:", self.font_size_spin)
        layout.addWidget(group3)

        layout.addStretch()
        return widget

    def slideshow_check_toggled(self, checked):
        self.slideshow_spin.setEnabled(checked)

    def choose_accent_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.accent_color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #ccc;")

    def choose_wallpaper(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Wallpaper Image", "",
                                                    "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            wallpaper_dir = os.path.join(os.path.expanduser("~"), ".BeautifulBrowser", "wallpapers")
            os.makedirs(wallpaper_dir, exist_ok=True)
            import time
            ext = os.path.splitext(file_path)[1]
            new_filename = f"wallpaper_{int(time.time())}{ext}"
            dest_path = os.path.join(wallpaper_dir, new_filename)
            try:
                shutil.copy2(file_path, dest_path)
                self.wallpaper_path.setText(dest_path)
                pixmap = QPixmap(dest_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.wallpaper_preview.setPixmap(scaled)
                    self.wallpaper_preview.setText("")
                else:
                    self.wallpaper_preview.setText("Invalid image")
                    QMessageBox.warning(self, "Invalid Image", "The selected file is not a valid image.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to copy wallpaper: {e}")

    def create_privacy_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Privacy")
        form = QFormLayout(group)
        self.clear_cookies_btn = QPushButton("Clear Cookies")
        self.clear_cookies_btn.clicked.connect(self.clear_cookies)
        form.addRow("Cookies:", self.clear_cookies_btn)

        self.clear_cache_btn = QPushButton("Clear Cache")
        self.clear_cache_btn.clicked.connect(self.clear_cache)
        form.addRow("Cache:", self.clear_cache_btn)

        self.tracking_check = QCheckBox("Enable tracking protection")
        form.addRow("Tracking:", self.tracking_check)

        self.popup_check = QCheckBox("Block popups")
        form.addRow("Popups:", self.popup_check)

        # ---- New setting ----
        self.history_editing_check = QCheckBox("Enable history editing (delete/clear)")
        self.history_editing_check.setToolTip("If disabled, history will be view‑only.")
        form.addRow("History:", self.history_editing_check)

        layout.addWidget(group)
        layout.addStretch()
        return widget

    def clear_cookies(self):
        profile = self.parent().tab_widget.current_browser().profile
        cookie_store = profile.cookieStore()
        cookie_store.deleteAllCookies()
        QMessageBox.information(self, "Success", "Cookies cleared successfully!")

    def clear_cache(self):
        profile = self.parent().tab_widget.current_browser().profile
        profile.clearHttpCache()
        QMessageBox.information(self, "Success", "Cache cleared successfully!")

    def create_advanced_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("Developer Options")
        form = QFormLayout(group)
        self.dev_tools_check = QCheckBox("Enable Developer Tools")
        form.addRow("Developer Tools:", self.dev_tools_check)

        self.remote_debug_check = QCheckBox("Enable Remote Debugging")
        form.addRow("Remote Debugging:", self.remote_debug_check)

        layout.addWidget(group)

        reset_btn = QPushButton("Restore Defaults")
        reset_btn.clicked.connect(self.restore_defaults)
        layout.addWidget(reset_btn)

        layout.addStretch()
        return widget

    def load_settings(self):
        self.startup_page_combo.setCurrentIndex(int(self.db.get_setting("startup_page", "0")))
        self.homepage_edit.setText(self.db.get_setting("homepage", "https://www.google.com"))
        search_engine = self.db.get_setting("search_engine", "google")
        search_map = {"google": 0, "duckduckgo": 1, "bing": 2, "yahoo": 3, "brave": 4}
        self.search_engine_combo.setCurrentIndex(search_map.get(search_engine, 0))
        self.download_path_edit.setText(self.db.get_setting("download_folder", os.path.expanduser("~/Downloads")))
        theme = self.db.get_setting("theme", "Light")
        self.theme_combo.setCurrentText(theme)
        accent = self.db.get_setting("accent_color", "#0078d4")
        self.accent_color_preview.setStyleSheet(f"background-color: {accent}; border: 1px solid #ccc;")
        wallpaper = self.db.get_setting("wallpaper", "")
        self.wallpaper_path.setText(wallpaper)
        if wallpaper and os.path.exists(wallpaper):
            pixmap = QPixmap(wallpaper)
            if not pixmap.isNull():
                scaled = pixmap.scaled(200, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.wallpaper_preview.setPixmap(scaled)
                self.wallpaper_preview.setText("")
            else:
                self.wallpaper_preview.setText("Invalid image")
        else:
            self.wallpaper_preview.setText("No wallpaper selected")

        self.random_wallpaper_check.setChecked(self.db.get_setting("random_wallpaper", "false") == "true")
        self.slideshow_check.setChecked(self.db.get_setting("slideshow_enabled", "false") == "true")
        self.slideshow_spin.setValue(int(self.db.get_setting("slideshow_interval", "5")))
        self.slideshow_spin.setEnabled(self.slideshow_check.isChecked())

        self.font_size_spin.setValue(int(self.db.get_setting("font_size", "9")))
        self.tracking_check.setChecked(self.db.get_setting("tracking_protection", "true") == "true")
        self.popup_check.setChecked(self.db.get_setting("block_popups", "true") == "true")
        self.dev_tools_check.setChecked(self.db.get_setting("dev_tools", "false") == "true")
        self.remote_debug_check.setChecked(self.db.get_setting("remote_debug", "false") == "true")
        # ---- Load new setting ----
        self.history_editing_check.setChecked(self.db.get_setting("history_editing", "false") == "true")

    def save_settings(self):
        self.db.set_setting("startup_page", str(self.startup_page_combo.currentIndex()))
        self.db.set_setting("homepage", self.homepage_edit.text())
        search_map = {0: "google", 1: "duckduckgo", 2: "bing", 3: "yahoo", 4: "brave"}
        self.db.set_setting("search_engine", search_map.get(self.search_engine_combo.currentIndex(), "google"))
        self.db.set_setting("download_folder", self.download_path_edit.text())
        self.db.set_setting("theme", self.theme_combo.currentText())
        color = self.accent_color_preview.styleSheet().split("background-color: ")[1].split(";")[0]
        self.db.set_setting("accent_color", color)
        self.db.set_setting("wallpaper", self.wallpaper_path.text())
        self.db.set_setting("random_wallpaper", "true" if self.random_wallpaper_check.isChecked() else "false")
        self.db.set_setting("slideshow_enabled", "true" if self.slideshow_check.isChecked() else "false")
        self.db.set_setting("slideshow_interval", str(self.slideshow_spin.value()))
        self.db.set_setting("font_size", str(self.font_size_spin.value()))
        self.db.set_setting("tracking_protection", "true" if self.tracking_check.isChecked() else "false")
        self.db.set_setting("block_popups", "true" if self.popup_check.isChecked() else "false")
        self.db.set_setting("dev_tools", "true" if self.dev_tools_check.isChecked() else "false")
        self.db.set_setting("remote_debug", "true" if self.remote_debug_check.isChecked() else "false")
        # ---- Save new setting ----
        self.db.set_setting("history_editing", "true" if self.history_editing_check.isChecked() else "false")

        self.theme_manager.load_theme(self.theme_combo.currentText())
        self.parent().apply_theme_and_wallpaper()
        font = QFont("Segoe UI", self.font_size_spin.value())
        QApplication.setFont(font)

    def accept(self):
        self.save_settings()
        super().accept()

    def restore_defaults(self):
        reply = QMessageBox.question(self, "Restore Defaults",
                                     "Are you sure you want to restore all settings to default?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.reset_settings()
            self.load_settings()
            self.theme_manager.load_theme("Light")
            self.parent().apply_theme_and_wallpaper()
            QMessageBox.information(self, "Success", "Settings restored to defaults!")
