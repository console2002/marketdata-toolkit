from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List

import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)


def _stooq_symbol(symbol: str) -> str:
    """Map Yahoo-style symbols to stooq symbols."""
    parts = symbol.split(".")
    if len(parts) == 2:
        ticker, suffix = parts
        mapping = {"L": "uk", "PA": "fr", "MI": "it"}
        return f"{ticker.lower()}.{mapping.get(suffix.upper(), suffix.lower())}"
    return f"{symbol.lower()}.us"


def _weekend_safe_end(end: pd.Timestamp) -> pd.Timestamp:
    """Return the previous business day if ``end`` falls on a weekend."""
    while end.weekday() > 4:
        end -= pd.Timedelta(days=1)
    return end


def get_prices(
    tickers: List[str],
    start: str,
    end: str,
    *,
    on_error: str = "warn",
) -> Dict[str, pd.DataFrame]:
    """Fetch daily OHLCV bars via Yahoo with Stooq fallback."""
    start_dt = pd.Timestamp(start)
    end_dt = _weekend_safe_end(pd.Timestamp(end))
    data: Dict[str, pd.DataFrame] = {}
    for t in tickers:
        df = pd.DataFrame()
        src = ""
        last_err = None
        for attempt in range(3):
            try:
                df = yf.download(
                    t,
                    start=start_dt,
                    end=end_dt + pd.Timedelta(days=1),
                    progress=False,
                    auto_adjust=False,
                )
                src = "yahoo"
                break
            except Exception as e:  # pragma: no cover - network failures
                last_err = e
                log.debug("%s: yahoo attempt %d failed (%s)", t, attempt + 1, e)
                time.sleep(2**attempt)
        else:
            if last_err is not None:
                log.warning("%s: yahoo fetch failed (%s)", t, last_err)

        if df.empty:
            try:
                sym = _stooq_symbol(t)
                sdf = pd.read_csv(f"https://stooq.com/q/d/l/?s={sym}&i=d")
                sdf["Date"] = pd.to_datetime(sdf["Date"])
                sdf = sdf[(sdf["Date"] >= start_dt) & (sdf["Date"] <= end_dt)]
                if not sdf.empty:
                    sdf = sdf.rename(columns=str.title)
                    sdf["Adj Close"] = sdf["Close"]
                    df = sdf
                    src = "stooq"
            except Exception as e:  # pragma: no cover - network failures
                msg = f"{t}: {e}"
                if on_error == "raise":
                    raise
                if on_error == "warn":
                    log.warning(msg)
                data[t] = pd.DataFrame()
                continue

        if not df.empty:
            if "Date" not in df.columns:
                df.reset_index(inplace=True)
            df = df.rename(columns=str.title)
            df = df.assign(Ticker=t.upper(), Source=src)
            cols = [
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Adj Close",
                "Volume",
                "Ticker",
                "Source",
            ]
            df = df[cols]
        data[t] = df
    return data


def get_latest_close(ticker: str, *, on_error: str = "warn") -> tuple[pd.Timestamp, float]:
    """Return the latest official close for ``ticker``.

    A small window is fetched to cover weekends and holidays. Raises
    ``ValueError`` if no data is returned.
    """
    today = pd.Timestamp.today().normalize()
    start = today - pd.Timedelta(days=7)
    bars = get_prices([ticker], start=str(start.date()), end=str(today.date()), on_error=on_error)
    df = bars.get(ticker, pd.DataFrame())
    if df.empty:
        raise ValueError(f"No data for {ticker}")
    last = df.iloc[-1]
    return last["Date"], float(last["Close"])


def save_prices_csv(bars: Dict[str, pd.DataFrame], out_dir: str, incremental: bool = True) -> List[str]:
    paths: List[str] = []
    os.makedirs(out_dir, exist_ok=True)
    for t, df in bars.items():
        if df.empty:
            continue

        if "Date" not in df.columns:
            if df.index.name == "Date":
                df = df.reset_index()
            else:  # pragma: no cover - unexpected schema
                log.error("%s: missing 'Date' column", t)
                continue

        path = f"{out_dir}/{t.replace('^','_')}_D.csv"
        try:
            if incremental:
                try:
                    old = pd.read_csv(path, parse_dates=["Date"])
                    if "Date" not in old.columns and old.index.name == "Date":
                        old = old.reset_index()
                except Exception:  # FileNotFoundError or malformed file
                    old = pd.DataFrame()
                if not old.empty:
                    df = pd.concat([old, df], ignore_index=True)
                if "Date" not in df.columns and df.index.name == "Date":
                    df = df.reset_index()
                if "Date" not in df.columns:
                    log.error("%s: missing 'Date' column", t)
                    continue
            cols = [
                "Date",
                "Open",
                "High",
                "Low",
                "Close",
                "Adj Close",
                "Volume",
                "Ticker",
                "Source",
            ]
            df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
            df = df.reindex(columns=cols)
            df.to_csv(path, index=False)
            paths.append(path)
            log.info("%s: wrote %s (%d rows)", t, path, len(df))
        except Exception as e:  # pragma: no cover - filesystem failures
            log.error("%s: failed to write %s (%s)", t, path, str(e))
    return paths


def save_prices_parquet(bars: Dict[str, pd.DataFrame], out_dir: str) -> List[str]:
    paths: List[str] = []
    os.makedirs(out_dir, exist_ok=True)
    for t, df in bars.items():
        if df.empty:
            continue
        path = f"{out_dir}/{t.replace('^','_')}_D.parquet"
        try:
            df.to_parquet(path, index=False)
            paths.append(path)
            log.info("%s: wrote %s (%d rows)", t, path, len(df))
        except Exception as e:  # pragma: no cover
            log.error("%s: failed to write %s (%s)", t, path, str(e))
    return paths


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="prices",
        description="Fetch OHLCV via Yahoo and save optional CSV/Parquet.",
    )
    p.add_argument(
        "--tickers",
        nargs="+",
        help="Symbols (Yahoo format). Separate with spaces or commas.",
    )
    p.add_argument("--config", help="JSON/YAML watchlist file")
    p.add_argument("--group", default="watchlist", help="Group name in watchlist config")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--out-dir", "--out", dest="out_dir", default="")
    p.add_argument("--format", choices=["csv", "parquet"], default="csv")
    p.add_argument("--on-error", choices=["raise", "warn", "ignore"], default="warn")
    p.add_argument("--incremental", action="store_true")
    p.add_argument("--log-level", default="INFO")
    p.add_argument("--table", action="store_true", help="Print full tables instead of a summary")

    args = p.parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    if args.out_dir and args.out_dir.endswith(".csv"):
        p.error("--out-dir expects a directory, not a file name")

    tickers: List[str] = []
    if args.tickers:
        for group in args.tickers:
            tickers.extend(
                [t.strip().upper() for t in group.split(",") if t.strip()]
            )
    if args.config:
        with open(args.config, "r", encoding="utf-8") as fh:
            if args.config.lower().endswith((".yaml", ".yml")):
                try:
                    import yaml  # type: ignore
                except ImportError as e:  # pragma: no cover - optional dep
                    p.error("PyYAML required for YAML configs")
                cfg = yaml.safe_load(fh)
            else:
                cfg = json.load(fh)
        groups = cfg.get("groups", {})
        if args.group and args.group in groups:
            tickers.extend(groups[args.group])
        else:
            tickers.extend(cfg.get("tickers", []))
    tickers = sorted({t.strip().upper() for t in tickers if t})
    if not tickers:
        p.error("No tickers provided. Use --tickers or --config.")

    bars = get_prices(tickers, start=args.start, end=args.end, on_error=args.on_error)

    successes = 0
    if args.out_dir:
        if args.format == "csv":
            paths = save_prices_csv(bars, out_dir=args.out_dir, incremental=args.incremental)
        else:
            paths = save_prices_parquet(bars, out_dir=args.out_dir)
        print("Saved:", paths)
        successes = len(paths)
    else:
        for t, df in bars.items():
            if args.table:
                if df.empty:
                    print(f"{t}: no data")
                else:
                    print(f"{t}:")
                    print(df.to_string(index=False))
            else:
                src = df["Source"].iloc[-1] if not df.empty else "NA"
                print(f"{t}: rows={len(df)} source={src}")
        successes = sum(1 for df in bars.values() if not df.empty)

    return 0 if successes > 0 else 2


def cli() -> None:  # console_scripts entrypoint
    sys.exit(main())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
