"""
Sidebar - Collapsible sidebar with emoji icons and AI panel, reading list, quick notes, highlights
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal, Slot, QSize, QTimer
from PySide6.QtGui import QIcon, QColor, QPainter, QBrush, QPen
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QScrollArea, QFrame, QStackedWidget, QTextEdit, QLineEdit,
                               QToolButton, QSizePolicy, QSpacerItem, QListWidget, QListWidgetItem,
                               QMenu, QFileDialog, QMessageBox)

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
        item_data = [
            ("dashboard", "📊", "Dashboard"),
            ("browser", "🌐", "Browser"),
            ("bookmarks", "🔖", "Bookmarks"),
            ("history", "📜", "History"),
            ("downloads", "⬇️", "Downloads"),
            ("notes", "📝", "Notes"),
            ("reading_list", "📚", "Reading List"),
            ("highlights", "✏️", "Highlights"),
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

        # AI panel
        self.ai_panel = self.create_ai_panel()
        layout.addWidget(self.ai_panel)

        # Quick notes panel (hidden)
        self.notes_panel = self.create_notes_panel()
        layout.addWidget(self.notes_panel)

        # Reading list panel (hidden)
        self.reading_panel = self.create_reading_panel()
        layout.addWidget(self.reading_panel)

        # Highlights panel (hidden) - NEW
        self.highlights_panel = self.create_highlights_panel()
        layout.addWidget(self.highlights_panel)

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

    def create_notes_panel(self) -> QWidget:
        panel = QWidget()
        panel.setVisible(False)
        panel.setFixedHeight(300)
        panel.setStyleSheet("""
            QWidget {
                background: rgba(0,0,0,0.1);
                border-top: 1px solid rgba(255,255,255,0.05);
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        header = QHBoxLayout()
        title = QLabel("Quick Notes")
        title.setStyleSheet("font-weight: bold; color: palette(text);")
        header.addWidget(title)
        close_btn = AnimatedButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background: transparent; border: none; color: palette(text);")
        close_btn.clicked.connect(self.toggle_notes_panel)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Write your notes here...")
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,0.05);
                border: none;
                border-radius: 8px;
                padding: 8px;
                color: palette(text);
            }
        """)
        layout.addWidget(self.notes_edit)

        save_btn = QPushButton("Save Notes")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        save_btn.clicked.connect(self.save_notes)
        layout.addWidget(save_btn)

        return panel

    def create_reading_panel(self) -> QWidget:
        panel = QWidget()
        panel.setVisible(False)
        panel.setFixedHeight(300)
        panel.setStyleSheet("""
            QWidget {
                background: rgba(0,0,0,0.1);
                border-top: 1px solid rgba(255,255,255,0.05);
            }
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        header = QHBoxLayout()
        title = QLabel("Reading List")
        title.setStyleSheet("font-weight: bold; color: palette(text);")
        header.addWidget(title)
        close_btn = AnimatedButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background: transparent; border: none; color: palette(text);")
        close_btn.clicked.connect(self.toggle_reading_panel)
        header.addWidget(close_btn)
        layout.addLayout(header)

        self.reading_list = QListWidget()
        self.reading_list.setStyleSheet("""
            QListWidget {
                background: rgba(255,255,255,0.05);
                border: none;
                border-radius: 8px;
                color: palette(text);
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        self.reading_list.itemDoubleClicked.connect(self.open_reading_item)
        layout.addWidget(self.reading_list)

        add_btn = QPushButton("Add Current Page")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        add_btn.clicked.connect(self.add_current_to_reading_list)
        layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        remove_btn.clicked.connect(self.remove_reading_item)
        layout.addWidget(remove_btn)

        return panel

    # ---- NEW: Highlights Panel ----
    def create_highlights_panel(self) -> QWidget:
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
        layout.setSpacing(5)

        header = QHBoxLayout()
        title = QLabel("✏️ Highlights & Notes")
        title.setStyleSheet("font-weight: bold; color: palette(text);")
        header.addWidget(title)
        close_btn = AnimatedButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("background: transparent; border: none; color: palette(text);")
        close_btn.clicked.connect(self.toggle_highlights_panel)
        header.addWidget(close_btn)
        layout.addLayout(header)

        # Search bar
        self.highlights_search = QLineEdit()
        self.highlights_search.setPlaceholderText("Search highlights...")
        self.highlights_search.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 4px 10px;
                color: palette(text);
            }
        """)
        self.highlights_search.textChanged.connect(self.filter_highlights)
        layout.addWidget(self.highlights_search)

        # List widget
        self.highlights_list = QListWidget()
        self.highlights_list.setStyleSheet("""
            QListWidget {
                background: rgba(255,255,255,0.05);
                border: none;
                border-radius: 8px;
                color: palette(text);
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }
            QListWidget::item:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        self.highlights_list.itemDoubleClicked.connect(self.open_highlight)
        self.highlights_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.highlights_list.customContextMenuRequested.connect(self.show_highlight_context_menu)
        layout.addWidget(self.highlights_list)

        # Buttons: Export, Clear
        btn_layout = QHBoxLayout()
        export_btn = QPushButton("📤 Export All")
        export_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        export_btn.clicked.connect(self.export_highlights)
        btn_layout.addWidget(export_btn)

        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #c0392b;
            }
        """)
        clear_btn.clicked.connect(self.clear_all_highlights)
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

        self.highlights_data = []
        return panel

    def toggle_ai_panel(self):
        self.ai_visible = not self.ai_visible
        self.ai_panel.setVisible(self.ai_visible)
        if self.ai_visible:
            self.ai_chat.append("AI Assistant ready. Ask me anything about this page.")

    def toggle_notes_panel(self):
        visible = self.notes_panel.isVisible()
        self.notes_panel.setVisible(not visible)
        if not visible:
            notes = self.db.get_quick_notes()
            self.notes_edit.setText(notes)

    def toggle_reading_panel(self):
        visible = self.reading_panel.isVisible()
        self.reading_panel.setVisible(not visible)
        if not visible:
            self.refresh_reading_list()

    def toggle_highlights_panel(self):
        visible = self.highlights_panel.isVisible()
        self.highlights_panel.setVisible(not visible)
        if not visible:
            self.refresh_highlights()

    def send_ai_message(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        self.ai_chat.append(f"You: {text}")
        response = f"AI: I'm a demo assistant. You asked: '{text}'. In a real implementation, I'd summarize the page or answer your query."
        self.ai_chat.append(response)
        self.ai_input.clear()

    def save_notes(self):
        text = self.notes_edit.toPlainText()
        self.db.save_quick_notes(text)

    # ---- Reading List methods ----
    def add_current_to_reading_list(self):
        main_window = self.window()
        browser = main_window.tab_widget.current_browser()
        if browser:
            url = browser.get_current_url()
            title = browser.get_current_title()
            if url and title:
                self.db.add_reading_item(url, title)
                self.refresh_reading_list()

    def remove_reading_item(self):
        item = self.reading_list.currentItem()
        if item:
            url = item.data(Qt.UserRole)
            self.db.remove_reading_item(url)
            self.refresh_reading_list()

    def refresh_reading_list(self):
        self.reading_list.clear()
        items = self.db.get_reading_list()
        for url, title in items:
            item = QListWidgetItem(f"{title}")
            item.setData(Qt.UserRole, url)
            self.reading_list.addItem(item)

    def open_reading_item(self, item):
        url = item.data(Qt.UserRole)
        if url:
            main_window = self.window()
            main_window.load_url_in_new_tab(url)

    # ---- Highlights methods ----
    def refresh_highlights(self):
        self.highlights_data = self.db.get_highlights()
        self.filter_highlights()

    def filter_highlights(self):
        search = self.highlights_search.text().strip().lower()
        self.highlights_list.clear()
        for item in self.highlights_data:
            if search:
                if search not in (item['selected_text'].lower() + item['title'].lower() + (item['note'] or '').lower()):
                    continue
            display = f"{item['title'] or 'Untitled'}"
            snippet = item['selected_text'][:80] + ("..." if len(item['selected_text']) > 80 else "")
            display += f"\n{snippet}"
            if item['note']:
                display += f"\n📝 {item['note'][:60]}{'...' if len(item['note']) > 60 else ''}"
            list_item = QListWidgetItem(display)
            list_item.setData(Qt.UserRole, item['id'])
            list_item.setToolTip(f"URL: {item['url']}\nText: {item['selected_text']}")
            self.highlights_list.addItem(list_item)

    def open_highlight(self, item):
        highlight_id = item.data(Qt.UserRole)
        for h in self.highlights_data:
            if h['id'] == highlight_id:
                url = h['url']
                text = h['selected_text']
                main_window = self.window()
                main_window.load_url_in_new_tab(url)
                # After page loads, highlight the text
                QTimer.singleShot(2000, lambda: self._highlight_text_in_current_tab(text))
                break

    def _highlight_text_in_current_tab(self, text):
        main_window = self.window()
        browser = main_window.tab_widget.current_browser()
        if browser:
            # Escape backslashes and double quotes for safe JavaScript injection
            escaped_text = text.replace('"', '\\"').replace('\\', '\\\\')
            js = f"""
            (function() {{
                var elements = document.querySelectorAll('*');
                var found = false;
                for (var i=0; i<elements.length && !found; i++) {{
                    if (elements[i].textContent.includes("{escaped_text}")) {{
                        elements[i].style.backgroundColor = 'yellow';
                        elements[i].style.transition = 'background-color 2s';
                        elements[i].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        setTimeout(function() {{
                            elements[i].style.backgroundColor = '';
                        }}, 5000);
                        found = true;
                    }}
                }}
            }})();
            """
            browser.web_view.page().runJavaScript(js)

    def show_highlight_context_menu(self, pos):
        item = self.highlights_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        delete_act = menu.addAction("Delete Highlight")
        action = menu.exec(self.highlights_list.mapToGlobal(pos))
        if action == delete_act:
            highlight_id = item.data(Qt.UserRole)
            self.db.delete_highlight(highlight_id)
            self.refresh_highlights()

    def export_highlights(self):
        text = self.db.export_highlights()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Highlights", "highlights.txt", "Text Files (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Export Complete", f"Highlights exported to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {e}")

    def clear_all_highlights(self):
        reply = QMessageBox.question(self, "Clear All Highlights",
                                     "Are you sure you want to delete all highlights?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            with self.db._get_cursor() as cur:
                cur.execute('DELETE FROM highlights')
            self.refresh_highlights()

    # ---- Sidebar navigation ----
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
        if page_id == "notes":
            self.toggle_notes_panel()
        elif page_id == "reading_list":
            self.toggle_reading_panel()
        elif page_id == "highlights":
            self.toggle_highlights_panel()
        else:
            self.page_selected.emit(page_id)
