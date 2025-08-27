from typing import Dict, Any
import pandas as pd
import os, json
from .config import PortfolioConfig, InstrumentConfig
from .strategy import TurtleStrategy, TurtleState
from .portfolio import Portfolio
from .utils import max_drawdown, sharpe, annual_return

def run_portfolio_backtest(data_map: Dict[str, pd.DataFrame], cfg: PortfolioConfig, out_dir: str=None) -> Dict[str, Any]:
    instruments: Dict[str, InstrumentConfig] = {ins.symbol: ins for ins in cfg.instruments}
    strategys = {sym: TurtleStrategy(cfg.turtle) for sym in data_map}
    dfs = {}
    states = {}

    for sym, df in data_map.items():
        df = strategys[sym].prepare_indicators(df.copy())
        df["prev_close"] = df["close"].shift(1)
        dfs[sym] = df
        states[sym] = TurtleState()

    port = Portfolio(cfg)
    port.states = states

    # 联合时间轴（按date对齐）
    all_dates = sorted(set().union(*[set(df["date"]) for df in dfs.values()]))
    last_prices = {sym: dfs[sym].iloc[0]["close"] for sym in dfs}
    equity_series = []

    for dt in all_dates:
        rows = {sym: df[df["date"]==dt].iloc[0] for sym, df in dfs.items() if not df[df["date"]==dt].empty}
        for sym, row in rows.items():
            last_prices[sym] = row["close"]
        equity = port.equity(last_prices)

        for sym, row in rows.items():
            strat = strategys[sym]
            state = port.states[sym]
            ins = instruments[sym]
            step = strat.step(row=row, state=state, equity=equity, dollar_per_point=ins.dollar_per_point, today=dt)
            for reason, size, price in step["fills"]:
                allow = True
                if reason in ("entry","add"):
                    if not port.can_open_new_unit(instruments, sym):
                        allow = False
                    else:
                        port._bump_units(instruments, sym, +1)
                if allow:
                    port.execute(dt, sym, reason, size, price, row, ins)

        equity_series.append((dt, port.equity(last_prices)))

    eq = pd.Series({pd.to_datetime(d): v for d, v in equity_series}).sort_index()
    rets = eq.pct_change().dropna()
    metrics = {
        "start": str(eq.index[0].date()) if not eq.empty else None,
        "end": str(eq.index[-1].date()) if not eq.empty else None,
        "start_equity": float(eq.iloc[0]) if not eq.empty else 0.0,
        "end_equity": float(eq.iloc[-1]) if not eq.empty else 0.0,
        "cagr": float(annual_return(eq)),
        "sharpe": float(sharpe(rets)),
        "max_drawdown": float(max_drawdown(eq)),
        "total_trades": len(port.trades),
        "final_positions": {k:int(v.size) for k,v in port.positions.items()}
    }

    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        pd.DataFrame({"equity": eq}).to_csv(os.path.join(out_dir, "equity_curve.csv"))
        with open(os.path.join(out_dir, "metrics.json"), "w") as f:
            json.dump(metrics, f, indent=2)
        import matplotlib.pyplot as plt
        plt.figure()
        eq.plot(title="Portfolio Equity Curve")
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "equity_curve.png"), dpi=144)
        plt.close()
        pd.DataFrame(port.trades).to_csv(os.path.join(out_dir, "trades.csv"), index=False)

    return {"metrics": metrics, "equity": eq, "trades": port.trades, "positions": port.positions}
