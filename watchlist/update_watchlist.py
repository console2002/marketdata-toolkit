from __future__ import annotations
portfolio_csv: str = "data/chatgpt_portfolio_update.csv",
trade_log_csv: Optional[str] = "data/chatgpt_trade_log.csv",
static_extras_json: Optional[str] = "config/static_extras.json",
out_json: str = "config/tickers.json",
recent_trade_days: int = 7,
retention_days: int = 5,
) -> dict:
port = _read_csv_safe(portfolio_csv)
trades = _read_csv_safe(trade_log_csv) if trade_log_csv else pd.DataFrame()
extras = _read_static_extras(static_extras_json)


tickers: set[str] = set()


if not port.empty:
latest_date = pd.to_datetime(port["Date"]).max()
latest = port[port["Date"] == latest_date]
active = latest[(latest["Ticker"].str.upper() != "TOTAL") & (latest.get("Shares", 0) > 0)]
tickers.update(active["Ticker"].astype(str).str.upper().tolist())


if retention_days > 0:
cutoff = latest_date - pd.Timedelta(days=retention_days)
recent_hist = port[(port["Ticker"].str.upper() != "TOTAL") & (port["Date"] >= cutoff)]
tickers.update(recent_hist["Ticker"].astype(str).str.upper().tolist())


if not trades.empty and "Date" in trades.columns and "Ticker" in trades.columns:
tmax = pd.to_datetime(trades["Date"]).max()
tcut = tmax - pd.Timedelta(days=recent_trade_days)
recent_trades = trades[trades["Date"] >= tcut]
tickers.update(recent_trades["Ticker"].astype(str).str.upper().tolist())


tickers.update(extras)
tickers = sorted({t for t in tickers if t and t != "TOTAL"})


payload = {
"last_updated": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
"tickers": tickers,
"groups": {
"benchmarks": [t for t in ["SPY", "IWM", "XBI"] if t in tickers],
"watchlist": tickers,
},
"sources": {
"portfolio_file": portfolio_csv,
"trade_log_file": trade_log_csv,
"static_extras_file": static_extras_json,
},
}


os.makedirs(os.path.dirname(out_json) or ".", exist_ok=True)
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as tmp:
json.dump(payload, tmp, indent=2)
tmp_path = tmp.name
shutil.move(tmp_path, out_json)
return payload




def main(argv: list[str] | None = None) -> int:
ap = argparse.ArgumentParser(prog="watchlist-update", description="Derive tickers.json from portfolio/trade CSVs.")
ap.add_argument("--portfolio", default="data/chatgpt_portfolio_update.csv")
ap.add_argument("--trades", default="data/chatgpt_trade_log.csv")
ap.add_argument("--extras", default="config/static_extras.json")
ap.add_argument("--out", default="config/tickers.json")
ap.add_argument("--recent-trade-days", type=int, default=7)
ap.add_argument("--retention-days", type=int, default=5)
args = ap.parse_args(argv)


out = update_watchlist(
portfolio_csv=args.portfolio,
trade_log_csv=args.trades,
static_extras_json=args.extras,
out_json=args.out,
recent_trade_days=args.recent_trade_days,
retention_days=args.retention_days,
)
print(json.dumps(out, indent=2))
return 0




if __name__ == "__main__":
raise SystemExit(main())
