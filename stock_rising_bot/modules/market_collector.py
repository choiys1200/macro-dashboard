"""Collect daily Korean market data with pykrx."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
from pykrx import stock

KOREAN_TO_ENGLISH_COLUMNS = {
    "시가": "open",
    "고가": "high",
    "저가": "low",
    "종가": "close",
    "거래량": "volume",
    "거래대금": "trade_value",
    "등락률": "change_pct",
}

REQUIRED_COLUMNS = ["ticker", "name", "market", "open", "high", "low", "close", "volume", "trade_value", "change_pct"]


class MarketCollector:
    """Collector for KOSPI/KOSDAQ OHLCV snapshot data."""

    def __init__(self, target_market: str) -> None:
        self.target_market = target_market

    def _resolve_markets(self) -> Iterable[str]:
        if self.target_market == "ALL":
            return ["KOSPI", "KOSDAQ"]
        return [self.target_market]

    @staticmethod
    def _normalize_base_frame(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize pykrx output into stable internal column names."""

        normalized = df.reset_index().copy()

        # pykrx index column can be named differently depending on version/environment.
        if "티커" in normalized.columns:
            normalized = normalized.rename(columns={"티커": "ticker"})
        elif "index" in normalized.columns:
            normalized = normalized.rename(columns={"index": "ticker"})

        normalized = normalized.rename(columns=KOREAN_TO_ENGLISH_COLUMNS)

        if "ticker" not in normalized.columns:
            raise ValueError("Failed to identify ticker column from pykrx response")

        for col in ["open", "high", "low", "close", "volume", "trade_value", "change_pct"]:
            if col not in normalized.columns:
                normalized[col] = 0

        return normalized[["ticker", "open", "high", "low", "close", "volume", "trade_value", "change_pct"]].copy()

    def _collect_market(self, date_yyyymmdd: str, market: str) -> pd.DataFrame:
        """Collect one market's OHLCV and normalize column names."""

        df = stock.get_market_ohlcv_by_ticker(date_yyyymmdd, market=market)
        if df.empty:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)

        normalized = self._normalize_base_frame(df)
        normalized["ticker"] = normalized["ticker"].astype(str).str.zfill(6)
        normalized["market"] = market
        normalized["name"] = normalized["ticker"].map(stock.get_market_ticker_name)

        ordered = normalized[["ticker", "name", "market", "open", "high", "low", "close", "volume", "trade_value", "change_pct"]]
        ordered["change_pct"] = pd.to_numeric(ordered["change_pct"], errors="coerce")
        ordered["trade_value"] = pd.to_numeric(ordered["trade_value"], errors="coerce")
        return ordered

    def collect(self, date_yyyymmdd: str) -> pd.DataFrame:
        """Collect target market data for a specific date."""

        frames = [self._collect_market(date_yyyymmdd, market) for market in self._resolve_markets()]
        valid_frames = [frame for frame in frames if not frame.empty]
        if not valid_frames:
            return pd.DataFrame(columns=REQUIRED_COLUMNS)

        return pd.concat(valid_frames, ignore_index=True)[REQUIRED_COLUMNS]
