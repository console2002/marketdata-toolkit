from watchlist.update_watchlist import update_watchlist

def test_update_watchlist_smoke(tmp_path):
    out_json = tmp_path / "tickers.json"
    payload = update_watchlist(
        portfolio_csv=str(tmp_path / "portfolio.csv"),
        trade_log_csv=str(tmp_path / "trades.csv"),
        static_extras_json=str(tmp_path / "extras.json"),
        out_json=str(out_json),
    )
    assert "tickers" in payload
