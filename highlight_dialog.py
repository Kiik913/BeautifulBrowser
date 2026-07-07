"""
HighlightDialog - Dialog to add a note to a highlighted text
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton


class HighlightDialog(QDialog):
    """Dialog to add a note to highlighted text"""

    def __init__(self, selected_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Note to Highlight")
        self.resize(500, 350)

        layout = QVBoxLayout(self)

        # Selected text preview
        preview_label = QLabel("Selected text:")
        preview_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(preview_label)

        self.text_display = QLabel(selected_text[:500] + ("..." if len(selected_text) > 500 else ""))
        self.text_display.setWordWrap(True)
        self.text_display.setStyleSheet("""
            QLabel {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 8px;
                font-style: italic;
            }
        """)
        layout.addWidget(self.text_display)

        # Note input
        note_label = QLabel("Your note:")
        note_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(note_label)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Write your thoughts about this highlight...")
        self.note_edit.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 8px;
                min-height: 100px;
            }
        """)
        layout.addWidget(self.note_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("💾 Save Highlight")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #106ebe;
            }
        """)
        save_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: palette(text);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.1);
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.selected_text = selected_text

    def get_note(self) -> str:
        return self.note_edit.toPlainText().strip()
