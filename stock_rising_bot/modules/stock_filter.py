"""Filter logic for rising stocks."""

from __future__ import annotations

import pandas as pd


class StockFilter:
    """Apply configurable stock filtering conditions."""

    def __init__(self, change_pct_threshold: float, trade_value_threshold: int) -> None:
        self.change_pct_threshold = change_pct_threshold
        self.trade_value_threshold = trade_value_threshold

    def filter_rising(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return rows matching both change % and trade value criteria."""

        if df.empty:
            return df.copy()

        working_df = df.copy()
        working_df["change_pct"] = pd.to_numeric(working_df["change_pct"], errors="coerce")
        working_df["trade_value"] = pd.to_numeric(working_df["trade_value"], errors="coerce")

        filtered = working_df[
            (working_df["change_pct"] >= self.change_pct_threshold)
            & (working_df["trade_value"] >= self.trade_value_threshold)
        ].copy()

        return filtered.sort_values(by=["change_pct", "trade_value"], ascending=[False, False]).reset_index(drop=True)
