import pandas as pd
from marketdata.prices import _stooq_symbol, _weekend_safe_end, get_latest_close

def test_symbol_map():
    assert _stooq_symbol("BP.L") == "bp.uk"
    assert _stooq_symbol("OR.PA") == "or.fr"
    assert _stooq_symbol("ENEL.MI") == "enel.it"
    assert _stooq_symbol("AAPL") == "aapl.us"

def test_weekend_safe_end():
    assert _weekend_safe_end(pd.Timestamp("2025-09-06")).weekday() == 4
    assert _weekend_safe_end(pd.Timestamp("2025-09-07")).weekday() == 4


def test_get_latest_close(monkeypatch):
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
        return {tickers[0]: df}

    monkeypatch.setattr("marketdata.prices.get_prices", fake_get_prices)
    asof, px = get_latest_close("AAPL")
    assert asof == pd.Timestamp("2024-01-05")
    assert px == 1.0


def test_get_prices_schema(monkeypatch):
    def fake_yf_download(*args, **kwargs):
        df = pd.DataFrame(
            {
                "Open": [1.0],
                "High": [1.0],
                "Low": [1.0],
                "Close": [1.0],
                "Adj Close": [1.0],
                "Volume": [0],
            },
            index=[pd.Timestamp("2024-01-05")],
        )
        df.index.name = "Date"
        return df

    monkeypatch.setattr("yfinance.download", fake_yf_download)
    from marketdata import prices as mp

    bars = mp.get_prices(["AAPL"], start="2024-01-01", end="2024-01-06")
    df = bars["AAPL"]
    assert list(df.columns) == [
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
    assert df["Ticker"].iloc[0] == "AAPL"
    assert df["Source"].iloc[0] == "yahoo"
