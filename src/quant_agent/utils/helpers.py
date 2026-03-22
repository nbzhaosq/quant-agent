"""Utility helper functions."""

from datetime import datetime
from typing import Any


def format_number(value: float | int | None, decimal: int = 2) -> str:
    """Format large numbers with Chinese units."""
    if value is None:
        return "N/A"

    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1e8:
        return f"{sign}{abs_value / 1e8:.{decimal}f}亿"
    elif abs_value >= 1e4:
        return f"{sign}{abs_value / 1e4:.{decimal}f}万"
    else:
        return f"{sign}{abs_value:.{decimal}f}"


def format_percent(value: float | None, decimal: int = 2) -> str:
    """Format percentage values."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimal}f}%"


def format_date(date_str: str) -> str:
    """Format date string from YYYYMMDD to YYYY-MM-DD."""
    if not date_str:
        return "N/A"
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get nested dictionary values."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data
