import pandas as pd
from turtletrader.config import TurtleConfig, SystemConfig, MarketConfig
from turtletrader.strategy import TurtleStrategy, TurtleState

def test_strategy_smoke():
    # 构造最小K线
    d = pd.date_range("2020-01-01", periods=60, freq="D")
    df = pd.DataFrame({
        "date": d, "open": 100, "high": 101, "low": 99, "close": 100
    })
    cfg = TurtleConfig(
        risk_per_unit=0.01, atr_len=20,
        s1=SystemConfig(entry_lookback=20, exit_lookback=10, use_s1_filter=True),
        s2=SystemConfig(entry_lookback=55, exit_lookback=20)
    )
    strat = TurtleStrategy(cfg)
    ind = strat.prepare_indicators(df)
    st = TurtleState()
    # 跑一行看不报错
    row = ind.iloc[-1]
    step = strat.step(row=row, state=st, equity=100000, dollar_per_point=1.0, today=row["date"])
    assert "fills" in step
