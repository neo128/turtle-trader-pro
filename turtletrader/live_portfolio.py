import os, json, time
import pandas as pd
from typing import Dict, Any
from .config import PortfolioConfig, InstrumentConfig
from .portfolio import Portfolio, Position
from .strategy import TurtleStrategy, TurtleState, Unit
from .data_sources import YFinanceSource, EFinanceSource
from .utils import unify_ohlcv

def _pick_source(name: str):
    name = (name or "").lower()
    if name in ["yf","yahoo","yfinance"]:
        return YFinanceSource()
    if name in ["ef","efinance","china","cn"]:
        return EFinanceSource()
    raise ValueError(f"unknown source {name}")

def _store_paths(store_dir: str):
    os.makedirs(store_dir, exist_ok=True)
    return (os.path.join(store_dir, "state.json"),
            os.path.join(store_dir, "trades.csv"))

def _serialize_state(port: Portfolio) -> dict:
    def ser_state(ts: TurtleState):
        return {
            "last_s1_win": ts.last_s1_win,
            "last_breakout_price": ts.last_breakout_price,
            "units": [
                {
                    "entry_price": u.entry_price,
                    "direction": u.direction,
                    "size": u.size,
                    "stop": u.stop,
                    "entry_date": str(u.entry_date)
                } for u in ts.units
            ]
        }
    return {
        "cash": port.cash,
        "positions": {k: {"size": v.size, "avg_price": v.avg_price} for k, v in port.positions.items()},
        "group_units": port.group_units,
        "total_units": port.total_units,
        "states": {k: ser_state(v) for k, v in port.states.items()},
        "trades": port.trades,
    }

def _deserialize_state(port: Portfolio, data: dict):
    port.cash = float(data.get("cash", port.cash))
    port.positions = {k: Position(size=int(v.get("size",0)), avg_price=float(v.get("avg_price",0))) for k,v in data.get("positions",{}).items()}
    port.group_units = {k:int(v) for k,v in data.get("group_units",{}).items()}
    port.total_units = int(data.get("total_units", 0))
    new_states = {}
    for sym, sd in data.get("states", {}).items():
        ts = TurtleState()
        ts.last_s1_win = bool(sd.get("last_s1_win", False))
        ts.last_breakout_price = sd.get("last_breakout_price", None)
        units = []
        for u in sd.get("units", []):
            units.append(Unit(
                entry_price=float(u["entry_price"]),
                direction=int(u["direction"]),
                size=int(u["size"]),
                stop=float(u["stop"]),
                entry_date=pd.to_datetime(u["entry_date"])
            ))
        ts.units = units
        new_states[sym] = ts
    if new_states:
        port.states = new_states
    port.trades = data.get("trades", [])

def run_portfolio_live(pcfg: PortfolioConfig, store_dir: str, poll: int=60, nbars: int=300, use_closed: bool=False):
    instruments = {ins.symbol: ins for ins in pcfg.instruments}
    strategys = {sym: TurtleStrategy(pcfg.turtle) for sym in instruments}
    sources = {sym: _pick_source(ins.source) for sym, ins in instruments.items()}

    port = Portfolio(pcfg)
    state_path, trades_path = _store_paths(store_dir)
    if os.path.exists(state_path):
        try:
            _deserialize_state(port, json.load(open(state_path,"r")))
            print(f"[restore] loaded state from {state_path}")
        except Exception as e:
            print("restore error:", e)

    print(f"[LIVE] portfolio {len(instruments)} symbols, poll={poll}s, nbars={nbars}, use_closed={use_closed}")
    while True:
        try:
            rows = {}
            last_prices = {}
            for sym, ins in instruments.items():
                if ins.source is None:
                    continue
                src = sources[sym]
                bars = src.recent_bars(ins.symbol, n=nbars, interval=ins.interval)
                df = strategys[sym].prepare_indicators(unify_ohlcv(bars))
                if len(df) < 2:
                    continue
                df["prev_close"] = df["close"].shift(1)
                # 关键：仅用已收盘K线时取倒数第二根
                row = df.iloc[-2] if (use_closed and len(df) >= 2) else df.iloc[-1]
                rows[sym] = row
                last_prices[sym] = row["close"]

            equity = port.equity(last_prices)

            for sym, row in rows.items():
                strat = strategys[sym]
                state = port.states.get(sym) or TurtleState()
                port.states[sym] = state
                ins = instruments[sym]
                step = strat.step(row=row, state=state, equity=equity,
                                  dollar_per_point=ins.dollar_per_point,
                                  today=row["date"] if "date" in row else pd.Timestamp.utcnow())
                for reason, size, price in step["fills"]:
                    allow = True
                    if reason in ("entry","add"):
                        if not port.can_open_new_unit(instruments, sym):
                            allow = False
                        else:
                            port._bump_units(instruments, sym, +1)
                    if allow:
                        port.execute(pd.to_datetime(row["date"]), sym, reason, size, price, row, ins)
                        print(f"FILLED {sym}: {reason} {size} @ {price}")

            with open(state_path, "w") as f:
                json.dump(_serialize_state(port), f, indent=2)

            time.sleep(poll)
        except KeyboardInterrupt:
            print("Stopped by user.")
            break
        except Exception as e:
            print("Error:", e)
            time.sleep(poll)
