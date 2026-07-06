"""
Sidebar - Collapsible sidebar with emoji icons and AI panel
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QColor, QPainter, QBrush, QPen
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QScrollArea, QFrame, QStackedWidget, QTextEdit, QLineEdit,
                               QToolButton, QSizePolicy, QSpacerItem)

from database import Database
from utils import resource_path
from widgets import AnimatedButton, GlassFrame


class SidebarItem(QPushButton):
    """Sidebar navigation item with emoji icon and label"""

    def __init__(self, text: str, emoji: str, parent=None):
        super().__init__(parent)
        self.setText(f"{emoji}  {text}")
        self.setCheckable(True)
        self.setAutoExclusive(True)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 10px;
                background: transparent;
                border: none;
                border-radius: 8px;
                color: palette(text);
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
            }
            QPushButton:checked {
                background: rgba(255,255,255,0.12);
                color: #0078d4;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)


class Sidebar(QWidget):
    """Sidebar with collapsible sections, AI panel, and page selection"""

    page_selected = Signal(str)

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.collapsed = False
        self.ai_visible = False
        self.setFixedWidth(60)
        self.setObjectName("sidebar")
        self.setStyleSheet("""
            #sidebar {
                background: rgba(255,255,255,0.03);
                border-right: 1px solid rgba(255,255,255,0.05);
                backdrop-filter: blur(10px);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.toggle_btn = AnimatedButton("☰")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: palette(text);
                font-size: 20px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
            }
        """)
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.toggle_btn, alignment=Qt.AlignHCenter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        items_widget = QWidget()
        items_layout = QVBoxLayout(items_widget)
        items_layout.setContentsMargins(5, 5, 5, 5)
        items_layout.setSpacing(2)

        self.items = {}
        # Removed OS and Store
        item_data = [
            ("dashboard", "📊", "Dashboard"),
            ("browser", "🌐", "Browser"),
            ("bookmarks", "🔖", "Bookmarks"),
            ("history", "📜", "History"),
            ("downloads", "⬇️", "Downloads"),
            ("notes", "📝", "Notes"),
            ("ai", "🤖", "AI Assistant"),
            ("weather", "🌤️", "Weather"),
            ("calculator", "🧮", "Calculator"),
            ("extensions", "🧩", "Extensions"),
            ("settings", "⚙️", "Settings"),
            ("about", "ℹ️", "About"),
        ]

        for key, emoji, label in item_data:
            btn = SidebarItem(label, emoji)
            btn.clicked.connect(lambda checked, k=key: self.select_page(k))
            items_layout.addWidget(btn)
            self.items[key] = btn

        items_layout.addStretch()

        scroll.setWidget(items_widget)
        layout.addWidget(scroll)

        self.ai_panel = self.create_ai_panel()
        layout.addWidget(self.ai_panel)

        self.select_page("browser")

    def create_ai_panel(self) -> QWidget:
        panel = QWidget()
        panel.setVisible(False)
        panel.setFixedHeight(400)
        panel.setStyleSheet("""
            QWidget {
                background: rgba(0,0,0,0.1);
                border-top: 1px solid rgba(255,255,255,0.05);
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        header = QHBoxLayout()
        title = QLabel("AI Assistant")
        title.setStyleSheet("font-weight: bold; color: palette(text);")
        header.addWidget(title)
        close_btn = AnimatedButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background: transparent; border: none; color: palette(text);")
        close_btn.clicked.connect(self.toggle_ai_panel)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self.ai_chat = QTextEdit()
        self.ai_chat.setReadOnly(True)
        self.ai_chat.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,0.05);
                border: none;
                border-radius: 8px;
                padding: 8px;
                color: palette(text);
            }
        """)
        layout.addWidget(self.ai_chat)

        input_layout = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("Ask AI...")
        self.ai_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 5px 10px;
                color: palette(text);
            }
        """)
        input_layout.addWidget(self.ai_input)

        send_btn = AnimatedButton("Send")
        send_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                border: none;
                border-radius: 15px;
                padding: 5px 15px;
                color: white;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        send_btn.clicked.connect(self.send_ai_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        return panel

    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        target_width = 40 if self.collapsed else 200
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(target_width)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.start()

    def select_page(self, page_id: str):
        for key, btn in self.items.items():
            btn.setChecked(key == page_id)
        self.page_selected.emit(page_id)

    def toggle_ai_panel(self):
        self.ai_visible = not self.ai_visible
        self.ai_panel.setVisible(self.ai_visible)
        if self.ai_visible:
            self.ai_chat.append("AI Assistant ready. Ask me anything about this page.")

    def send_ai_message(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        self.ai_chat.append(f"You: {text}")
        response = f"AI: I'm a demo assistant. You asked: '{text}'. In a real implementation, I'd summarize the page or answer your query."
        self.ai_chat.append(response)
        self.ai_input.clear()
