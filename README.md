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
Use a virtual environment and install in editable mode from the project root (where `pyproject.toml` is located).

### Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip setuptools wheel

# core package
pip install -e .

# optional extras
pip install -e .[parquet]   # Parquet support
pip install -e .[yaml]      # YAML watchlists
```

### Windows (PowerShell)
```bash
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip setuptools wheel

# core package
pip install -e .

# optional extras
pip install -e .[parquet]   # Parquet support
pip install -e .[yaml]      # YAML watchlists
```

## 🧪 Running Tests
```bash
pytest
```

## 🚀 Quick Start
### Library
```python
from marketdata.prices import fetch

# Fetch prices for multiple tickers
prices = fetch(["AAPL", "MSFT"], start="2024-01-01", end="2024-06-01")
print(prices.head())
```

### CLI
```bash
# Download prices to CSV
prices --tickers AAPL MSFT --start 2024-01-01 --end 2024-06-01 --out data.csv
```

## 🧭 Using a Watchlist
Maintain a watchlist and generate JSON/YAML files for downstream tools.
```bash
watchlist-update --portfolio portfolio.csv --trades trades.csv \
  --extras config/static_extras.json --out tickers.json
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

## ⚙️ Error Handling & Logging
- Retries with exponential backoff before falling back to Stooq
- Graceful handling of weekend dates and symbol suffixes
- Logging through Python's standard `logging` module

## 📜 License
This project is licensed under the MIT License.
