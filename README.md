# Market Data Toolkit

Market Data Toolkit is a lightweight Python library and command line interface for downloading and managing historical market prices. It pulls quotes from Yahoo Finance and automatically falls back to Stooq, normalizing the result into tidy OHLCV data ready for analysis or storage.

- [x] Free data sources (no API keys)
- [x] Weekend-safe date handling and symbol suffix mapping
- [x] Retries with backoff before provider fallback
- [x] CSV/Parquet writers that de-duplicate by `Date`
- [x] Optional JSON/YAML watchlist helpers

## Table of Contents
- [✨ Features](#-features)
- [📦 Installation](#-installation)
- [🧪 Running Tests](#-running-tests)
- [🚀 Quick Start](#-quick-start)
  - [Library](#library)
  - [CLI](#cli)
- [🧭 Using a Watchlist](#-using-a-watchlist)
- [🧰 Project Structure](#-project-structure)
- [🗂️ Data Schema](#-data-schema)
- [⚙️ Error Handling & Logging](#-error-handling--logging)
- [📜 License](#-license)

## ✨ Features
- Yahoo → Stooq fallback (free; no API keys)
- Weekend-safe end dates; suffix mapping (`.L→.uk`, `.PA→.fr`, `.MI→.it`, `.DE`, `.HK`)
- Retries/backoff for Yahoo before fallback
- Normalized OHLCV DataFrames; **Adj Close** always included
- CSV/Parquet writers (append + de-dupe by `Date`)
- Small CLIs for terminal use
- Optional JSON/YAML watchlist support

## 📦 Installation

### Windows

1. Download or clone this repository to a folder such as `D:\marketdata-toolkit`.
2. Double‑click `install.bat`.

The script checks for `pip`, creates a `.venv` virtual environment, upgrades packaging tools, and installs the project in editable mode.

After installation, activate the environment in a new Command Prompt:

```bat
call .venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip wheel
pip install -e .
```

Optional extras:

```bash
pip install -e .[parquet]   # Parquet support
pip install -e .[yaml]      # YAML watchlists
```

## 🧪 Running Tests
Run the test suite to verify that both the library and CLI are working. The
tests simulate downloads and write to temporary CSV files.

```bash
pytest
```

## 🚀 Quick Start
### Library
```python
from marketdata.prices import get_prices, get_latest_close

# Fetch OHLCV for multiple tickers
bars = get_prices(["ABEO", "BP.L"], start="2025-06-01", end="2025-09-05")
print(bars["ABEO"].tail())

# Latest official close
asof, px = get_latest_close("ABEO")
print(asof.date(), px)
```

### CLI
The `prices` command either prints data to the terminal or writes it to disk.
Tickers may be supplied directly or via a JSON/YAML watchlist file using
`--config` and `--group`.

**Display on screen**

```bash
# compact summary
prices --tickers AAPL MSFT --start 2024-01-01 --end 2024-06-01

# full table output
prices --tickers AAPL MSFT --start 2024-01-01 --end 2024-06-01 --table
```

**Write CSV/Parquet**

```bash
# create data/ if missing and append new rows when incremental
prices --tickers AAPL MSFT --start 2024-01-01 --end 2024-06-01 --out-dir data --incremental

# Parquet instead of CSV
prices --tickers AAPL MSFT --start 2024-01-01 --end 2024-06-01 --out-dir data --format parquet
```

Multiple tickers may be separated by spaces or commas. On Windows, run the
commands exactly as shown—do not include leading `#` characters, which are used
as comments in Unix examples.

## 🧭 Using a Watchlist
Maintain a watchlist and generate JSON/YAML files for downstream tools.
```bash
watchlist-update \
  --portfolio data/chatgpt_portfolio_update.csv \
  --trades data/chatgpt_trade_log.csv \
  --extras config/static_extras.json \
  --out config/tickers.json
```
Then fetch prices using that watchlist:
```bash
prices --config config/tickers.json --group watchlist \
  --start 2025-06-01 --end 2025-09-05 \
  --out-dir data/ohlcv
```

## 🧰 Project Structure
```bash
marketdata-toolkit/
├── marketdata/
│   ├── __init__.py
│   └── prices.py
├── watchlist/
│   ├── __init__.py
│   └── update_watchlist.py
├── config/
│   ├── static_extras.json.example
│   └── tickers.json.example
├── tests/
│   ├── test_prices.py
│   └── test_watchlist.py
├── pyproject.toml
└── README.md
```

## 🗂️ Data Schema
Normalized output columns:

| Column | Description |
|--------|-------------|
| Date   | Trading day |
| Open   | Opening price |
| High   | Session high |
| Low    | Session low |
| Close  | Closing price |
| Adj Close | Adjusted close |
| Volume | Trading volume |
| Ticker | Symbol identifier |
| Source | Data provider (yahoo or stooq) |

## ⚙️ Error Handling & Logging
- Retries with exponential backoff before falling back to Stooq
- Graceful handling of weekend dates and symbol suffixes
- Logging through Python's standard `logging` module
Error policy: --on-error raise|warn|ignore (default = warn in CLI, raise in library)

- Logging levels:
- **INFO** → successful fetch
- **WARNING** → Yahoo failed, fell back to Stooq
- **ERROR** → all sources failed
```bash
prices --tickers ABEO --start 2025-06-01 --end 2025-09-05 --log-level INFO
```

## 📜 License
This project is licensed under the MIT License.
