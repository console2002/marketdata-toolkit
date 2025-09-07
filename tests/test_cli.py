import pandas as pd
from marketdata import prices


def test_cli_saves_csv(tmp_path, monkeypatch, capsys):
    df = pd.DataFrame({
        "Date": [pd.Timestamp("2024-01-05")],
        "Open": [1.0],
        "High": [1.0],
        "Low": [1.0],
        "Close": [1.0],
        "Adj Close": [1.0],
        "Volume": [0],
        "Ticker": ["AAPL"],
        "Source": ["yahoo"],
    })

    def fake_get_prices(tickers, start, end, on_error="warn"):
        return {tickers[0]: df.assign(Ticker=tickers[0])}

    monkeypatch.setattr(prices, "get_prices", fake_get_prices)
    out_dir = tmp_path / "out"
    rc = prices.main([
        "--tickers",
        "AAPL",
        "--start",
        "2024-01-02",
        "--end",
        "2024-01-05",
        "--out-dir",
        str(out_dir),
    ])
    assert rc == 0
    csv_path = out_dir / "AAPL_D.csv"
    assert csv_path.exists()
    saved = pd.read_csv(csv_path)
    assert not saved.empty


def test_cli_watchlist(tmp_path, monkeypatch, capsys):
    df = pd.DataFrame(
        {
            "Date": [pd.Timestamp("2024-01-05")],
            "Open": [1.0],
            "High": [1.0],
            "Low": [1.0],
            "Close": [1.0],
            "Adj Close": [1.0],
            "Volume": [0],
            "Ticker": ["AAPL"],
            "Source": ["yahoo"],
        }
    )

    def fake_get_prices(tickers, start, end, on_error="warn"):
        return {t: df.assign(Ticker=t) for t in tickers}

    monkeypatch.setattr(prices, "get_prices", fake_get_prices)
    cfg = tmp_path / "watch.json"
    cfg.write_text(
        '{"tickers": ["AAPL"], "groups": {"watchlist": ["AAPL"]}}', encoding="utf-8"
    )
    rc = prices.main([
        "--config",
        str(cfg),
        "--start",
        "2024-01-02",
        "--end",
        "2024-01-05",
    ])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "AAPL" in captured
