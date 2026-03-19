"""Utility helpers shared across modules."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable


def today_yyyymmdd() -> str:
    """Return today's date in YYYYMMDD format."""

    return datetime.now().strftime("%Y%m%d")


def ensure_directories(paths: Iterable[Path]) -> None:
    """Create directories when they do not exist."""

    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def format_krw(value: int | float) -> str:
    """Format KRW values with comma separators."""

    return f"{int(value):,}"
