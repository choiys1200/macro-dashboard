"""Application settings loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the stock rising bot."""

    project_root: Path
    data_raw_dir: Path
    data_processed_dir: Path
    data_output_dir: Path
    logs_dir: Path
    change_pct_threshold: float
    trade_value_threshold: int
    target_market: str


def _parse_market(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in {"ALL", "KOSPI", "KOSDAQ"}:
        raise ValueError("TARGET_MARKET must be one of: ALL, KOSPI, KOSDAQ")
    return normalized


def load_settings() -> Settings:
    """Load environment variables and return validated settings."""

    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    load_dotenv(env_path if env_path.exists() else None)

    change_pct_threshold = float(os.getenv("CHANGE_PCT_THRESHOLD", "10.0"))
    trade_value_threshold = int(os.getenv("TRADE_VALUE_THRESHOLD", "10000000000"))
    target_market = _parse_market(os.getenv("TARGET_MARKET", "ALL"))

    data_dir = project_root / "data"

    return Settings(
        project_root=project_root,
        data_raw_dir=data_dir / "raw",
        data_processed_dir=data_dir / "processed",
        data_output_dir=data_dir / "output",
        logs_dir=project_root / "logs",
        change_pct_threshold=change_pct_threshold,
        trade_value_threshold=trade_value_threshold,
        target_market=target_market,
    )
