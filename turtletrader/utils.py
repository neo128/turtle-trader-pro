from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import numpy as np
import pandas as pd

@dataclass
class Fill:
    date: pd.Timestamp
    price: float
    size: int
    reason: str
    symbol: str = ""

def ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()

def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr

def atr_ema(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    tr = true_range(high, low, close)
    return ema(tr, length)

def donchian_high(series: pd.Series, lookback: int) -> pd.Series:
    return series.rolling(lookback).max()

def donchian_low(series: pd.Series, lookback: int) -> pd.Series:
    return series.rolling(lookback).min()

def max_drawdown(equity: pd.Series) -> float:
    cummax = equity.cummax()
    dd = (equity / cummax) - 1.0
    return dd.min()

def sharpe(returns: pd.Series, risk_free=0.0) -> float:
    if returns.std() == 0:
        return 0.0
    return (returns.mean() - risk_free/252) / (returns.std() + 1e-12) * (252 ** 0.5)

def annual_return(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    start = equity.iloc[0]
    end = equity.iloc[-1]
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-6)
    return (end / start) ** (1/years) - 1.0

def unify_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names: date/open/high/low/close[/volume]."""
    cols = {c.lower(): c for c in df.columns}
    out = df.rename(columns={
        cols.get("date","date"): "date",
        cols.get("open","open"): "open",
        cols.get("high","high"): "high",
        cols.get("low","low"): "low",
        cols.get("close","close"): "close",
        cols.get("volume","volume"): "volume",
    })
    sel = ["date","open","high","low","close"]
    if "volume" in out.columns: sel.append("volume")
    return out[sel]
