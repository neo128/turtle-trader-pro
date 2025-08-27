from typing import Dict, Any
import pandas as pd
from .config import TurtleConfig
from .strategy import TurtleStrategy, TurtleState
from .utils import max_drawdown, sharpe, annual_return

def run_backtest(df: pd.DataFrame, cfg: TurtleConfig, out_dir: str=None) -> Dict[str, Any]:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df.set_index("date", inplace=True)

    strat = TurtleStrategy(cfg)
    df = strat.prepare_indicators(df)

    state = TurtleState()
    equity = 100_000.0
    pos = 0
    cash = equity
    trades = []
    eq = []

    for dt, row in df.iterrows():
        equity = cash + pos * row["close"]
        step = strat.step(row=row, state=state, equity=equity, dollar_per_point=cfg.market.dollar_per_point, today=dt)
        for reason, size, price in step["fills"]:
            cash -= price * size
            pos += size
            trades.append((dt, reason, size, price))
        equity = cash + pos * row["close"]
        eq.append((dt, equity))

    equity_series = pd.Series({dt: e for dt, e in eq}).sort_index()
    rets = equity_series.pct_change().dropna()
    metrics = {
        "start": str(equity_series.index[0].date()) if not equity_series.empty else None,
        "end": str(equity_series.index[-1].date()) if not equity_series.empty else None,
        "start_equity": float(equity_series.iloc[0]) if not equity_series.empty else 0.0,
        "end_equity": float(equity_series.iloc[-1]) if not equity_series.empty else 0.0,
        "cagr": float(annual_return(equity_series)),
        "sharpe": float(sharpe(rets)),
        "max_drawdown": float(max_drawdown(equity_series)),
        "total_trades": len(trades),
        "final_position": int(pos),
    }

    if out_dir:
        import os, json, matplotlib.pyplot as plt
        os.makedirs(out_dir, exist_ok=True)
        pd.DataFrame({"equity": equity_series}).to_csv(os.path.join(out_dir, "equity_curve.csv"))
        with open(os.path.join(out_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        plt.figure()
        equity_series.plot(title="Equity Curve")
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "equity_curve.png"), dpi=144)
        plt.close()

    return {"metrics": metrics, "equity": equity_series, "trades": trades}
