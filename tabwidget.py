"""
TabWidget - Manages tabs with preview, grouping, drag-and-drop, tab colours, counters
"""

import os
import random
from typing import Optional, List, Dict, Any

from PySide6.QtCore import Qt, QTimer, QPoint, QRect, Signal, Slot, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QPixmap, QAction, QKeySequence, QColor, QPainter
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabBar, QStackedWidget,
                               QPushButton, QLabel, QMenu, QApplication, QStyle, QToolButton,
                               QColorDialog)

from browser import Browser
from database import Database
from utils import resource_path


class TabBar(QTabBar):
    """Custom tab bar with tab preview, drag, group colors, and tab counter"""

    tab_count_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setDocumentMode(True)
        self.setElideMode(Qt.ElideRight)
        self.setUsesScrollButtons(True)
        self.setStyleSheet("""
            QTabBar::tab {
                background: transparent;
                color: palette(text);
                padding: 8px 12px;
                border: none;
                border-radius: 8px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: rgba(255,255,255,0.12);
            }
            QTabBar::tab:hover {
                background: rgba(255,255,255,0.06);
            }
            QTabBar::tab:!selected {
                background: transparent;
            }
            QTabBar {
                padding-right: 40px;
            }
        """)

        # Tab colours dictionary
        self.tab_colours = {}

        # Add new tab button
        self.new_tab_button = QPushButton("+", self)
        self.new_tab_button.setFixedSize(28, 28)
        self.new_tab_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 14px;
                color: palette(text);
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.15);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,0.25);
            }
        """)
        self.new_tab_button.clicked.connect(self.parent().new_tab)
        self.new_tab_button.show()

        # Mouse tracking for wheel scroll
        self.setMouseTracking(True)

    def tabSizeHint(self, index: int) -> QRect:
        size = super().tabSizeHint(index)
        size.setWidth(min(200, max(80, size.width())))
        return size

    def showEvent(self, event):
        super().showEvent(event)
        self.update_new_tab_button()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_new_tab_button()

    def update_new_tab_button(self):
        x = self.width() - self.new_tab_button.width() - 8
        y = (self.height() - self.new_tab_button.height()) // 2
        self.new_tab_button.move(x, y)
        self.new_tab_button.show()
        self.new_tab_button.raise_()

    def addTab(self, text: str, icon: QIcon = QIcon()) -> int:
        idx = super().addTab(icon, text)
        # Assign random colour to new tab
        self.tab_colours[idx] = self.generate_random_colour()
        self.update_tab_colour(idx)
        self.update_new_tab_button()
        self.tab_count_changed.emit(self.count())
        return idx

    def insertTab(self, index: int, text: str, icon: QIcon = QIcon()) -> int:
        idx = super().insertTab(index, icon, text)
        self.tab_colours[idx] = self.generate_random_colour()
        self.update_tab_colour(idx)
        self.update_new_tab_button()
        self.tab_count_changed.emit(self.count())
        return idx

    def removeTab(self, index: int):
        if index in self.tab_colours:
            del self.tab_colours[index]
        super().removeTab(index)
        self.update_new_tab_button()
        self.tab_count_changed.emit(self.count())

    def generate_random_colour(self) -> QColor:
        """Generate a random pastel colour for tabs"""
        hue = random.randint(0, 360)
        saturation = random.randint(30, 60)
        lightness = random.randint(50, 80)
        return QColor.fromHsl(hue, saturation, lightness)

    def update_tab_colour(self, index: int):
        """Update tab colour indicator"""
        if index in self.tab_colours:
            colour = self.tab_colours[index]
            self.setStyleSheet(self.styleSheet() + f"""
                QTabBar::tab:!selected {{
                    border-left: 3px solid rgba({colour.red()}, {colour.green()}, {colour.blue()}, 0.6);
                }}
            """)

    def set_tab_colour(self, index: int, colour: QColor):
        """Manually set tab colour"""
        if index >= 0 and index < self.count():
            self.tab_colours[index] = colour
            self.update_tab_colour(index)

    def mouseDoubleClickEvent(self, event):
        """Double-click to close tab"""
        if event.button() == Qt.LeftButton:
            index = self.tabAt(event.position().toPoint())
            if index >= 0:
                self.parent().close_tab(index)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        """Middle-click to close tab"""
        if event.button() == Qt.MiddleButton:
            index = self.tabAt(event.position().toPoint())
            if index >= 0:
                self.parent().close_tab(index)
        super().mousePressEvent(event)

    def wheelEvent(self, event):
        """Scroll to switch tabs"""
        if self.count() > 0:
            delta = event.angleDelta().y()
            current = self.currentIndex()
            if delta > 0:
                next_tab = (current - 1) % self.count()
            else:
                next_tab = (current + 1) % self.count()
            self.setCurrentIndex(next_tab)
        super().wheelEvent(event)


class TabWidget(QWidget):
    """Main tab widget containing TabBar and stacked browsers"""

    tab_count_changed = Signal(int)

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.browsers: List[Browser] = []
        self.closed_tabs: List[dict] = []
        self.current_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_bar = TabBar(self)
        self.tab_bar.currentChanged.connect(self.on_tab_changed)
        self.tab_bar.tabCloseRequested.connect(self.close_tab)
        self.tab_bar.tabMoved.connect(self.on_tab_moved)
        self.tab_bar.tab_count_changed.connect(self.tab_count_changed.emit)
        self.tab_bar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_bar.customContextMenuRequested.connect(self.show_tab_context_menu)

        layout.addWidget(self.tab_bar)

        self.stacked = QStackedWidget()
        layout.addWidget(self.stacked)

        self.new_tab()

    def new_tab(self, url: str = "", incognito: bool = False) -> Browser:
        browser = Browser(self, incognito=incognito, db=self.db)
        self.browsers.append(browser)
        self.stacked.addWidget(browser)

        title = "New Tab"
        icon = QIcon(resource_path("resources/icons/default_favicon.png"))
        index = self.tab_bar.addTab(title, icon)
        self.tab_bar.setTabData(index, browser)

        browser.title_changed.connect(lambda t, idx=index: self.update_tab_title(idx, t))
        browser.icon_changed.connect(lambda ic, idx=index: self.update_tab_icon(idx, ic))
        browser.url_changed.connect(lambda u, idx=index: self.update_tab_url(idx, u))
        browser.load_finished.connect(lambda ok, idx=index: self.on_load_finished(idx, ok))
        browser.close_requested.connect(lambda: self.close_tab_by_browser(browser))

        self.tab_bar.setCurrentIndex(index)
        self.current_index = index

        if url:
            browser.load(url)
        else:
            browser.load_new_tab_page()

        self.tab_count_changed.emit(self.count())
        return browser

    def update_tab_title(self, index: int, title: str):
        if index < self.tab_bar.count():
            if not title:
                title = "Loading..."
            self.tab_bar.setTabText(index, title)
            browser = self.tab_bar.tabData(index)
            if browser:
                self.tab_bar.setTabToolTip(index, browser.get_current_url() or title)

    def update_tab_icon(self, index: int, icon: QIcon):
        if index < self.tab_bar.count():
            self.tab_bar.setTabIcon(index, icon)

    def update_tab_url(self, index: int, url: str):
        pass

    def on_load_finished(self, index: int, ok: bool):
        pass

    def close_tab(self, index: int):
        if self.count() <= 1:
            self.new_tab()
            self.tab_bar.removeTab(index)
            return

        browser = self.tab_bar.tabData(index)
        if browser:
            self.closed_tabs.append({
                "url": browser.get_current_url(),
                "title": browser.get_current_title(),
                "incognito": browser.incognito
            })

        self.tab_bar.removeTab(index)
        self.browsers.remove(browser)
        self.stacked.removeWidget(browser)
        browser.deleteLater()

        self.tab_count_changed.emit(self.count())

    def close_tab_by_browser(self, browser: Browser):
        for i, b in enumerate(self.browsers):
            if b is browser:
                self.close_tab(i)
                break

    def on_tab_changed(self, index: int):
        if index < 0:
            return
        self.current_index = index
        browser = self.tab_bar.tabData(index)
        if browser:
            self.stacked.setCurrentWidget(browser)
        self.tab_count_changed.emit(self.count())

    def on_tab_moved(self, from_index: int, to_index: int):
        browser = self.browsers.pop(from_index)
        self.browsers.insert(to_index, browser)
        self.tab_bar.setTabData(to_index, browser)

    def current_browser(self) -> Optional[Browser]:
        if self.current_index >= 0 and self.current_index < len(self.browsers):
            return self.browsers[self.current_index]
        return None

    def count(self) -> int:
        return self.tab_bar.count()

    def close_current_tab(self):
        if self.current_index >= 0:
            self.close_tab(self.current_index)

    def duplicate_tab(self):
        browser = self.current_browser()
        if browser:
            url = browser.get_current_url()
            self.new_tab(url, incognito=browser.incognito)

    def restore_closed_tab(self):
        if self.closed_tabs:
            tab_data = self.closed_tabs.pop()
            self.new_tab(tab_data["url"], incognito=tab_data["incognito"])

    def show_tab_context_menu(self, pos: QPoint):
        index = self.tab_bar.tabAt(pos)
        if index < 0:
            return
        menu = QMenu(self)
        new_tab_act = menu.addAction("New Tab")
        duplicate_act = menu.addAction("Duplicate Tab")
        close_act = menu.addAction("Close Tab")
        close_others_act = menu.addAction("Close Other Tabs")
        close_right_act = menu.addAction("Close Tabs to Right")
        restore_act = menu.addAction("Restore Closed Tab")
        pin_act = menu.addAction("Pin Tab")
        mute_act = menu.addAction("Mute Tab")
        menu.addSeparator()
        set_colour_act = menu.addAction("Set Tab Colour...")

        action = menu.exec(self.tab_bar.mapToGlobal(pos))
        if action == new_tab_act:
            self.new_tab()
        elif action == duplicate_act:
            self.duplicate_tab()
        elif action == close_act:
            self.close_tab(index)
        elif action == close_others_act:
            for i in range(self.count() - 1, -1, -1):
                if i != index:
                    self.close_tab(i)
        elif action == close_right_act:
            for i in range(self.count() - 1, index, -1):
                self.close_tab(i)
        elif action == restore_act:
            self.restore_closed_tab()
        elif action == set_colour_act:
            colour = QColorDialog.getColor()
            if colour.isValid():
                self.tab_bar.set_tab_colour(index, colour)
        elif action == pin_act:
            pass
        elif action == mute_act:
            pass
