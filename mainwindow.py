"""
MainWindow - Frameless main window with sidebar, tabs, navigation, and animations
"""

import os
import sys
import base64
import random
from typing import Optional, List, Dict, Any
from datetime import datetime
import calendar

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize, Signal, Slot, QTimer, QDateTime
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QLinearGradient, QPixmap, QIcon, QAction, QKeySequence
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QStackedWidget, QFrame, QSpacerItem, QSizePolicy, QMenu, QSystemTrayIcon,
                               QApplication, QStyle, QScrollArea, QGridLayout, QGroupBox, QLineEdit,
                               QCalendarWidget)
from PySide6.QtWebEngineWidgets import QWebEngineView

from tabwidget import TabWidget
from toolbar import Toolbar
from sidebar import Sidebar
from settings import SettingsDialog
from history import HistoryDialog
from bookmarks import BookmarksDialog
from downloads import DownloadsDialog
from database import Database
from themes import ThemeManager
from utils import resource_path, is_url
from widgets import AnimatedButton, GlassFrame, RoundedWidget


class MainWindow(QMainWindow):
    """Main application window with frameless design and modern UI"""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.theme_manager = ThemeManager.instance()
        self.dragging = False
        self.drag_position = QPoint()
        self.incognito = False
        self.slideshow_timer = QTimer()
        self.slideshow_timer.timeout.connect(self.rotate_wallpaper)

        # Remove window frame
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Set size
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

        # Central widget
        central = QWidget(self)
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar (custom)
        self.title_bar = self.create_title_bar()
        main_layout.addWidget(self.title_bar)

        # Main content: sidebar + stacked widget
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self.db, self)
        self.sidebar.page_selected.connect(self.on_sidebar_page_selected)
        content_layout.addWidget(self.sidebar)

        # Stacked widget for browser and other pages (dashboard, etc.)
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("stackedWidget")

        # Browser tab widget
        self.tab_widget = TabWidget(db, self)
        self.tab_widget.tab_count_changed.connect(self.update_title_bar)
        self.stacked_widget.addWidget(self.tab_widget)  # index 0

        # Dashboard
        self.dashboard_widget = self.create_dashboard()
        self.stacked_widget.addWidget(self.dashboard_widget)  # index 1

        content_layout.addWidget(self.stacked_widget, 1)

        # Add content widget to main layout
        main_layout.addWidget(content_widget, 1)

        # --- New Features ---
        # Bookmark bar (if enabled)
        self.bookmark_bar = self.create_bookmark_bar()
        main_layout.addWidget(self.bookmark_bar)

        # Status bar (for link preview)
        self.status_bar = QLabel("")
        self.status_bar.setStyleSheet("""
            QLabel {
                color: palette(text);
                font-size: 12px;
                padding: 2px 10px;
                background: rgba(0,0,0,0.03);
                border-top: 1px solid rgba(255,255,255,0.05);
            }
        """)
        main_layout.addWidget(self.status_bar)

        # Apply theme + wallpaper
        self.apply_theme_and_wallpaper()

        # Start slideshow if enabled
        self.setup_slideshow()

        # Start clock timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        self.update_clock()

        # Restore session
        self.restore_session()

        # Show bookmark bar if enabled
        self.update_bookmark_bar_visibility()

    def create_title_bar(self) -> QWidget:
        """Create custom title bar with window controls and theme toggle"""
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            #titleBar {
                background: rgba(0,0,0,0.02);
                backdrop-filter: blur(12px);
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
        """)

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 10, 0)

        # App icon and title
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(resource_path("resources/icons/app_icon.png")).pixmap(20, 20))
        layout.addWidget(icon_label)

        self.title_label = QLabel("BeautifulBrowser")
        self.title_label.setStyleSheet("color: palette(text); font-weight: 500;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Clock label (real-time)
        self.clock_label = QLabel("00:00:00 | Mon, Jan 01, 2000")
        self.clock_label.setStyleSheet("""
            QLabel {
                color: palette(text);
                font-size: 12px;
                font-weight: 400;
                padding: 0 10px;
                opacity: 0.8;
            }
        """)
        layout.addWidget(self.clock_label)

        # Theme toggle button
        self.theme_toggle_btn = AnimatedButton("🌙")
        self.theme_toggle_btn.setFixedSize(30, 30)
        self.theme_toggle_btn.setToolTip("Toggle Theme (Dark/Light)")
        self.theme_toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: palette(text);
                border: none;
                border-radius: 15px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        self.theme_toggle_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_toggle_btn)

        # Window controls
        self.min_button = AnimatedButton("-")
        self.min_button.setFixedSize(30, 30)
        self.min_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: palette(text);
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        self.min_button.clicked.connect(self.showMinimized)

        self.max_button = AnimatedButton("□")
        self.max_button.setFixedSize(30, 30)
        self.max_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: palette(text);
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        self.max_button.clicked.connect(self.toggle_maximize)

        self.close_button = AnimatedButton("✕")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: palette(text);
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #e81123;
                color: white;
            }
        """)
        self.close_button.clicked.connect(self.close)

        layout.addWidget(self.min_button)
        layout.addWidget(self.max_button)
        layout.addWidget(self.close_button)

        title_bar.mousePressEvent = self.title_bar_mouse_press
        title_bar.mouseMoveEvent = self.title_bar_mouse_move
        title_bar.mouseDoubleClickEvent = lambda e: self.toggle_maximize()

        return title_bar

    def update_clock(self):
        now = QDateTime.currentDateTime()
        time_str = now.toString("hh:mm:ss")
        date_str = now.toString("ddd, MMM dd, yyyy")
        self.clock_label.setText(f"{time_str} | {date_str}")

    def toggle_theme(self):
        current = self.theme_manager.current_theme
        new_theme = "Dark" if current == "Light" else "Light"
        self.theme_manager.load_theme(new_theme)
        self.apply_theme_and_wallpaper()
        if new_theme == "Dark":
            self.theme_toggle_btn.setText("🌙")
            self.theme_toggle_btn.setToolTip("Switch to Light Theme")
        else:
            self.theme_toggle_btn.setText("☀️")
            self.theme_toggle_btn.setToolTip("Switch to Dark Theme")

    def title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def title_bar_mouse_move(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def title_bar_mouse_release(self, event):
        self.dragging = False

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def update_title_bar(self, count: int):
        active = self.tab_widget.current_browser()
        if active:
            title = active.get_current_title() or "New Tab"
            self.title_label.setText(f"{title} - BeautifulBrowser ({count} tabs)")
        else:
            self.title_label.setText(f"BeautifulBrowser ({count} tabs)")

    def apply_theme_and_wallpaper(self):
        style = self.theme_manager.get_current_stylesheet()
        self.setStyleSheet(style)
        bg_color = self.theme_manager.get_color("background")
        self.title_bar.setStyleSheet(f"""
            #titleBar {{
                background: {bg_color};
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }}
        """)
        self.set_wallpaper()
        if self.theme_manager.current_theme == "Dark":
            self.theme_toggle_btn.setText("🌙")
            self.theme_toggle_btn.setToolTip("Switch to Light Theme")
        else:
            self.theme_toggle_btn.setText("☀️")
            self.theme_toggle_btn.setToolTip("Switch to Dark Theme")
        # Update bookmark bar style
        self.update_bookmark_bar_visibility()

    def set_wallpaper(self):
        random_wallpaper = self.db.get_setting("random_wallpaper", "false") == "true"
        wallpaper_path = self.db.get_setting("wallpaper", "")
        if random_wallpaper:
            wallpaper_path = self.get_random_wallpaper()
            if wallpaper_path:
                self.db.set_setting("wallpaper", wallpaper_path)

        if wallpaper_path and os.path.exists(wallpaper_path):
            wallpaper_url = wallpaper_path.replace('\\', '/')
            self.centralWidget().setStyleSheet(f"""
                #centralWidget {{
                    background-image: url("{wallpaper_url}");
                    background-repeat: no-repeat;
                    background-position: center;
                    background-size: cover;
                }}
            """)
        else:
            self.centralWidget().setStyleSheet("")

    def get_random_wallpaper(self):
        wallpaper_dir = os.path.join(os.path.expanduser("~"), ".BeautifulBrowser", "wallpapers")
        if os.path.exists(wallpaper_dir) and os.listdir(wallpaper_dir):
            images = [f for f in os.listdir(wallpaper_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]
            if images:
                return os.path.join(wallpaper_dir, random.choice(images))
        predefined = [
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1920&q=80",
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=80",
            "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1920&q=80",
            "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1920&q=80",
            "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1920&q=80",
            "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1920&q=80",
            "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920&q=80",
        ]
        return random.choice(predefined)

    def setup_slideshow(self):
        slideshow_enabled = self.db.get_setting("slideshow_enabled", "false") == "true"
        if slideshow_enabled:
            interval = int(self.db.get_setting("slideshow_interval", "5")) * 60000
            self.slideshow_timer.start(interval)
        else:
            self.slideshow_timer.stop()

    def rotate_wallpaper(self):
        random_path = self.get_random_wallpaper()
        if random_path:
            self.db.set_setting("wallpaper", random_path)
            self.set_wallpaper()

    def create_bookmark_bar(self) -> QWidget:
        """Create bookmark bar showing bookmarks from 'Bookmarks Bar' folder"""
        bar = QWidget()
        bar.setObjectName("bookmarkBar")
        bar.setFixedHeight(30)
        bar.setStyleSheet("""
            #bookmarkBar {
                background: rgba(255,255,255,0.03);
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
        """)
        bar_layout = QHBoxLayout(bar)
        bar_layout.setContentsMargins(5, 2, 5, 2)
        bar_layout.setSpacing(4)

        # Load bookmarks from "Bookmarks Bar" folder
        bookmarks = self.db.get_bookmarks_by_folder("Bookmarks Bar")
        for url, title in bookmarks:
            btn = QPushButton(title or url)
            btn.setFlat(True)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: palette(text);
                    border: none;
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.1);
                }
            """)
            btn.clicked.connect(lambda checked, u=url: self.load_url_in_new_tab(u))
            bar_layout.addWidget(btn)

        bar_layout.addStretch()
        bar.hide()  # Initially hidden, show based on setting
        return bar

    def update_bookmark_bar_visibility(self):
        """Show/hide bookmark bar based on setting"""
        visible = self.db.get_setting("show_bookmark_bar", "false") == "true"
        self.bookmark_bar.setVisible(visible)

    def create_dashboard(self) -> QWidget:
        from widgets import GlassFrame

        dashboard = QWidget()
        main_layout = QVBoxLayout(dashboard)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Top: Welcome + Search
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        welcome = QLabel("✨ Welcome to BeautifulBrowser")
        welcome.setStyleSheet("font-size: 28px; font-weight: 300; color: palette(text);")
        top_layout.addWidget(welcome)

        search_frame = GlassFrame()
        search_frame.setStyleSheet("""
            GlassFrame {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 25px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 5, 10, 5)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 18px;")
        search_layout.addWidget(search_icon)

        self.dashboard_search = QLineEdit()
        self.dashboard_search.setPlaceholderText("Search or enter address...")
        self.dashboard_search.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: palette(text);
                font-size: 14px;
                padding: 5px 0;
            }
        """)
        self.dashboard_search.returnPressed.connect(self.dashboard_search_execute)
        search_layout.addWidget(self.dashboard_search)

        search_btn = QPushButton("Go")
        search_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        search_btn.clicked.connect(self.dashboard_search_execute)
        search_layout.addWidget(search_btn)

        top_layout.addWidget(search_frame)
        main_layout.addWidget(top_widget)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(20)

        # ---------- Categories ----------
        categories = [
            ("🚀 Quick Links", [
                ("YouTube", "https://www.youtube.com"),
                ("Aura Lab: Cares & Laughs 2", "https://codepen.io/Kavyant-Kumar/pen/dPOXwmY"),
                ("Aura Lab: Cares & Laughs 1", "https://codepen.io/Kavyant-Kumar/pen/dPGJPKj"),
                ("Instagram", "https://instagram.com/kavyanthub"),
                ("Facebook", "https://facebook.com/profile.php?id=61586003535719"),
                ("GitHub", "https://github.com/Kiik913"),
                ("Discord", "https://discord.com/channels/1505857480503197696/1505857672597999736"),
            ]),
            ("📅 Calendar", []),       # special – interactive HTML calendar
            ("🌤️ Weather", []),       # special – auto‑location weather
            ("🔍 Main Google Apps", [
                ("Google Account", "https://myaccount.google.com"),
                ("Google Search", "https://www.google.com"),
                ("Gmail", "https://mail.google.com"),
                ("Google Maps", "https://maps.google.com"),
                ("Google Play Store", "https://play.google.com"),
                ("Google News", "https://news.google.com"),
                ("Google Contacts", "https://contacts.google.com"),
                ("Google Drive", "https://drive.google.com"),
                ("Google Calendar", "https://calendar.google.com"),
                ("Google Translate", "https://translate.google.com"),
                ("Google Photos", "https://photos.google.com"),
                ("Google Meet", "https://meet.google.com"),
                ("Google Chat", "https://chat.google.com"),
                ("Google Shopping", "https://shopping.google.com"),
                ("Google Finance", "https://www.google.com/finance"),
                ("Google Docs", "https://docs.google.com/document"),
                ("Google Sheets", "https://docs.google.com/spreadsheets"),
                ("Google Slides", "https://docs.google.com/presentation"),
                ("Google Books", "https://books.google.com"),
                ("Google Keep", "https://keep.google.com"),
                ("Google Forms", "https://forms.google.com"),
                ("Google Sites", "https://sites.google.com"),
                ("Google Earth", "https://earth.google.com"),
                ("Google Flights", "https://flights.google.com"),
                ("Google Arts & Culture", "https://artsandculture.google.com"),
            ]),
            ("💼 Google Workspace (India URLs)", [
                ("Gmail (Workspace)", "https://workspace.google.com/intl/en_in/products/gmail"),
                ("Drive (Workspace)", "https://workspace.google.com/intl/en_in/products/drive"),
                ("Meet (Workspace)", "https://workspace.google.com/intl/en_in/products/meet"),
                ("Calendar (Workspace)", "https://workspace.google.com/intl/en_in/products/calendar"),
                ("Chat (Workspace)", "https://workspace.google.com/intl/en_in/products/chat"),
                ("Gemini (Workspace AI)", "https://workspace.google.com/intl/en_in/solutions/ai/"),
                ("Docs (Workspace)", "https://workspace.google.com/intl/en_in/products/docs"),
                ("Sheets (Workspace)", "https://workspace.google.com/intl/en_in/products/sheets"),
                ("Slides (Workspace)", "https://workspace.google.com/intl/en_in/products/slides"),
                ("Vids (Workspace)", "https://workspace.google.com/intl/en_in/products/vids"),
                ("Keep (Workspace)", "https://workspace.google.com/intl/en_in/products/keep"),
                ("Sites (Workspace)", "https://workspace.google.com/intl/en_in/products/sites"),
                ("Forms (Workspace)", "https://workspace.google.com/intl/en_in/products/forms"),
                ("Tasks (Workspace)", "https://workspace.google.com/intl/en_in/products/tasks/"),
                ("NotebookLM (Workspace)", "https://workspace.google.com/intl/en_in/products/notebooklm"),
                ("AppSheet (Workspace)", "https://about.appsheet.com/home/"),
                ("Workspace Marketplace", "https://workspace.google.com/marketplace?pann=ogb"),
            ]),
            ("🤖 AI & Labs", [
                ("Google Gemini", "https://gemini.google.com"),
                ("Google AI Studio", "https://ai.google.dev/"),
                ("NotebookLM", "https://notebooklm.google"),
                ("Google Labs", "https://labs.google/"),
            ]),
            ("🎮 Hidden & Fun", [
                ("Google Fonts", "https://fonts.google.com"),
                ("Material Design", "https://m3.material.io"),
                ("Google Open Source", "https://opensource.google"),
                ("Google Search Console", "https://search.google.com/search-console"),
                ("Blogger", "https://www.blogger.com/features"),
                ("elgooG (Google Easter Eggs)", "https://elgoog.im/"),
            ]),
            ("📂 Official Directories", [
                ("All Google Products Directory", "https://about.google/products/"),
                ("Developer Products Directory", "https://developers.google.com/products"),
            ]),
            ("🖼️ Predefined Wallpapers", [
                ("🌄 Mountain Sunset", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1920&q=80"),
                ("🌊 Ocean Waves", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=80"),
                ("🌲 Forest Path", "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1920&q=80"),
                ("🏔️ Mountain Lake", "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1920&q=80"),
                ("🌅 Golden Hour", "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1920&q=80"),
                ("🌌 Starry Night", "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1920&q=80"),
                ("🌸 Cherry Blossom", "https://images.unsplash.com/photo-1522383225653-ed111181a951?w=1920&q=80"),
                ("🌴 Tropical Beach", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1920&q=80"),
            ]),
        ]

        for category_name, links in categories:
            if category_name == "📅 Calendar":
                # ---- Interactive HTML Calendar with independent month/year dropdowns ----
                group = QGroupBox("📅 Calendar")
                group.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid rgba(255,255,255,0.06);
                        border-radius: 16px;
                        margin-top: 10px;
                        padding-top: 15px;
                        background: rgba(255,255,255,0.03);
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 8px;
                        color: palette(text);
                        font-weight: 500;
                    }
                """)
                cal_layout = QVBoxLayout(group)
                cal_layout.setContentsMargins(10, 10, 10, 10)

                now = datetime.now()
                current_month = now.month - 1  # JS months are 0-based
                current_year = now.year

                # Generate year options from 1900 to 9999 (max)
                year_options = ""
                for y in range(1900, 10000):
                    selected = "selected" if y == current_year else ""
                    year_options += f'<option value="{y}" {selected}>{y}</option>'

                calendar_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 0; background: transparent; }}
                    .calendar {{
                        max-width: 500px;
                        margin: 0 auto;
                        background: rgba(255,255,255,0.05);
                        border-radius: 16px;
                        padding: 15px;
                        backdrop-filter: blur(10px);
                        color: palette(text);
                    }}
                    .header {{
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 0 5px 15px 5px;
                    }}
                    .nav-arrow {{
                        font-size: 24px;
                        cursor: pointer;
                        padding: 0 10px;
                        user-select: none;
                        transition: 0.2s;
                    }}
                    .nav-arrow:hover {{
                        background: rgba(255,255,255,0.1);
                        border-radius: 8px;
                    }}
                    .month-year {{
                        display: flex;
                        gap: 8px;
                        align-items: center;
                    }}
                    .month-year select {{
                        background: rgba(255,255,255,0.1);
                        border: 1px solid rgba(255,255,255,0.15);
                        border-radius: 6px;
                        padding: 4px 8px;
                        color: palette(text);
                        font-size: 16px;
                        font-weight: 500;
                        outline: none;
                    }}
                    .month-year select:hover {{
                        background: rgba(255,255,255,0.2);
                    }}
                    .weekdays {{
                        display: grid;
                        grid-template-columns: repeat(7, 1fr);
                        text-align: center;
                        font-weight: 600;
                        font-size: 14px;
                        color: palette(text);
                        opacity: 0.7;
                        margin-bottom: 8px;
                    }}
                    .days {{
                        display: grid;
                        grid-template-columns: repeat(7, 1fr);
                        gap: 6px;
                    }}
                    .day {{
                        text-align: center;
                        padding: 10px 0;
                        border-radius: 10px;
                        font-size: 15px;
                        background: rgba(255,255,255,0.04);
                        transition: 0.2s;
                        cursor: default;
                    }}
                    .day:hover {{
                        background: rgba(255,255,255,0.12);
                    }}
                    .other-month {{
                        opacity: 0.3;
                    }}
                    .today {{
                        background: #0078d4 !important;
                        color: white !important;
                        font-weight: 600;
                        box-shadow: 0 4px 15px rgba(0,120,212,0.3);
                    }}
                    .today:hover {{
                        background: #106ebe !important;
                    }}
                    .weekend {{
                        color: #e74c3c;
                    }}
                    @media (prefers-color-scheme: dark) {{
                        .calendar {{ background: rgba(0,0,0,0.2); }}
                        .day {{ background: rgba(255,255,255,0.03); }}
                        .month-year select {{
                            background: rgba(255,255,255,0.08);
                            color: #eee;
                        }}
                    }}
                </style>
                </head>
                <body>
                <div class="calendar" id="calendar">
                    <div class="header">
                        <span class="nav-arrow" onclick="changeMonth(-1)">‹</span>
                        <span class="month-year">
                            <select id="monthSelect" onchange="changeMonthYear()">
                                <option value="0">January</option>
                                <option value="1">February</option>
                                <option value="2">March</option>
                                <option value="3">April</option>
                                <option value="4">May</option>
                                <option value="5">June</option>
                                <option value="6">July</option>
                                <option value="7">August</option>
                                <option value="8">September</option>
                                <option value="9">October</option>
                                <option value="10">November</option>
                                <option value="11">December</option>
                            </select>
                            <select id="yearSelect" onchange="changeMonthYear()">
                                {year_options}
                            </select>
                        </span>
                        <span class="nav-arrow" onclick="changeMonth(1)">›</span>
                    </div>
                    <div class="weekdays">
                        <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span>
                    </div>
                    <div class="days" id="daysContainer"></div>
                </div>
                <script>
                    let currentMonth = {current_month};
                    let currentYear = {current_year};

                    function renderCalendar(month, year) {{
                        // Update selectors
                        document.getElementById('monthSelect').value = month;
                        document.getElementById('yearSelect').value = year;

                        const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];
                        // Optionally update a title (but we use selectors)

                        const firstDay = new Date(year, month, 1);
                        const startDay = firstDay.getDay();
                        const start = (startDay === 0) ? 6 : startDay - 1;
                        const daysInMonth = new Date(year, month + 1, 0).getDate();
                        const daysInPrevMonth = new Date(year, month, 0).getDate();

                        let html = '';
                        for (let i = start - 1; i >= 0; i--) {{
                            const day = daysInPrevMonth - i;
                            html += `<span class="day other-month">${{day}}</span>`;
                        }}
                        const today = new Date();
                        const todayDay = today.getDate();
                        const todayMonth = today.getMonth();
                        const todayYear = today.getFullYear();
                        for (let d = 1; d <= daysInMonth; d++) {{
                            let cls = 'day';
                            if (d === todayDay && month === todayMonth && year === todayYear) {{
                                cls += ' today';
                            }}
                            const date = new Date(year, month, d);
                            const dow = date.getDay();
                            if (dow === 0 || dow === 6) {{
                                cls += ' weekend';
                            }}
                            html += `<span class="${{cls}}">${{d}}</span>`;
                        }}
                        const totalCells = start + daysInMonth;
                        const remaining = (totalCells % 7 === 0) ? 0 : 7 - (totalCells % 7);
                        for (let d = 1; d <= remaining; d++) {{
                            html += `<span class="day other-month">${{d}}</span>`;
                        }}
                        document.getElementById('daysContainer').innerHTML = html;
                    }}

                    function changeMonth(delta) {{
                        currentMonth += delta;
                        if (currentMonth < 0) {{
                            currentMonth = 11;
                            currentYear--;
                        }} else if (currentMonth > 11) {{
                            currentMonth = 0;
                            currentYear++;
                        }}
                        renderCalendar(currentMonth, currentYear);
                    }}

                    function changeMonthYear() {{
                        currentMonth = parseInt(document.getElementById('monthSelect').value);
                        currentYear = parseInt(document.getElementById('yearSelect').value);
                        renderCalendar(currentMonth, currentYear);
                    }}

                    renderCalendar(currentMonth, currentYear);
                </script>
                </body>
                </html>
                """

                cal_view = QWebEngineView()
                cal_view.setHtml(calendar_html)
                cal_view.setMinimumHeight(300)
                cal_view.setMaximumWidth(550)
                cal_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                cal_view.setStyleSheet("background: transparent; border: none;")

                cal_layout.addWidget(cal_view, alignment=Qt.AlignCenter)
                scroll_layout.addWidget(group)

            elif category_name == "🌤️ Weather":
                # ---- Auto‑location Weather (uses your IP) ----
                group = QGroupBox("🌤️ Weather")
                group.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid rgba(255,255,255,0.06);
                        border-radius: 16px;
                        margin-top: 10px;
                        padding-top: 15px;
                        background: rgba(255,255,255,0.03);
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 8px;
                        color: palette(text);
                        font-weight: 500;
                    }
                """)
                weather_layout = QVBoxLayout(group)
                weather_layout.setContentsMargins(10, 10, 10, 10)

                # New weather HTML – IP‑based auto‑detection
                weather_html = """
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body { margin: 0; padding: 0; background: transparent; font-family: 'Segoe UI', sans-serif; }
                        .weather-card {
                            max-width: 500px;
                            margin: 0 auto;
                            background: rgba(255,255,255,0.05);
                            border-radius: 16px;
                            padding: 20px;
                            text-align: center;
                            backdrop-filter: blur(10px);
                            color: palette(text);
                        }
                        .location { font-size: 20px; font-weight: 600; margin-bottom: 8px; }
                        .temp { font-size: 48px; font-weight: 300; }
                        .condition { font-size: 18px; opacity: 0.8; margin-top: 4px; }
                        .details { display: flex; justify-content: center; gap: 30px; margin-top: 12px; font-size: 14px; opacity: 0.7; }
                        .detail-item { display: flex; align-items: center; gap: 6px; }
                        @media (prefers-color-scheme: dark) {
                            .weather-card { background: rgba(0,0,0,0.2); }
                        }
                    </style>
                </head>
                <body>
                    <div class="weather-card">
                        <div class="location" id="location">📍 Detecting your location...</div>
                        <div class="temp" id="temp">--°C</div>
                        <div class="condition" id="condition">Loading weather...</div>
                        <div class="details">
                            <span class="detail-item">💨 <span id="wind">-- km/h</span></span>
                            <span class="detail-item">💧 <span id="humidity">--%</span></span>
                        </div>
                    </div>
                    <script>
                        // Uses the IP‑based endpoint – no city needed
                        fetch('https://wttr.in?format=j1')
                            .then(res => res.json())
                            .then(data => {
                                const current = data.current_condition[0];
                                const loc = data.nearest_area[0];
                                const city = loc.areaName[0].value;
                                const country = loc.country[0].value;
                                document.getElementById('location').textContent = `📍 ${city}, ${country}`;
                                document.getElementById('temp').textContent = current.temp_C + '°C';
                                document.getElementById('condition').textContent = current.weatherDesc[0].value;
                                const wind = current.windspeedKmph || current.windSpeedKmph || '--';
                                document.getElementById('wind').textContent = wind + ' km/h';
                                document.getElementById('humidity').textContent = (current.humidity || '--') + '%';
                            })
                            .catch(() => {
                                document.getElementById('location').textContent = '📍 Unable to detect location';
                                document.getElementById('condition').textContent = 'Please try again later';
                            });
                    </script>
                </body>
                </html>
                """

                weather_view = QWebEngineView()
                weather_view.setHtml(weather_html)
                weather_view.setMinimumHeight(200)
                weather_view.setMaximumWidth(550)
                weather_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                weather_view.setStyleSheet("background: transparent; border: none;")

                weather_layout.addWidget(weather_view, alignment=Qt.AlignCenter)
                scroll_layout.addWidget(group)

            else:
                # ---- Normal link group ----
                group = QGroupBox(category_name)
                group.setStyleSheet("""
                    QGroupBox {
                        border: 1px solid rgba(255,255,255,0.06);
                        border-radius: 12px;
                        margin-top: 10px;
                        padding-top: 10px;
                        background: rgba(255,255,255,0.03);
                    }
                    QGroupBox::title {
                        subcontrol-origin: margin;
                        left: 10px;
                        padding: 0 8px;
                        color: palette(text);
                        font-weight: 500;
                    }
                """)
                group_layout = QGridLayout(group)
                group_layout.setSpacing(8)
                group_layout.setHorizontalSpacing(8)

                cols = 4
                row = 0
                col = 0
                for name, url in links:
                    btn = QPushButton(name)
                    btn.setStyleSheet("""
                        QPushButton {
                            background: rgba(255,255,255,0.06);
                            border: 1px solid rgba(255,255,255,0.05);
                            border-radius: 8px;
                            padding: 8px 6px;
                            font-size: 12px;
                            color: palette(text);
                            text-align: center;
                        }
                        QPushButton:hover {
                            background: rgba(255,255,255,0.12);
                        }
                    """)
                    btn.clicked.connect(lambda checked, u=url: self.load_url_in_new_tab(u))
                    group_layout.addWidget(btn, row, col)
                    col += 1
                    if col >= cols:
                        col = 0
                        row += 1

                scroll_layout.addWidget(group)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        return dashboard

    def dashboard_search_execute(self):
        text = self.dashboard_search.text().strip()
        if text:
            engine = self.db.get_setting("search_engine", "google")
            search_urls = {
                "google": "https://www.google.com/search?q={}",
                "duckduckgo": "https://duckduckgo.com/?q={}",
                "bing": "https://www.bing.com/?FORM=Z9FD1&q={}",
                "yahoo": "https://search.yahoo.com/search?p={}",
                "brave": "https://search.brave.com/search?q={}"
            }
            template = search_urls.get(engine, search_urls["google"])
            url = template.format(text)
            self.load_url_in_new_tab(url)
            self.dashboard_search.clear()

    def load_url_in_new_tab(self, url: str):
        self.stacked_widget.setCurrentIndex(0)
        self.tab_widget.new_tab(url)

    def on_sidebar_page_selected(self, page_id: str):
        if page_id == "browser":
            self.stacked_widget.setCurrentIndex(0)
        elif page_id == "dashboard":
            self.stacked_widget.setCurrentIndex(1)
        elif page_id == "bookmarks":
            dlg = BookmarksDialog(self.db, self)
            dlg.exec()
        elif page_id == "history":
            dlg = HistoryDialog(self.db, self)
            dlg.exec()
        elif page_id == "downloads":
            dlg = DownloadsDialog(self.db, self)
            dlg.exec()
        elif page_id == "settings":
            dlg = SettingsDialog(self.db, self)
            dlg.exec()
        elif page_id == "extensions":
            self.load_url_in_new_tab("https://chromewebstore.google.com/category/extensions")
        elif page_id == "notes":
            self.load_url_in_new_tab("https://keep.google.com/")
        elif page_id == "weather":
            self.load_url_in_new_tab("https://www.accuweather.com/")
        elif page_id == "ai":
            self.load_url_in_new_tab("https://www.perplexity.ai/")
        elif page_id == "calculator":
            self.load_url_in_new_tab("https://calculator.apps.chrome/")
        elif page_id == "about":
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.about(self, "About BeautifulBrowser",
                              "BeautifulBrowser v1.0\n\n"
                              "A modern Chromium-based browser built with Python and Qt.\n"
                              "Designed with glassmorphism and a clean UI.\n\n"
                              "❤️ Made with love by the BeautifulBrowser team.")

    def restore_session(self):
        self.tab_widget.new_tab()

    def closeEvent(self, event):
        self.slideshow_timer.stop()
        self.clock_timer.stop()
        event.accept()

    # ---- Status bar methods ----
    def show_status_message(self, message: str):
        self.status_bar.setText(message)

    def clear_status_message(self):
        self.status_bar.setText("")
