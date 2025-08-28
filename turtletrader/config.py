from dataclasses import dataclass, field
from typing import Optional, Dict, List

@dataclass
class SystemConfig:
    entry_lookback: int
    exit_lookback: int
    use_s1_filter: bool = False  # 是否启用“若上次S1盈利则跳过本次S1”的过滤

@dataclass
class PyramidingConfig:
    step_N: float = 0.5       # 加仓触发步长（N的倍数）
    max_units: int = 4        # 最多单位数
    stop_N: float = 2.0       # 2N止损

@dataclass
class MarketConfig:
    dollar_per_point: float = 1.0
    slippage_per_contract: float = 0.0
    commission_per_contract: float = 0.0

@dataclass
class RuleConfig:
    allow_short: bool = True
    t_plus_one: bool = False
    limit_rate: float = 0.0   # A股涨跌停（如10%则0.10）

@dataclass
class TurtleConfig:
    risk_per_unit: float = 0.01
    atr_len: int = 20
    s1: Optional[SystemConfig] = None
    s2: Optional[SystemConfig] = None
    pyramiding: PyramidingConfig = field(default_factory=PyramidingConfig)
    market: MarketConfig = field(default_factory=MarketConfig)

@dataclass
class InstrumentConfig:
    symbol: str
    group: str = "default"
    csv: Optional[str] = None
    source: Optional[str] = None    # yfinance / efinance
    start: Optional[str] = None
    end: Optional[str] = None
    interval: str = "1d"
    dollar_per_point: float = 1.0
    rules: RuleConfig = field(default_factory=RuleConfig)

@dataclass
class PortfolioRiskCaps:
    max_units_total: int = 10
    max_units_per_group: Optional[Dict[str, int]] = None  # 例如 {"equities": 6, "a_shares": 6}

@dataclass
class PortfolioConfig:
    account_init_equity: float = 100000.0
    turtle: TurtleConfig = field(default_factory=TurtleConfig)
    instruments: Optional[List[InstrumentConfig]] = None
    risk_caps: PortfolioRiskCaps = field(default_factory=PortfolioRiskCaps)
