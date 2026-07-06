"""
Browser - QtWebEngine wrapper with enhanced features
"""

import os
import base64
import time
from PySide6.QtCore import QUrl, Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QMenu, QMessageBox, QFileDialog, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineSettings,
    QWebEngineDownloadRequest
)

from utils import is_url


class BrowserPage(QWebEnginePage):
    """Custom page with enhanced features like fullscreen, permission handling"""

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(profile, parent)
        self.fullScreenRequested.connect(self.handle_fullscreen)
        self.reading_mode_active = False
        self.original_html = ""

    def handle_fullscreen(self, request):
        request.accept()
        if self.view():
            window = self.view().window()
            if request.toggleOn():
                window.showFullScreen()
            else:
                window.showNormal()

    def javaScriptConsoleMessage(self, level, message, line_number, source_id):
        if level == QWebEnginePage.JavaScriptConsoleMessageLevel.ErrorLevel:
            print(f"JS Error: {message} at {source_id}:{line_number}")

    def certificateError(self, error):
        error.acceptCertificate()
        return True

    def toggle_reading_mode(self):
        """Toggle reading mode by injecting CSS to strip clutter"""
        if self.reading_mode_active:
            self.triggerAction(QWebEnginePage.Reload)
            self.reading_mode_active = False
        else:
            self.original_html = self.toHtml()
            reading_css = """
            <style>
                body {
                    max-width: 800px !important;
                    margin: 0 auto !important;
                    padding: 40px 20px !important;
                    font-family: Georgia, 'Times New Roman', serif !important;
                    font-size: 18px !important;
                    line-height: 1.8 !important;
                    color: #333 !important;
                    background: #f9f5f0 !important;
                }
                header, footer, nav, aside, .ad, .advertisement, .sidebar, .related,
                .comments, .share, .social, .newsletter, .popup, .banner,
                .menu, .navigation, .footer, .header, .nav, .cookie,
                [class*="ad"], [id*="ad"], [class*="banner"], [id*="banner"],
                [class*="sidebar"], [id*="sidebar"], [class*="related"],
                [class*="share"], [class*="social"], [class*="comment"] {
                    display: none !important;
                }
                h1, h2, h3, h4, h5, h6 {
                    font-family: 'Segoe UI', sans-serif !important;
                    color: #222 !important;
                }
                p {
                    margin-bottom: 20px !important;
                }
                img {
                    max-width: 100% !important;
                    height: auto !important;
                }
                a {
                    color: #0066cc !important;
                }
                @media (prefers-color-scheme: dark) {
                    body {
                        color: #ddd !important;
                        background: #1a1a1a !important;
                    }
                    h1, h2, h3, h4, h5, h6 { color: #eee !important; }
                    a { color: #66b3ff !important; }
                }
            </style>
            """
            js = """
            (function() {
                var style = document.createElement('style');
                style.innerHTML = `""" + reading_css.replace('`', '\\`') + """`;
                document.head.appendChild(style);
                var elements = document.querySelectorAll('header, footer, nav, aside, .ad, .advertisement, .sidebar, .related, .comments, .share, .social, .newsletter, .popup, .banner, .menu, .navigation, .footer, .header, .nav, .cookie, [class*="ad"], [id*="ad"], [class*="banner"], [id*="banner"], [class*="sidebar"], [id*="sidebar"], [class*="related"], [class*="share"], [class*="social"], [class*="comment"]');
                for(var i=0; i<elements.length; i++) {
                    elements[i].style.display = 'none';
                }
                var main = document.querySelector('main, article, .content, .post, .entry, [role="main"]');
                if(main) {
                    main.style.maxWidth = '800px';
                    main.style.margin = '0 auto';
                }
            })();
            """
            self.runJavaScript(js)
            self.reading_mode_active = True


class Browser(QWidget):
    """A single browser tab containing web view and loading progress"""

    url_changed = Signal(str)
    title_changed = Signal(str)
    icon_changed = Signal(QIcon)
    load_progress = Signal(int)
    load_finished = Signal(bool)
    load_time_updated = Signal(float)
    close_requested = Signal()

    def __init__(self, parent=None, incognito: bool = False, db=None):
        super().__init__(parent)
        self.db = db
        self.incognito = incognito
        self.current_url = ""
        self.current_title = ""
        self.favicon = QIcon()
        self.load_start_time = 0
        self.load_time = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Progress bar with load time
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximumHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: transparent;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #00b4d8, stop:1 #0077b6);
                border-radius: 0px;
            }
        """)
        self.progress_bar.hide()

        # Load time label
        self.load_time_label = QLabel("")
        self.load_time_label.setStyleSheet("""
            QLabel {
                color: palette(text);
                font-size: 10px;
                opacity: 0.6;
                padding: 0 5px;
            }
        """)
        self.load_time_label.hide()

        # Web view
        self.web_view = QWebEngineView(self)
        self.web_view.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.web_view.customContextMenuRequested.connect(self.show_context_menu)

        self.setup_profile()
        self.setup_page()
        self.web_view.setPage(self.page)

        self.web_view.urlChanged.connect(self.on_url_changed)
        self.web_view.titleChanged.connect(self.on_title_changed)
        self.web_view.iconChanged.connect(self.on_icon_changed)
        self.web_view.loadProgress.connect(self.on_load_progress)
        self.web_view.loadFinished.connect(self.on_load_finished)

        # Add widgets to layout
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(0)
        progress_layout.addWidget(self.progress_bar, 1)
        progress_layout.addWidget(self.load_time_label)

        layout.addLayout(progress_layout)
        layout.addWidget(self.web_view)

    def setup_profile(self):
        if self.incognito:
            self.profile = QWebEngineProfile("Incognito", self)
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)
            self.profile.setPersistentStoragePath("")
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        else:
            self.profile = QWebEngineProfile.defaultProfile()
            self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            cache_path = os.path.join(os.path.expanduser("~"), ".BeautifulBrowser", "cache")
            os.makedirs(cache_path, exist_ok=True)
            self.profile.setCachePath(cache_path)
            self.profile.setPersistentStoragePath(os.path.join(os.path.expanduser("~"), ".BeautifulBrowser", "storage"))
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)

    def setup_page(self):
        self.page = BrowserPage(self.profile, self)
        self.page.windowCloseRequested.connect(self.close_requested.emit)

    def show_context_menu(self, pos: QPoint):
        menu = QMenu(self)

        back_action = QAction("◀ Back", self)
        back_action.triggered.connect(self.go_back)
        back_action.setEnabled(self.web_view.history().canGoBack())
        menu.addAction(back_action)

        forward_action = QAction("▶ Forward", self)
        forward_action.triggered.connect(self.go_forward)
        forward_action.setEnabled(self.web_view.history().canGoForward())
        menu.addAction(forward_action)

        menu.addSeparator()

        if self.is_loading():
            stop_action = QAction("✕ Stop", self)
            stop_action.triggered.connect(self.stop)
            menu.addAction(stop_action)
        else:
            reload_action = QAction("⟳ Reload", self)
            reload_action.triggered.connect(self.reload)
            menu.addAction(reload_action)

        menu.addSeparator()

        # Reading Mode toggle
        if self.page.reading_mode_active:
            reading_action = QAction("📖 Exit Reading Mode", self)
        else:
            reading_action = QAction("📖 Reading Mode", self)
        reading_action.triggered.connect(self.toggle_reading_mode)
        menu.addAction(reading_action)

        # Screenshot
        screenshot_action = QAction("📷 Screenshot (Visible)", self)
        screenshot_action.triggered.connect(self.take_screenshot)
        menu.addAction(screenshot_action)

        full_screenshot_action = QAction("📷 Screenshot (Full Page)", self)
        full_screenshot_action.triggered.connect(self.take_full_screenshot)
        menu.addAction(full_screenshot_action)

        menu.addSeparator()

        # QR Code
        qr_action = QAction("📱 Generate QR Code", self)
        qr_action.triggered.connect(self.generate_qr_code)
        menu.addAction(qr_action)

        menu.addSeparator()

        zoom_in = QAction("🔍 Zoom In", self)
        zoom_in.triggered.connect(self.zoom_in)
        menu.addAction(zoom_in)

        zoom_out = QAction("🔍 Zoom Out", self)
        zoom_out.triggered.connect(self.zoom_out)
        menu.addAction(zoom_out)

        zoom_reset = QAction("🔍 Reset Zoom", self)
        zoom_reset.triggered.connect(self.zoom_reset)
        menu.addAction(zoom_reset)

        menu.addSeparator()

        if self.db and self.db.get_setting("dev_tools", "false") == "true":
            inspect_action = QAction("🔧 Inspect Element", self)
            inspect_action.triggered.connect(self.inspect_element)
            menu.addAction(inspect_action)

        menu.exec(self.web_view.mapToGlobal(pos))

    def toggle_reading_mode(self):
        self.page.toggle_reading_mode()

    def take_screenshot(self):
        pixmap = self.web_view.grab()
        self.save_screenshot(pixmap)

    def take_full_screenshot(self):
        self.web_view.page().runJavaScript("""
            (function() {
                return {
                    width: document.documentElement.scrollWidth,
                    height: document.documentElement.scrollHeight
                };
            })();
        """, self._handle_full_screenshot)

    def _handle_full_screenshot(self, result):
        if result:
            width = result.get('width', 1920)
            height = result.get('height', 1080)
            pixmap = self.web_view.grab()
            self.save_screenshot(pixmap)

    def save_screenshot(self, pixmap):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", "screenshot.png", "PNG Images (*.png);;JPEG Images (*.jpg)"
        )
        if file_path:
            pixmap.save(file_path)
            QMessageBox.information(self, "Screenshot Saved", f"Screenshot saved to:\n{file_path}")

    def generate_qr_code(self):
        import qrcode
        from io import BytesIO
        from PySide6.QtGui import QPixmap

        url = self.current_url
        if not url:
            QMessageBox.warning(self, "No URL", "No URL to generate QR code for.")
            return

        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.read(), "PNG")
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel
            dlg = QDialog(self)
            dlg.setWindowTitle("QR Code")
            layout = QVBoxLayout(dlg)
            label = QLabel()
            label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))
            layout.addWidget(label)
            dlg.exec()
        except ImportError:
            QMessageBox.warning(self, "QR Code", "Please install 'qrcode' library:\npip install qrcode pillow")

    def inspect_element(self):
        self.web_view.page().setDevToolsPage(self.web_view.page())

    def load(self, url: str):
        if not url:
            return
        if not is_url(url):
            url = self.get_search_url(url)
        self.load_start_time = time.time()
        self.web_view.load(QUrl(url))

    def get_search_url(self, query: str) -> str:
        engine = "google"
        if self.db:
            engine = self.db.get_setting("search_engine", "google")
        search_urls = {
            "google": "https://www.google.com",
            "duckduckgo": "https://duckduckgo.com",
            "bing": "https://www.bing.com",
            "yahoo": "https://search.yahoo.com",
            "brave": "https://search.brave.com"
        }
        template = search_urls.get(engine, search_urls["google"])
        return template.format(query)

    def load_new_tab_page(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Tab</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                    background: transparent;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    color: #1e1e1e;
                }
                .container {
                    text-align: center;
                    max-width: 700px;
                    width: 90%;
                    padding: 30px;
                    background: rgba(255,255,255,0.08);
                    backdrop-filter: blur(20px);
                    -webkit-backdrop-filter: blur(20px);
                    border-radius: 24px;
                    border: 1px solid rgba(255,255,255,0.12);
                    box-shadow: 0 20px 60px rgba(0,0,0,0.2);
                }
                .greeting {
                    font-size: 32px;
                    font-weight: 300;
                    margin-bottom: 20px;
                    letter-spacing: -0.5px;
                }
                .search-box {
                    display: flex;
                    background: rgba(255,255,255,0.15);
                    border-radius: 40px;
                    padding: 6px 6px 6px 20px;
                    margin: 20px 0 30px;
                    border: 1px solid rgba(255,255,255,0.1);
                    transition: all 0.3s;
                }
                .search-box:focus-within {
                    background: rgba(255,255,255,0.25);
                    border-color: #0078d4;
                    box-shadow: 0 0 0 3px rgba(0,120,212,0.3);
                }
                .search-box input {
                    flex: 1;
                    background: transparent;
                    border: none;
                    outline: none;
                    color: inherit;
                    font-size: 16px;
                    padding: 10px 0;
                }
                .search-box input::placeholder {
                    color: rgba(0,0,0,0.4);
                }
                .search-box button {
                    background: #0078d4;
                    border: none;
                    border-radius: 40px;
                    padding: 10px 25px;
                    color: white;
                    font-size: 15px;
                    font-weight: 500;
                    cursor: pointer;
                    transition: background 0.2s;
                    white-space: nowrap;
                }
                .search-box button:hover {
                    background: #106ebe;
                }
                .quick-links {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
                    gap: 12px;
                    margin-top: 10px;
                }
                .quick-link {
                    background: rgba(255,255,255,0.1);
                    border: 1px solid rgba(255,255,255,0.06);
                    border-radius: 16px;
                    padding: 14px 8px;
                    text-decoration: none;
                    color: inherit;
                    font-size: 13px;
                    font-weight: 500;
                    transition: all 0.25s;
                    text-align: center;
                    cursor: pointer;
                    backdrop-filter: blur(10px);
                }
                .quick-link:hover {
                    background: rgba(255,255,255,0.2);
                    transform: translateY(-2px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                }
                .quick-link .icon {
                    font-size: 24px;
                    display: block;
                    margin-bottom: 6px;
                }
                .footer {
                    margin-top: 30px;
                    font-size: 12px;
                    opacity: 0.6;
                }
                @media (prefers-color-scheme: dark) {
                    body { color: #f0f0f0; }
                    .search-box input::placeholder { color: rgba(255,255,255,0.4); }
                    .container { background: rgba(0,0,0,0.3); border-color: rgba(255,255,255,0.08); }
                    .quick-link { background: rgba(255,255,255,0.05); }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="greeting">✨ New Tab</div>
                <div class="search-box">
                    <input type="text" id="searchInput" placeholder="Search or enter address..." autofocus>
                    <button id="searchBtn">Search</button>
                </div>
                <div class="quick-links">
                    <a href="https://codepen.io/Kavyant-Kumar/pen/dPOXwmY" class="quick-link"><span class="icon">🎨</span>Aura Lab 2</a>
                    <a href="https://codepen.io/Kavyant-Kumar/pen/dPGJPKj" class="quick-link"><span class="icon">🎨</span>Aura Lab 1</a>
                    <a href="https://instagram.com/kavyanthub" class="quick-link"><span class="icon">📷</span>Instagram</a>
                    <a href="https://facebook.com/profile.php?id=61586003535719" class="quick-link"><span class="icon">📘</span>Facebook</a>
                    <a href="https://github.com/Kiik913" class="quick-link"><span class="icon">🐙</span>GitHub</a>
                    <a href="https://discord.com/channels/1505857480503197696/1505857672597999736" class="quick-link"><span class="icon">💬</span>Discord</a>
                    <a href="https://keep.google.com/" class="quick-link"><span class="icon">📝</span>Keep</a>
                    <a href="https://calculator.apps.chrome/" class="quick-link"><span class="icon">🧮</span>Calc</a>
                    <a href="https://www.perplexity.ai/" class="quick-link"><span class="icon">🤖</span>Perplexity</a>
                    <a href="https://chromewebstore.google.com/category/extensions" class="quick-link"><span class="icon">🧩</span>Extensions</a>
                </div>
                <div class="footer">BeautifulBrowser · New Tab</div>
            </div>
            <script>
                document.getElementById('searchBtn').addEventListener('click', function() {
                    const query = document.getElementById('searchInput').value.trim();
                    if (query) {
                        window.location.href = 'https://www.google.com/search?q=' + encodeURIComponent(query);
                    }
                });
                document.getElementById('searchInput').addEventListener('keydown', function(e) {
                    if (e.key === 'Enter') {
                        document.getElementById('searchBtn').click();
                    }
                });
                document.getElementById('searchInput').focus();
            </script>
        </body>
        </html>
        """
        encoded = base64.b64encode(html.encode('utf-8')).decode('utf-8')
        data_url = f"data:text/html;base64,{encoded}"
        self.load(data_url)

    def on_url_changed(self, url: QUrl):
        self.current_url = url.toString()
        self.url_changed.emit(self.current_url)

    def on_title_changed(self, title: str):
        self.current_title = title
        self.title_changed.emit(title)

    def on_icon_changed(self, icon: QIcon):
        self.favicon = icon
        self.icon_changed.emit(icon)

    def on_load_progress(self, progress: int):
        if progress < 100:
            self.progress_bar.show()
        self.progress_bar.setValue(progress)
        self.load_progress.emit(progress)

    def on_load_finished(self, ok: bool):
        self.progress_bar.hide()
        self.load_finished.emit(ok)
        if ok:
            self.load_time = time.time() - self.load_start_time
            self.load_time_label.setText(f"Loaded in {self.load_time:.1f}s")
            self.load_time_label.show()
            self.load_time_updated.emit(self.load_time)
            QTimer.singleShot(3000, self.load_time_label.hide)
        if ok and not self.incognito and self.db and self.current_url:
            self.db.add_history(self.current_url, self.current_title)

    def reload(self):
        self.web_view.reload()

    def stop(self):
        self.web_view.stop()

    def go_back(self):
        self.web_view.back()

    def go_forward(self):
        self.web_view.forward()

    def home(self):
        homepage = "https://www.google.com"
        if self.db:
            homepage = self.db.get_setting("homepage", homepage)
        self.load(homepage)

    def zoom_in(self):
        self.web_view.setZoomFactor(self.web_view.zoomFactor() + 0.1)

    def zoom_out(self):
        self.web_view.setZoomFactor(max(0.1, self.web_view.zoomFactor() - 0.1))

    def zoom_reset(self):
        self.web_view.setZoomFactor(1.0)

    def find_text(self, text: str):
        self.web_view.findText(text)

    def print_page(self):
        self.web_view.page().printToPdf("output.pdf")

    def get_current_url(self) -> str:
        return self.current_url

    def get_current_title(self) -> str:
        return self.current_title

    def get_favicon(self) -> QIcon:
        return self.favicon

    def is_loading(self) -> bool:
        return self.web_view.isLoading()
