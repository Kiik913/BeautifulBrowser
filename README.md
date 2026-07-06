# BeautifulBrowser
# 🌟 BeautifulBrowser

**BeautifulBrowser** is a modern, production‑quality desktop web browser built with **Python 3.12+** and **PySide6** (Qt for Python) with **QtWebEngine**. It features a sleek, glass‑morphism UI inspired by Arc, Edge, Zen Browser, and Windows 11 – but with its own original design.

![BeautifulBrowser Screenshot](screenshot.png)

---

## ✨ Features

### 🖥️ Window & UI
- **Frameless, resizable window** with custom title bar (min/max/close)
- **Glassmorphism** design with blur effects and rounded corners
- **Smooth animations** and hover effects
- **Custom title bar** with draggable area

### 🎨 Themes
- **Light** (default), **Dark**, **AMOLED**, **Ocean**, **Purple**
- **Custom accent colours**
- **Wallpaper support** – set any image as background

### 📑 Tabs
- Unlimited tabs
- New tab, close, duplicate, pin, mute
- Tab previews on hover
- Drag and drop reorder
- Restore closed tabs
- Keyboard shortcuts (Ctrl+T, Ctrl+W, Ctrl+Shift+T, etc.)

### 🧭 Navigation
- Back / Forward / Refresh / Stop / Home
- Address bar with HTTPS lock icon
- Search support (Google, DuckDuckGo, Bing, Yahoo, Brave)
- Bookmark button (add/remove)
- Progress bar while loading pages

### 📚 Sidebar
- Collapsible with animation
- Quick access to:
  - Dashboard
  - Browser
  - Bookmarks
  - History
  - Downloads
  - Notes (Google Keep)
  - AI Assistant (Perplexity AI)
  - Weather (AccuWeather)
  - Calculator
  - Themes (Settings → Appearance)
  - Extensions (Chrome Web Store)
  - Settings
  - About

### 🤖 AI Assistant
- Modern chat interface (mock – ready for real API)
- Summarize, explain, translate, rewrite, generate notes

### 📦 Built‑in Tools
- Calculator (opens Chrome Calculator)
- Notes (Google Keep)
- QR Code Generator (coming soon)
- Unit Converter (coming soon)

### 💾 Data Management
- **SQLite database** for:
  - History (with search & clear)
  - Bookmarks (folders, import/export HTML)
  - Downloads (progress, pause, resume, open)
  - Settings & Themes
- **Persistent storage** across sessions

### 🔒 Privacy
- Incognito mode
- Clear cookies & cache
- Tracking protection
- Popup blocker
- Permission manager

### ⌨️ Keyboard Shortcuts
| Shortcut | Action |
|----------|--------|
| Ctrl+T | New Tab |
| Ctrl+W | Close Tab |
| Ctrl+Shift+T | Restore Closed Tab |
| Ctrl+L | Focus Address Bar |
| Ctrl+R / F5 | Refresh |
| Ctrl+F | Find in Page |
| Ctrl+D | Bookmark Page |
| Ctrl+H | History |
| Ctrl+J | Downloads |
| Ctrl++ | Zoom In |
| Ctrl+- | Zoom Out |
| F11 | Fullscreen |
| Alt+Left | Back |
| Alt+Right | Forward |

---

## 📦 Requirements

### System Requirements
- **Python 3.12** or later (3.11 also works)
- **pip** (Python package installer)
- **Windows, Linux, or macOS** (QtWebEngine supported on all platforms)

### Python Packages
| Package | Version | Purpose |
|---------|---------|---------|
| PySide6 | >= 6.5 | Qt6 bindings (GUI, WebEngine) |
| beautifulsoup4 | >= 4.12 | Bookmark import/export (optional) |

---

## 🛠️ Installation

### 1. Clone or Download
```bash
git clone https://github.com/Kiik913/BeautifulBrowser.git
cd BeautifulBrowser
```

Or download the ZIP and extract it.

### 2. Create Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install PySide6 beautifulsoup4
```

> `beautifulsoup4` is optional – only needed for bookmark import/export.

### 4. Create Resource Folders
```bash
mkdir -p resources/icons
mkdir -p resources/themes
mkdir -p resources/wallpapers
```

### 5. Add Icons (Optional)
Place your icon files (PNG) in `resources/icons/`. The app will run even without icons, but some UI elements will be blank.

---

## 🚀 Usage

### Run the Browser
```bash
python main.py
```

### First Run
- The database (`browser.db`) will be created automatically in `~/.BeautifulBrowser/`
- Default theme: **Light**
- Default search engine: **Google**
- Default homepage: `https://www.google.com`

---

## 📁 Project Structure

```
BeautifulBrowser/
├── main.py               # Entry point
├── browser.py            # QtWebEngine wrapper + new tab page
├── mainwindow.py         # Main frameless window
├── tabwidget.py          # Tab bar + tab management
├── toolbar.py            # Navigation toolbar
├── sidebar.py            # Sidebar with collapsible items and AI panel
├── settings.py           # Settings dialog (General, Appearance, Privacy, Advanced)
├── history.py            # History viewer
├── bookmarks.py          # Bookmark manager
├── downloads.py          # Download manager
├── database.py           # SQLite database layer
├── themes.py             # Theme manager (predefined + custom)
├── widgets.py            # Custom widgets (animated button, glass frame, etc.)
├── utils.py              # Helper functions (URL, resource path, etc.)
├── README.md             # This file
└── resources/
    ├── icons/            # Icon files (PNG)
    │   ├── app_icon.png
    │   ├── splash.png
    │   ├── lock.png
    │   ├── default_favicon.png
    │   ├── dashboard.png
    │   ├── browser.png
    │   ├── bookmark.png
    │   ├── history.png
    │   ├── download.png
    │   ├── notes.png
    │   ├── ai.png
    │   ├── weather.png
    │   ├── calc.png
    │   ├── themes.png
    │   ├── extensions.png
    │   ├── settings.png
    │   └── about.png
    ├── themes/           # (Optional) custom theme stylesheets
    └── wallpapers/       # (Optional) wallpaper images
```

---

## ⚙️ Configuration

### Settings Location
All settings are stored in the SQLite database at:
- **Windows:** `C:\Users\YourUsername\.BeautifulBrowser\browser.db`
- **Linux/macOS:** `~/.BeautifulBrowser/browser.db`

### Default Settings
| Setting | Default |
|---------|---------|
| Theme | Light |
| Search Engine | Google |
| Homepage | https://www.google.com |
| Download Folder | ~/Downloads |
| Startup Page | Blank Page |
| Tracking Protection | Enabled |
| Block Popups | Enabled |

### Change Settings
Open **Settings** from the sidebar or menu:
- **General:** Startup page, homepage, search engine, download folder
- **Appearance:** Theme, accent colour, wallpaper, font size
- **Privacy:** Clear cookies/cache, tracking protection, popup blocker
- **Advanced:** Developer tools, remote debugging

---

## 🧩 Customising Quick Links

The dashboard and new tab page contain quick links. You can edit them in:

### Dashboard Links (`mainwindow.py` → `create_dashboard()`)
```python
quick_links = [
    ("Aura Lab: Cares & Laughs 2", "https://codepen.io/Kavyant-Kumar/pen/dPOXwmY"),
    ("Instagram", "https://instagram.com/kavyanthub"),
    # Add or remove links here
]
```

### New Tab Links (`browser.py` → `load_new_tab_page()`)
Search for the `<div class="quick-links">` section in the HTML string and modify the `<a>` tags.

---

## 🐛 Troubleshooting

### Error: `ImportError: cannot import name 'QWebEngineProfile'`
**Fix:** Update your imports in `browser.py`:
```python
from PySide6.QtWebEngineCore import (
    QWebEngineProfile,
    QWebEnginePage,
    QWebEngineSettings,
    QWebEngineDownloadRequest
)
```

### Error: `AttributeError: 'BrowserPage' object has no attribute 'fullscreen_requested'`
**Fix:** Change `fullscreen_requested` to `fullScreenRequested` (capital 'S'):
```python
self.fullScreenRequested.connect(self.handle_fullscreen)
```

### Error: `400 Bad Request` from Akamai (Reference #7.6cf10117...)
**Fix:** Add a modern User-Agent in `browser.py`:
```python
self.profile.setHttpUserAgent(
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
```

### Browser Doesn't Start / Missing Icons
- Create placeholder PNG files in `resources/icons/` or use real icons.
- The app will still run, but some buttons will be blank.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the **MIT License** – see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- **Qt for Python (PySide6)** – Official Qt bindings
- **QtWebEngine** – Chromium-based web engine
- **Inspiration** – Arc, Microsoft Edge, Zen Browser, Windows 11
- **Icons** – Flaticon, Icons8, FontAwesome

---

## 📧 Contact

- **GitHub:** [github.com/Kiik913](https://github.com/Kiik913)
- **Instagram:** [@kavyanthub](https://instagram.com/kavyanthub)
- **Discord:** [Aura Lab Server](https://discord.com/channels/1505857480503197696/1505857672597999736)

---

### 🌟 Star Us on GitHub!
If you like this project, please ⭐ star the repository and share it with others!

---

**BeautifulBrowser** – Because browsing should be beautiful. 🎨✨
