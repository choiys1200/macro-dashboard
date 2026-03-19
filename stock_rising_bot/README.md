# Daily Rising Stocks Summary Automation (Korean Market) - MVP v1

## 1) Project Purpose
This project is a local Python MVP that automates a daily "rising stocks" summary workflow for the Korean stock market.

It performs the following tasks:
1. Collects same-day OHLCV snapshot data for KOSPI/KOSDAQ using `pykrx`.
2. Filters stocks by configurable conditions (daily change %, trade value).
3. Separately saves raw data, processed data, and final report outputs.
4. Generates CSV + Markdown daily summary outputs.
5. Prints a concise summary in the console.

> Scope is intentionally small and modular so it can be extended later with DART/news/Telegram/blog posting.

---

## 2) Folder Structure

```text
stock_rising_bot/
├─ README.md
├─ requirements.txt
├─ .env.example
├─ .gitignore
├─ main.py
├─ config/
│  ├─ __init__.py
│  └─ settings.py
├─ modules/
│  ├─ __init__.py
│  ├─ market_collector.py
│  ├─ stock_filter.py
│  ├─ reporter.py
│  └─ utils.py
├─ data/
│  ├─ raw/
│  ├─ processed/
│  └─ output/
├─ logs/
└─ tests/
```

---

## 3) Installation

### Prerequisites
- Python 3.11+
- Internet connection (for `pykrx` data collection)

### Setup Steps

```bash
# 1) Move into project
cd stock_rising_bot

# 2) Create virtual environment
python -m venv .venv

# 3) Activate virtual environment
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

# 4) Install dependencies
pip install -r requirements.txt
```

---

## 4) Environment Variables (.env)

### Create `.env`

Copy from the example file:

```bash
cp .env.example .env
```

### Example `.env`

```env
CHANGE_PCT_THRESHOLD=10.0
TRADE_VALUE_THRESHOLD=10000000000
TARGET_MARKET=ALL
```

### Variable Meanings
- `CHANGE_PCT_THRESHOLD`: minimum daily change percentage (e.g., `10.0` means +10% or higher)
- `TRADE_VALUE_THRESHOLD`: minimum daily trade value in KRW
- `TARGET_MARKET`: `KOSPI`, `KOSDAQ`, or `ALL`

---

## 5) Run

From the project root (`stock_rising_bot/`):

```bash
python main.py
```

The script uses today's date (`YYYYMMDD`) by default and writes dated output files.

---

## 6) Output Files

After execution, files are generated as follows:

- `data/raw/raw_market_data_YYYYMMDD.csv`
  - Full collected market data (raw)
- `data/processed/filtered_rising_stocks_YYYYMMDD.csv`
  - Filtered rising stocks (processed)
- `data/output/daily_summary_YYYYMMDD.md`
  - Human-readable summary report

### Markdown Report Format
- Title with date
- Filter conditions
- Result count
- Matched stock table with:
  - Ticker
  - Name
  - Market
  - Change %
  - Trade Value

If nothing matches, the report explicitly states that no stocks matched.

---

## 7) Notes on `pykrx` Dependency / Risks

- `pykrx` is the primary source for Korean stock data in this MVP.
- Data availability can vary by trading day/holiday/time of execution.
- Occasionally, upstream API/schema changes can affect data collection.
- For production hardening, consider:
  - retries/backoff
  - fallback data source
  - stricter schema validation and alerting

---

## 8) Extension Ideas (Out of Scope for MVP v1)
The architecture is split by concern (`collector`, `filter`, `reporter`) so it can be extended later with minimal refactoring:
- DART fundamentals/disclosures
- news crawling and ranking
- Telegram/bot notifications
- scheduled execution (cron, Airflow, etc.)
- DB persistence and historical analytics
