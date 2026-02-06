"""Utility helper functions."""

import os
from typing import Optional


def get_file_extension(filename: str) -> Optional[str]:
    """Extract file extension from filename."""
    if not filename or "." not in filename:
        return None
    return filename.rsplit(".", 1)[-1].lower()


def format_timestamp(seconds: float) -> str:
    """Format seconds into MM:SS string."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"


def ensure_upload_dir(upload_dir: str = "/app/uploads") -> str:
    """Ensure the upload directory exists and return its path."""
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir
