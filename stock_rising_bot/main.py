"""Entry point for daily rising stocks summary automation MVP."""

from __future__ import annotations

import sys

from config.settings import load_settings
from modules.market_collector import MarketCollector
from modules.reporter import Reporter
from modules.stock_filter import StockFilter
from modules.utils import ensure_directories, format_krw, today_yyyymmdd


def run() -> int:
    """Run end-to-end stock data collection, filtering, and reporting."""

    settings = load_settings()
    date_yyyymmdd = today_yyyymmdd()

    ensure_directories(
        [
            settings.data_raw_dir,
            settings.data_processed_dir,
            settings.data_output_dir,
            settings.logs_dir,
        ]
    )

    collector = MarketCollector(target_market=settings.target_market)
    stock_filter = StockFilter(
        change_pct_threshold=settings.change_pct_threshold,
        trade_value_threshold=settings.trade_value_threshold,
    )
    reporter = Reporter()

    print(f"[INFO] Running for date: {date_yyyymmdd}")
    print(f"[INFO] Target market: {settings.target_market}")

    raw_df = collector.collect(date_yyyymmdd)
    filtered_df = stock_filter.filter_rising(raw_df)

    raw_path = reporter.save_raw_csv(raw_df, settings.data_raw_dir, date_yyyymmdd)
    processed_path = reporter.save_processed_csv(filtered_df, settings.data_processed_dir, date_yyyymmdd)

    markdown_content = reporter.build_markdown_summary(
        df=filtered_df,
        date_yyyymmdd=date_yyyymmdd,
        change_pct_threshold=settings.change_pct_threshold,
        trade_value_threshold=settings.trade_value_threshold,
    )
    report_path = reporter.save_markdown(markdown_content, settings.data_output_dir, date_yyyymmdd)

    print("\n=== Daily Rising Stocks Summary ===")
    print(f"Date: {date_yyyymmdd}")
    print(f"Filter - Change % >= {settings.change_pct_threshold}")
    print(f"Filter - Trade Value >= {format_krw(settings.trade_value_threshold)} KRW")
    print(f"Matched stocks: {len(filtered_df)}")
    print(f"Raw CSV: {raw_path}")
    print(f"Processed CSV: {processed_path}")
    print(f"Markdown Report: {report_path}")

    if not filtered_df.empty:
        preview_cols = ["ticker", "name", "market", "change_pct", "trade_value"]
        print("\nTop matched stocks:")
        print(filtered_df[preview_cols].head(10).to_string(index=False))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(run())
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        raise SystemExit(130)
    except Exception as exc:  # broad catch for CLI stability
        print(f"[ERROR] Execution failed: {exc}")
        raise SystemExit(1)
