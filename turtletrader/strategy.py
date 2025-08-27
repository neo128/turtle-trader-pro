from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
from .config import TurtleConfig
from .utils import donchian_high, donchian_low, atr_ema

@dataclass
class Unit:
    entry_price: float
    direction: int  # +1 long, -1 short
    size: int
    stop: float
    entry_date: pd.Timestamp

class TurtleState:
    def __init__(self):
        self.units: List[Unit] = []
        self.last_s1_win: bool = False
        self.last_breakout_price: Optional[float] = None

class TurtleStrategy:
    def __init__(self, cfg: TurtleConfig):
        self.cfg = cfg

    def prepare_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["N"] = atr_ema(df["high"], df["low"], df["close"], self.cfg.atr_len)
        if self.cfg.s1:
            df["s1_high"] = donchian_high(df["high"].shift(1), self.cfg.s1.entry_lookback)
            df["s1_low"]  = donchian_low(df["low"].shift(1),  self.cfg.s1.entry_lookback)
            df["s1_exit_high"] = donchian_high(df["high"].shift(1), self.cfg.s1.exit_lookback)
            df["s1_exit_low"]  = donchian_low(df["low"].shift(1),  self.cfg.s1.exit_lookback)
        if self.cfg.s2:
            df["s2_high"] = donchian_high(df["high"].shift(1), self.cfg.s2.entry_lookback)
            df["s2_low"]  = donchian_low(df["low"].shift(1),  self.cfg.s2.entry_lookback)
            df["s2_exit_high"] = donchian_high(df["high"].shift(1), self.cfg.s2.exit_lookback)
            df["s2_exit_low"]  = donchian_low(df["low"].shift(1), self.cfg.s2.exit_lookback)
        return df

    def _unit_size(self, equity: float, N: float, dollar_per_point: float) -> int:
        unit_risk = equity * self.cfg.risk_per_unit
        per_contract_risk = max(N * dollar_per_point, 1e-12)
        return max(int(unit_risk // per_contract_risk), 0)

    def _new_stop(self, entry: float, direction: int, N: float) -> float:
        return entry - direction * self.cfg.pyramiding.stop_N * N

    def step(self, row: pd.Series, state: TurtleState, equity: float, dollar_per_point: float, today: pd.Timestamp) -> dict:
        """给定一根K线（建议已收盘），返回当根要执行的成交（entry/add/exit/stop）"""
        last_price = row["open"]  # 执行价使用开盘较稳健
        N = row["N"]
        fills = []

        # 1) 止损
        still = []
        for u in state.units:
            stop_hit = (u.direction == 1 and row["low"] <= u.stop) or (u.direction == -1 and row["high"] >= u.stop)
            if stop_hit:
                fills.append(("stop", -u.direction * u.size, u.stop))
            else:
                still.append(u)
        state.units = still

        # 2) 系统退出（通道退出信号 -> 平仓）
        if state.units:
            direction = state.units[0].direction
            exit_hit = False
            if "s1_exit_low" in row and "s1_exit_high" in row:
                if direction == 1 and row["close"] < row["s1_exit_low"]: exit_hit = True
                if direction == -1 and row["close"] > row["s1_exit_high"]: exit_hit = True
            if "s2_exit_low" in row and "s2_exit_high" in row:
                if direction == 1 and row["close"] < row["s2_exit_low"]: exit_hit = True
                if direction == -1 and row["close"] > row["s2_exit_high"]: exit_hit = True
            if exit_hit:
                total = sum(u.size for u in state.units) * direction
                if total != 0:
                    fills.append(("exit", -direction * total, last_price))
                if state.last_breakout_price is not None and "s1_high" in row:
                    pnl = (last_price - state.last_breakout_price) * direction
                    state.last_s1_win = pnl > 0
                state.units = []

        # 3) 进场（若空仓）
        if not state.units and N > 0:
            choose_dir = 0
            # S1：仅当上次S1非盈利时才进场
            if "s1_high" in row and "s1_low" in row:
                if not state.last_s1_win:
                    if row["close"] > row["s1_high"]:
                        choose_dir = 1
                    elif row["close"] < row["s1_low"]:
                        choose_dir = -1
            # S2：若S1未触发
            if choose_dir == 0 and "s2_high" in row and "s2_low" in row:
                if row["close"] > row["s2_high"]:
                    choose_dir = 1
                elif row["close"] < row["s2_low"]:
                    choose_dir = -1

            if choose_dir != 0:
                size = self._unit_size(equity, N, dollar_per_point=dollar_per_point)
                if size > 0:
                    entry_price = last_price
                    stop = self._new_stop(entry_price, choose_dir, N)
                    state.units.append(Unit(entry_price, choose_dir, size, stop, today))
                    state.last_breakout_price = entry_price
                    state.last_s1_win = False
                    fills.append(("entry", choose_dir * size, entry_price))

        # 4) 金字塔加仓
        if state.units and len(state.units) < self.cfg.pyramiding.max_units:
            first = state.units[0]
            k = len(state.units)  # 下一单位的索引
            trigger = first.entry_price + first.direction * k * self.cfg.pyramiding.step_N * N
            hit = (first.direction == 1 and row["high"] >= trigger) or (first.direction == -1 and row["low"] <= trigger)
            if hit:
                size = self._unit_size(equity, N, dollar_per_point=dollar_per_point)
                if size > 0:
                    stop = self._new_stop(trigger, first.direction, N)
                    state.units.append(Unit(trigger, first.direction, size, stop, today))
                    fills.append(("add", first.direction * size, trigger))

        return {"fills": fills, "units": state.units}
