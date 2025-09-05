# marketdata-toolkit

Free/no-key market data fetcher with Yahoo primary, Stooq fallback. Optional watchlist generator from portfolio/trade CSVs. Includes small CLIs for terminal use.

## Install
```bash
pip install -e .
# optional extras
pip install -e .[parquet]
pip install -e .[yaml]
```

## Quick start (library)
```python
from marketdata.prices import get_prices, get_latest_close
bars = get_prices(["ABEO", "BP.L"], start="2025-06-01", end="2025-09-05")
print(bars["ABEO"].tail())
print(get_latest_close("ABEO"))
```

## Quick start (CLI)
```bash
prices --tickers ABEO,BP.L --start 2025-06-01 --end 2025-09-05
prices --tickers ABEO,BP.L --start 2025-06-01 --end 2025-09-05 --out-dir data/ohlcv --format csv --incremental
```

## Using a JSON/YAML watchlist
```bash
watchlist-update --portfolio data/chatgpt_portfolio_update.csv --trades data/chatgpt_trade_log.csv --extras config/static_extras.json --out config/tickers.json
prices --config config/tickers.json --group watchlist --start 2025-06-01 --end 2025-09-05 --out-dir data/ohlcv
```

## Schema
All OHLCV DataFrames/CSVs include:
Date, Open, High, Low, Close, Adj Close, Volume, Source, Currency, Timezone, Ticker, SchemaVer

## License
MIT
