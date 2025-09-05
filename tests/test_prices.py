import pandas as pd
from marketdata.prices import _stooq_symbol, _weekend_safe_end

def test_symbol_map():
    assert _stooq_symbol("BP.L") == "bp.uk"
    assert _stooq_symbol("OR.PA") == "or.fr"
    assert _stooq_symbol("ENEL.MI") == "enel.it"
    assert _stooq_symbol("AAPL") == "aapl.us"

def test_weekend_safe_end():
    assert _weekend_safe_end(pd.Timestamp("2025-09-06")).weekday() == 4
    assert _weekend_safe_end(pd.Timestamp("2025-09-07")).weekday() == 4
