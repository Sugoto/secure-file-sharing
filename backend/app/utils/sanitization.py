import re
import html
from typing import Any, Union


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and invalid characters."""
    filename = re.sub(r"[/\\]", "", filename)
    filename = filename.replace("\0", "")
    filename = re.sub(r"[^a-zA-Z0-9\-_. ]", "", filename)
    return filename.strip()


def sanitize_input(input_str: Union[str, Any]) -> str:
    """Sanitize general input string."""
    if not isinstance(input_str, str):
        return str(input_str)
    input_str = html.escape(input_str)
    input_str = re.sub(r'[;\'"\\]', "", input_str)
    return input_str.strip()


def sanitize_token(token: str) -> str:
    """Sanitize share token to ensure it only contains valid characters."""
    return re.sub(r"[^a-zA-Z0-9\-]", "", token)
