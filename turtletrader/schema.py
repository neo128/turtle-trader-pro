from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List

class RuleSchema(BaseModel):
    allow_short: bool = True
    t_plus_one: bool = False
    limit_rate: float = 0.0
    @field_validator("limit_rate")
    @classmethod
    def _check_limit(cls, v): 
        if v < 0 or v > 0.3: 
            raise ValueError("limit_rate must be between 0 and 0.3")
        return v

class InstrumentSchema(BaseModel):
    symbol: str
    group: str = "default"
    csv: Optional[str] = None
    source: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    interval: str = "1d"
    dollar_per_point: float = 1.0
    rules: RuleSchema = RuleSchema()

class SystemSchema(BaseModel):
    entry_lookback: int
    exit_lookback: int
    use_s1_filter: bool = False

class PyramidingSchema(BaseModel):
    step_N: float = 0.5
    max_units: int = 4
    stop_N: float = 2.0

class MarketSchema(BaseModel):
    dollar_per_point: float = 1.0
    slippage_per_contract: float = 0.0
    commission_per_contract: float = 0.0

class TurtleSchema(BaseModel):
    risk_per_unit: float = 0.01
    atr_len: int = 20
    s1: Optional[SystemSchema] = None
    s2: Optional[SystemSchema] = None
    pyramiding: PyramidingSchema = PyramidingSchema()
    market: MarketSchema = MarketSchema()

class RiskCapsSchema(BaseModel):
    max_units_total: int = 10
    max_units_per_group: Dict[str,int] = {}

class PortfolioSchema(BaseModel):
    account: Dict[str, float] = {"init_equity": 100000.0}
    turtle: TurtleSchema = TurtleSchema()
    instruments: List[InstrumentSchema]
    risk_caps: RiskCapsSchema = RiskCapsSchema()
