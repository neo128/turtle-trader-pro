from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from .config import PortfolioConfig, InstrumentConfig
from .strategy import TurtleStrategy, TurtleState
from .utils import max_drawdown, sharpe, annual_return

@dataclass
class Position:
    size: int = 0
    avg_price: float = 0.0

class Portfolio:
    def __init__(self, cfg: PortfolioConfig):
        self.cfg = cfg
        self.cash = cfg.account_init_equity
        self.positions: Dict[str, Position] = {}
        self.states: Dict[str, TurtleState] = {}
        self.group_units: Dict[str, int] = {}
        self.total_units: int = 0
        self.trades: List[Dict[str, Any]] = []

    def _group_of_symbol(self, instruments: Dict[str, InstrumentConfig], symbol: str) -> str:
        return instruments[symbol].group

    def can_open_new_unit(self, instruments: Dict[str, InstrumentConfig], symbol: str) -> bool:
        if self.total_units >= self.cfg.risk_caps.max_units_total:
            return False
        caps = self.cfg.risk_caps.max_units_per_group or {}
        grp = self._group_of_symbol(instruments, symbol)
        if grp in caps and self.group_units.get(grp, 0) >= caps[grp]:
            return False
        return True

    def _bump_units(self, instruments: Dict[str, InstrumentConfig], symbol: str, delta: int):
        self.total_units += delta
        grp = self._group_of_symbol(instruments, symbol)
        self.group_units[grp] = self.group_units.get(grp, 0) + delta

    # A股涨跌停“封板”简化判断：若高=低=收=涨停或跌停价，则对应方向无法成交
    def _cn_limit_block(self, prev_close: float, row: pd.Series, side: str, limit_rate: float) -> bool:
        if limit_rate <= 0 or np.isnan(prev_close): return False
        up = prev_close * (1 + limit_rate)
        dn = prev_close * (1 - limit_rate)
        locked_up = (abs(row["high"]-up)<1e-8) and (abs(row["low"]-up)<1e-8) and (abs(row["close"]-up)<1e-8)
        locked_dn = (abs(row["high"]-dn)<1e-8) and (abs(row["low"]-dn)<1e-8) and (abs(row["close"]-dn)<1e-8)
        if side == "buy" and locked_up: return True
        if side == "sell" and locked_dn: return True
        return False

    # T+1：若今天买入，则当天不许卖出
    def _t_plus_one_block(self, today: pd.Timestamp, symbol: str) -> bool:
        for t in reversed(self.trades):
            if t["symbol"] == symbol and t["size"] > 0:
                if pd.to_datetime(t["date"]).date() == today.date():
                    return True
                break
        return False

    def execute(self, dt: pd.Timestamp, symbol: str, reason: str, size: int, price: float,
                row: pd.Series, instr: InstrumentConfig):
        side = "buy" if size>0 else "sell"
        # 禁做空
        if size < 0 and not instr.rules.allow_short:
            if self.positions.get(symbol, Position()).size <= 0:
                return
        # T+1
        if instr.rules.t_plus_one and side == "sell":
            if self._t_plus_one_block(dt, symbol):
                return
        # 涨跌停封单
        if instr.rules.limit_rate > 0.0:
            prev_close = row.get("prev_close", np.nan)
            if self._cn_limit_block(prev_close, row, side, instr.rules.limit_rate):
                return

        # 执行成交（Paper模式：现金简单扣减，不计滑点与手续费）
        pos = self.positions.setdefault(symbol, Position())
        self.cash -= price * size
        new_size = pos.size + size
        if pos.size == 0 or (pos.size>0) == (size>0):
            total_cost = pos.avg_price * abs(pos.size) + price * abs(size)
            total_size = abs(pos.size) + abs(size)
            pos.avg_price = total_cost / max(total_size,1)
            pos.size = new_size
        else:
            # 反向减仓/平仓
            pos.size = new_size
            if pos.size == 0: pos.avg_price = 0.0
            else: pos.avg_price = price

        self.trades.append({"date": str(dt), "symbol": symbol, "reason": reason, "size": size, "price": price})

    def equity(self, last_prices: Dict[str, float]) -> float:
        eq = self.cash
        for sym, pos in self.positions.items():
            eq += pos.size * last_prices.get(sym, 0.0)
        return eq
