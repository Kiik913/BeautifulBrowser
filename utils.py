"""
Utils - Helper functions for URL parsing, resource paths, etc.
"""

import os
import sys
import re
from urllib.parse import urlparse


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def is_url(text: str) -> bool:
    """Check if text is a valid URL"""
    if re.match(r'^https?://', text, re.I):
        return True
    if re.match(r'^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(/.*)?$', text):
        return True
    return False


def format_url(url: str) -> str:
    """Ensure URL has scheme"""
    if not url:
        return ""
    if not re.match(r'^https?://', url, re.I):
        return "http://" + url
    return url


def get_domain(url: str) -> str:
    """Extract domain from URL"""
    parsed = urlparse(url)
    return parsed.netloc or parsed.path


def safe_filename(name: str) -> str:
    """Sanitize string for file name"""
    return re.sub(r'[\\/*?:"<>|]', "", name)[:100]
