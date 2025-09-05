from __future__ import annotations
# Persistence helpers
# --------------------------------------------------------------------------------------


def save_prices_csv(bars: Dict[str, pd.DataFrame], out_dir: str, incremental: bool = True) -> List[str]:
paths: List[str] = []
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
except Exception as e:
log.error("%s: failed to write %s (%s)", t, path, str(e))
return paths




def save_prices_parquet(bars: Dict[str, pd.DataFrame], out_dir: str) -> List[str]:
paths: List[str] = []
for t, df in bars.items():
if df.empty:
continue
path = f"{out_dir}/{t.replace('^','_')}_D.parquet"
try:
df.to_parquet(path, index=False)
paths.append(path)
log.info("%s: wrote %s (%d rows)", t, path, len(df))
except Exception as e:
log.error("%s: failed to write %s (%s)", t, path, str(e))
return paths




# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
p = argparse.ArgumentParser(prog="prices", description="Fetch OHLCV via Yahoo/stooq, save optional CSV/Parquet.")
p.add_argument("--tickers", help="Comma-separated symbols (Yahoo format)")
p.add_argument("--config", help="JSON/YAML file with tickers and optional groups")
p.add_argument("--group", help="Group name inside config (e.g., watchlist)")
p.add_argument("--start", required=True)
p.add_argument("--end", required=True)
p.add_argument("--out-dir", default="")
p.add_argument("--format", choices=["csv", "parquet"], default="csv")
p.add_argument("--on-error", choices=["raise", "warn", "ignore"], default="warn")
p.add_argument("--incremental", action="store_true")
p.add_argument("--log-level", default="INFO")


args = p.parse_args(argv)
logging.getLogger(__name__).setLevel(getattr(logging, args.log_level.upper(), logging.INFO))


tickers: list[str] = []
if args.tickers:
tickers.extend([t.strip().upper() for t in args.tickers.split(",") if t.strip()])
if args.config:
tickers.extend(_load_config_symbols(args.config, args.group))
tickers = sorted({t for t in tickers if t})
if not tickers:
p.error("No tickers provided. Use --tickers or --config [--group].")


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




def cli() -> None: # console_scripts entrypoint
sys.exit(main())




if __name__ == "__main__": # python -m marketdata.prices
sys.exit(main())
