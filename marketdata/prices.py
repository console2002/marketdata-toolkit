from __future__ import annotations

import argparse
import logging
import os
import sys
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
    """Fetch daily OHLCV bars via yfinance."""
    start_dt = pd.Timestamp(start)
    end_dt = _weekend_safe_end(pd.Timestamp(end))
    data: Dict[str, pd.DataFrame] = {}
    for t in tickers:
        try:
            df = yf.download(t, start=start_dt, end=end_dt + pd.Timedelta(days=1), progress=False)
            if not df.empty:
                df = df.rename(columns=str.title).assign(Source="yahoo")
                df.reset_index(inplace=True)
            data[t] = df
        except Exception as e:  # pragma: no cover - network failures
            msg = f"{t}: {e}"
            if on_error == "raise":
                raise
            if on_error == "warn":
                log.warning(msg)
            data[t] = pd.DataFrame()
    return data


def save_prices_csv(bars: Dict[str, pd.DataFrame], out_dir: str, incremental: bool = True) -> List[str]:
    paths: List[str] = []
    os.makedirs(out_dir, exist_ok=True)
    for t, df in bars.items():
        if df.empty:
            continue
        path = f"{out_dir}/{t.replace('^','_')}_D.csv"
        try:
            if incremental:
                try:
                    old = pd.read_csv(path, parse_dates=["Date"])
                    df = pd.concat([old, df], ignore_index=True)
                except FileNotFoundError:
                    pass
            df = df.drop_duplicates(subset=["Date"], keep="last").sort_values("Date")
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
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--out-dir", "--out", dest="out_dir", default="")
    p.add_argument("--format", choices=["csv", "parquet"], default="csv")
    p.add_argument("--on-error", choices=["raise", "warn", "ignore"], default="warn")
    p.add_argument("--incremental", action="store_true")
    p.add_argument("--log-level", default="INFO")

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
    tickers = sorted(set(tickers))
    if not tickers:
        p.error("No tickers provided. Use --tickers.")

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
            src = df["Source"].iloc[-1] if not df.empty else "NA"
            print(f"{t}: rows={len(df)} source={src}")
        successes = sum(1 for df in bars.values() if not df.empty)

    return 0 if successes > 0 else 2


def cli() -> None:  # console_scripts entrypoint
    sys.exit(main())


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
