"""
Database - SQLite persistence for history, bookmarks, downloads, settings, themes, sessions
"""

import sqlite3
import os
import json
from typing import List, Tuple, Optional, Any
from datetime import datetime
import threading
from contextlib import contextmanager


class Database:
    """Thread-safe database manager"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            app_data = os.path.join(os.path.expanduser("~"), ".BeautifulBrowser")
            os.makedirs(app_data, exist_ok=True)
            self.db_path = os.path.join(app_data, "browser.db")
        else:
            self.db_path = db_path

        self._lock = threading.Lock()
        self._init_db()

    @contextmanager
    def _get_cursor(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _init_db(self):
        with self._get_cursor() as cur:
            # History table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    title TEXT,
                    timestamp INTEGER NOT NULL,
                    visits INTEGER DEFAULT 1
                )
            ''')
            # Bookmarks table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT,
                    folder TEXT,
                    added INTEGER NOT NULL
                )
            ''')
            # Downloads table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT,
                    total_size INTEGER,
                    received_size INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'downloading',
                    start_time INTEGER NOT NULL,
                    end_time INTEGER
                )
            ''')
            # Settings table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            # Themes table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS themes (
                    name TEXT PRIMARY KEY,
                    stylesheet TEXT,
                    is_custom BOOLEAN DEFAULT 0
                )
            ''')
            # Sessions table (for session manager)
            cur.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    timestamp INTEGER NOT NULL
                )
            ''')
            # Insert default settings
            default_settings = {
                "startup_page": "0",
                "homepage": "https://www.google.com",
                "search_engine": "google",
                "download_folder": os.path.expanduser("~/Downloads"),
                "theme": "Light",
                "accent_color": "#0078d4",
                "wallpaper": "",
                "random_wallpaper": "false",
                "slideshow_enabled": "false",
                "slideshow_interval": "5",
                "font_size": "9",
                "tracking_protection": "true",
                "block_popups": "true",
                "dev_tools": "false",
                "remote_debug": "false",
                "ad_blocker": "true"
            }
            for key, value in default_settings.items():
                cur.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))

    # === History ===
    def add_history(self, url: str, title: str):
        with self._get_cursor() as cur:
            now = int(datetime.now().timestamp())
            cur.execute('SELECT id FROM history WHERE url = ?', (url,))
            row = cur.fetchone()
            if row:
                cur.execute('UPDATE history SET visits = visits + 1, timestamp = ? WHERE id = ?', (now, row['id']))
            else:
                cur.execute('INSERT INTO history (url, title, timestamp) VALUES (?, ?, ?)', (url, title, now))

    def get_history(self, limit: int = 1000) -> List[Tuple[str, str, int]]:
        with self._get_cursor() as cur:
            cur.execute('''
                SELECT url, title, timestamp FROM history
                ORDER BY timestamp DESC LIMIT ?
            ''', (limit,))
            return [(row['url'], row['title'], row['timestamp']) for row in cur.fetchall()]

    def clear_history(self):
        with self._get_cursor() as cur:
            cur.execute('DELETE FROM history')

    def delete_history_item(self, url: str):
        with self._get_cursor() as cur:
            cur.execute('DELETE FROM history WHERE url = ?', (url,))

    # === Bookmarks ===
    def add_bookmark(self, url: str, title: str = None, folder: str = None):
        with self._get_cursor() as cur:
            now = int(datetime.now().timestamp())
            cur.execute('''
                INSERT OR REPLACE INTO bookmarks (url, title, folder, added)
                VALUES (?, ?, ?, ?)
            ''', (url, title, folder, now))

    def remove_bookmark(self, url: str):
        with self._get_cursor() as cur:
            cur.execute('DELETE FROM bookmarks WHERE url = ?', (url,))

    def is_bookmarked(self, url: str) -> bool:
        with self._get_cursor() as cur:
            cur.execute('SELECT id FROM bookmarks WHERE url = ?', (url,))
            return cur.fetchone() is not None

    def get_all_bookmarks(self) -> List[Tuple[str, str, str]]:
        with self._get_cursor() as cur:
            cur.execute('SELECT url, title, folder FROM bookmarks ORDER BY folder, title')
            return [(row['url'], row['title'], row['folder']) for row in cur.fetchall()]

    # === Settings ===
    def get_setting(self, key: str, default: Any = None) -> str:
        with self._get_cursor() as cur:
            cur.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cur.fetchone()
            return row['value'] if row else default

    def set_setting(self, key: str, value: str):
        with self._get_cursor() as cur:
            cur.execute('''
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
            ''', (key, value))

    def reset_settings(self):
        with self._get_cursor() as cur:
            cur.execute('DELETE FROM settings')
            default_settings = {
                "startup_page": "0",
                "homepage": "https://www.google.com",
                "search_engine": "google",
                "download_folder": os.path.expanduser("~/Downloads"),
                "theme": "Light",
                "accent_color": "#0078d4",
                "wallpaper": "",
                "random_wallpaper": "false",
                "slideshow_enabled": "false",
                "slideshow_interval": "5",
                "font_size": "9",
                "tracking_protection": "true",
                "block_popups": "true",
                "dev_tools": "false",
                "remote_debug": "false",
                "ad_blocker": "true"
            }
            for key, value in default_settings.items():
                cur.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)', (key, value))

    # === Downloads ===
    def add_download(self, url: str, file_path: str, total_size: int):
        with self._get_cursor() as cur:
            now = int(datetime.now().timestamp())
            cur.execute('''
                INSERT INTO downloads (url, file_path, total_size, start_time)
                VALUES (?, ?, ?, ?)
            ''', (url, file_path, total_size, now))

    def update_download(self, url: str, received_size: int, status: str):
        with self._get_cursor() as cur:
            cur.execute('''
                UPDATE downloads SET received_size = ?, status = ?, end_time = ?
                WHERE url = ?
            ''', (received_size, status, int(datetime.now().timestamp()), url))

    def get_downloads(self) -> List[dict]:
        with self._get_cursor() as cur:
            cur.execute('SELECT * FROM downloads ORDER BY start_time DESC')
            return [dict(row) for row in cur.fetchall()]

    # === Themes ===
    def get_theme(self, name: str) -> Optional[str]:
        with self._get_cursor() as cur:
            cur.execute('SELECT stylesheet FROM themes WHERE name = ?', (name,))
            row = cur.fetchone()
            return row['stylesheet'] if row else None

    def save_theme(self, name: str, stylesheet: str, is_custom: bool = False):
        with self._get_cursor() as cur:
            cur.execute('''
                INSERT OR REPLACE INTO themes (name, stylesheet, is_custom)
                VALUES (?, ?, ?)
            ''', (name, stylesheet, 1 if is_custom else 0))

    # === Sessions ===
    def save_session(self, tabs: List[dict]) -> None:
        """Save current tab session"""
        with self._get_cursor() as cur:
            cur.execute('DELETE FROM sessions')  # Keep only latest session
            cur.execute('INSERT INTO sessions (data, timestamp) VALUES (?, ?)',
                       (json.dumps(tabs), int(datetime.now().timestamp())))

    def load_session(self) -> Optional[List[dict]]:
        """Load saved tab session"""
        with self._get_cursor() as cur:
            cur.execute('SELECT data FROM sessions ORDER BY timestamp DESC LIMIT 1')
            row = cur.fetchone()
            if row:
                return json.loads(row['data'])
        return None

    def get_browsing_stats(self) -> dict:
        """Get browsing statistics"""
        with self._get_cursor() as cur:
            # Total pages visited
            cur.execute('SELECT COUNT(*) FROM history')
            total_pages = cur.fetchone()[0]
            # Pages visited today
            today_start = int(datetime.now().replace(hour=0, minute=0, second=0).timestamp())
            cur.execute('SELECT COUNT(*) FROM history WHERE timestamp >= ?', (today_start,))
            pages_today = cur.fetchone()[0]
            # Most visited sites
            cur.execute('''
                SELECT url, title, COUNT(*) as count
                FROM history
                GROUP BY url
                ORDER BY count DESC
                LIMIT 10
            ''')
            most_visited = [(row['url'], row['title'], row['count']) for row in cur.fetchall()]
            return {
                'total_pages': total_pages,
                'pages_today': pages_today,
                'most_visited': most_visited
            }
