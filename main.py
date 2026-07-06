import sys
import traceback

print("=== BeautifulBrowser Debug Start ===", file=sys.stderr)

try:
    print("Importing mainwindow...", file=sys.stderr)
    from mainwindow import MainWindow
    print("Importing database...", file=sys.stderr)
    from database import Database
    print("Importing themes...", file=sys.stderr)
    from themes import ThemeManager
    print("All imports successful!", file=sys.stderr)

    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QIcon, QFont, QPixmap
    from PySide6.QtWidgets import QApplication, QSplashScreen

    from utils import resource_path

    print("Creating app...", file=sys.stderr)
    app = QApplication(sys.argv)
    app.setApplicationName("BeautifulBrowser")

    print("Initializing database...", file=sys.stderr)
    db = Database()
    ThemeManager.initialize(db)

    print("Creating main window...", file=sys.stderr)
    window = MainWindow(db)
    window.show()

    print("Running event loop...", file=sys.stderr)
    sys.exit(app.exec())

except Exception as e:
    print("=== EXCEPTION CAUGHT ===", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    input("Press Enter to exit...")
