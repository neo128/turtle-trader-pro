from __future__ import annotations
import pandas as pd
from typing import Optional

class DataSource:
    def get_history(self, symbol: str, start: Optional[str], end: Optional[str], interval: str) -> pd.DataFrame:
        raise NotImplementedError
    def recent_bars(self, symbol: str, n: int, interval: str) -> pd.DataFrame:
        raise NotImplementedError

class YFinanceSource(DataSource):
    def __init__(self):
        try:
            import yfinance as yf  # type: ignore
        except Exception as e:
            raise RuntimeError("需要安装 yfinance，请执行：pip install yfinance") from e
        self.yf = yf

    def get_history(self, symbol: str, start: Optional[str], end: Optional[str], interval: str) -> pd.DataFrame:
        ticker = self.yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval=interval, auto_adjust=False)
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        df = df.reset_index().rename(columns={"Date":"date"})
        return df[["date","open","high","low","close","volume"]]

    def recent_bars(self, symbol: str, n: int, interval: str) -> pd.DataFrame:
        # yfinance用period+interval拉最近数据
        period_map = {"1m":"2d","2m":"5d","5m":"30d","15m":"60d","30m":"60d","60m":"730d","1h":"730d","1d":"max","1wk":"max","1mo":"max"}
        period = period_map.get(interval, "max")
        df = self.yf.download(symbol, period=period, interval=interval, auto_adjust=False, progress=False)
        df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
        df = df.reset_index().rename(columns={df.columns[0]:"date"})
        return df.tail(n)

class EFinanceSource(DataSource):
    def __init__(self):
        try:
            import efinance as ef  # type: ignore
        except Exception as e:
            raise RuntimeError("需要安装 efinance，请执行：pip install efinance") from e
        self.ef = ef

    def get_history(self, symbol: str, start: Optional[str], end: Optional[str], interval: str) -> pd.DataFrame:
        df = self.ef.stock.get_quote_history(symbol)
        rename_map = {"日期":"date","开盘":"open","最高":"high","最低":"low","收盘":"close","成交量":"volume"}
        df = df.rename(columns=rename_map)
        df["date"] = pd.to_datetime(df["date"])
        cols = ["date","open","high","low","close"] + (["volume"] if "volume" in df.columns else [])
        return df[cols]

    def recent_bars(self, symbol: str, n: int, interval: str) -> pd.DataFrame:
        # efinance 统一返回日线，若用更细粒度需改造
        df = self.get_history(symbol, start=None, end=None, interval=interval)
        return df.tail(n)
