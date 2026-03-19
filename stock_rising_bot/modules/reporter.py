"""Output generation for CSV and Markdown reports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from modules.utils import format_krw


class Reporter:
    """Persist pipeline outputs and render a readable markdown summary."""

    def save_raw_csv(self, df: pd.DataFrame, output_dir: Path, date_yyyymmdd: str) -> Path:
        output_path = output_dir / f"raw_market_data_{date_yyyymmdd}.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    def save_processed_csv(self, df: pd.DataFrame, output_dir: Path, date_yyyymmdd: str) -> Path:
        output_path = output_dir / f"filtered_rising_stocks_{date_yyyymmdd}.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    @staticmethod
    def _build_markdown_table(df: pd.DataFrame) -> list[str]:
        """Build markdown table lines without optional third-party dependencies."""

        lines = [
            "| Ticker | Name | Market | Change % | Trade Value |",
            "|--------|------|--------|----------|-------------|",
        ]

        for _, row in df.iterrows():
            lines.append(
                "| {ticker} | {name} | {market} | {change_pct:.2f} | {trade_value} |".format(
                    ticker=row["ticker"],
                    name=row["name"],
                    market=row["market"],
                    change_pct=float(row["change_pct"]),
                    trade_value=format_krw(float(row["trade_value"])),
                )
            )

        return lines

    def build_markdown_summary(
        self,
        df: pd.DataFrame,
        date_yyyymmdd: str,
        change_pct_threshold: float,
        trade_value_threshold: int,
    ) -> str:
        lines: list[str] = [
            f"# Daily Rising Stocks Summary - {date_yyyymmdd}",
            "",
            "## Filter Conditions",
            f"- Change % >= {change_pct_threshold}",
            f"- Trade Value >= {format_krw(trade_value_threshold)} KRW",
            "",
            "## Result Summary",
            f"- Total matched stocks: {len(df)}",
            "",
            "## Stocks",
        ]

        if df.empty:
            lines.extend(["", "No stocks matched the configured conditions today."])
            return "\n".join(lines)

        display_df = df[["ticker", "name", "market", "change_pct", "trade_value"]].copy()
        lines.extend(self._build_markdown_table(display_df))
        return "\n".join(lines)

    def save_markdown(self, content: str, output_dir: Path, date_yyyymmdd: str) -> Path:
        output_path = output_dir / f"daily_summary_{date_yyyymmdd}.md"
        output_path.write_text(content, encoding="utf-8")
        return output_path
