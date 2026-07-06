"""
Themes - Theme management with predefined and custom themes
"""

import os
import json
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor

from database import Database


class ThemeManager(QObject):
    """Singleton theme manager"""

    _instance = None

    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_theme = "Light"
        self.themes = {}
        self.colors = {}
        self.load_themes()

    @classmethod
    def instance(cls):
        return cls._instance

    @classmethod
    def initialize(cls, db: Database):
        cls._instance = cls(db)

    def load_themes(self):
        """Load predefined themes from resources and custom from DB"""
        predefined = {
            "Dark": self.dark_theme(),
            "Light": self.light_theme(),
            "AMOLED": self.amoled_theme(),
            "Ocean": self.ocean_theme(),
            "Purple": self.purple_theme()
        }
        self.themes.update(predefined)

        custom = self.db.get_theme("custom_theme")
        if custom:
            self.themes["Custom"] = custom

        theme_from_db = self.db.get_setting("theme", "Light")
        self.load_theme(theme_from_db)

    def dark_theme(self) -> str:
        return """
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QMainWindow, QDialog {
                background-color: #1e1e1e;
            }
            QLineEdit, QTextEdit, QTableView, QTreeView {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
            QPushButton:pressed {
                background-color: #505050;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #d4d4d4;
                padding: 8px 12px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #3c3c3c;
            }
            QTabBar::tab:hover {
                background-color: #3c3c3c;
            }
            QMenuBar, QMenu {
                background-color: #2d2d2d;
                color: #d4d4d4;
            }
            QMenu::item:selected {
                background-color: #3c3c3c;
            }
        """

    def light_theme(self) -> str:
        return """
            QWidget {
                background-color: #f0f0f0;
                color: #1e1e1e;
            }
            QMainWindow, QDialog {
                background-color: #f0f0f0;
            }
            QLineEdit, QTextEdit, QTableView, QTreeView {
                background-color: #ffffff;
                color: #1e1e1e;
                border: 1px solid #cccccc;
            }
            QPushButton {
                background-color: #ffffff;
                color: #1e1e1e;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #cccccc;
            }
            QTabBar::tab {
                background-color: #e6e6e6;
                color: #1e1e1e;
                padding: 8px 12px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #f0f0f0;
            }
            QTabBar::tab:hover {
                background-color: #d9d9d9;
            }
            QMenuBar, QMenu {
                background-color: #f0f0f0;
                color: #1e1e1e;
            }
            QMenu::item:selected {
                background-color: #d9d9d9;
            }
        """

    def amoled_theme(self) -> str:
        return """
            QWidget {
                background-color: #000000;
                color: #ffffff;
            }
            QMainWindow, QDialog {
                background-color: #000000;
            }
            QLineEdit, QTextEdit, QTableView, QTreeView {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #1a1a1a;
            }
            QPushButton {
                background-color: #0a0a0a;
                color: #ffffff;
                border: 1px solid #1a1a1a;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QTabBar::tab {
                background-color: #0a0a0a;
                color: #ffffff;
                padding: 8px 12px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #1a1a1a;
            }
            QTabBar::tab:hover {
                background-color: #1a1a1a;
            }
            QMenuBar, QMenu {
                background-color: #0a0a0a;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #1a1a1a;
            }
        """

    def ocean_theme(self) -> str:
        return """
            QWidget {
                background-color: #0a1628;
                color: #b0c4de;
            }
            QMainWindow, QDialog {
                background-color: #0a1628;
            }
            QLineEdit, QTextEdit, QTableView, QTreeView {
                background-color: #0e1a2f;
                color: #b0c4de;
                border: 1px solid #1a3050;
            }
            QPushButton {
                background-color: #0e1a2f;
                color: #b0c4de;
                border: 1px solid #1a3050;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #1a3050;
            }
            QPushButton:pressed {
                background-color: #2a4060;
            }
            QTabBar::tab {
                background-color: #0e1a2f;
                color: #b0c4de;
                padding: 8px 12px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #1a3050;
            }
            QTabBar::tab:hover {
                background-color: #1a3050;
            }
            QMenuBar, QMenu {
                background-color: #0e1a2f;
                color: #b0c4de;
            }
            QMenu::item:selected {
                background-color: #1a3050;
            }
        """

    def purple_theme(self) -> str:
        return """
            QWidget {
                background-color: #1a0a2e;
                color: #d4b0ff;
            }
            QMainWindow, QDialog {
                background-color: #1a0a2e;
            }
            QLineEdit, QTextEdit, QTableView, QTreeView {
                background-color: #2a1040;
                color: #d4b0ff;
                border: 1px solid #4a1a6e;
            }
            QPushButton {
                background-color: #2a1040;
                color: #d4b0ff;
                border: 1px solid #4a1a6e;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4a1a6e;
            }
            QPushButton:pressed {
                background-color: #5a2a8e;
            }
            QTabBar::tab {
                background-color: #2a1040;
                color: #d4b0ff;
                padding: 8px 12px;
                border: none;
            }
            QTabBar::tab:selected {
                background-color: #4a1a6e;
            }
            QTabBar::tab:hover {
                background-color: #4a1a6e;
            }
            QMenuBar, QMenu {
                background-color: #2a1040;
                color: #d4b0ff;
            }
            QMenu::item:selected {
                background-color: #4a1a6e;
            }
        """

    def load_theme(self, name: str):
        if name in self.themes:
            self.current_theme = name
            self.db.set_setting("theme", name)
        else:
            self.load_theme("Light")

    def get_current_stylesheet(self) -> str:
        return self.themes.get(self.current_theme, "")

    def get_theme_names(self) -> List[str]:
        return list(self.themes.keys())

    def get_color(self, color_name: str) -> str:
        if self.current_theme == "Dark":
            return "#1e1e1e"
        elif self.current_theme == "Light":
            return "#f0f0f0"
        elif self.current_theme == "AMOLED":
            return "#000000"
        elif self.current_theme == "Ocean":
            return "#0a1628"
        elif self.current_theme == "Purple":
            return "#1a0a2e"
        return "#f0f0f0"
