"""
Widgets - Custom reusable widgets (animated buttons, glass frames, etc.)
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QPoint, QSize, Signal
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QLinearGradient, QPixmap, QIcon
from PySide6.QtWidgets import QPushButton, QWidget, QFrame, QLabel, QVBoxLayout, QGraphicsOpacityEffect


def qrcode_available() -> bool:
    """Check if qrcode library is installed"""
    try:
        import qrcode
        return True
    except ImportError:
        return False


class AnimatedButton(QPushButton):
    """Button with hover and click animations using QGraphicsOpacityEffect"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)
        self._animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._animation.setDuration(150)

    def enterEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._opacity_effect.opacity())
        self._animation.setEndValue(0.7)
        self._animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animation.stop()
        self._animation.setStartValue(self._opacity_effect.opacity())
        self._animation.setEndValue(1.0)
        self._animation.start()
        super().leaveEvent(event)


class GlassFrame(QFrame):
    """A frame with glassmorphism effect"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            GlassFrame {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 15px;
            }
        """)


class RoundedWidget(QWidget):
    """Widget with rounded corners and optional blur effect"""

    def __init__(self, parent=None, radius=10):
        super().__init__(parent)
        self.radius = radius
        self.setAttribute(Qt.WA_StyledBackground, True)

    def paintEvent(self, event):
        super().paintEvent(event)


class RippleButton(QPushButton):
    """Button with ripple effect (simplified)"""

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.ripple_radius = 0
        self.ripple_center = QPoint()
        self.ripple_animation = QPropertyAnimation(self, b"ripple_radius")
        self.ripple_animation.setDuration(600)
        self.ripple_animation.setEasingCurve(QEasingCurve.OutQuad)

    def mousePressEvent(self, event):
        self.ripple_center = event.position().toPoint()
        self.ripple_radius = 0
        self.ripple_animation.setStartValue(0)
        self.ripple_animation.setEndValue(100)
        self.ripple_animation.start()
        super().mousePressEvent(event)

    def set_ripple_radius(self, r):
        self.ripple_radius = r
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.ripple_radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(255, 255, 255, 50)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(self.ripple_center, self.ripple_radius, self.ripple_radius)
