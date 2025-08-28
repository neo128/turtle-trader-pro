import pandas as pd
try:
    import pandas_market_calendars as mcal
except Exception:
    mcal = None

def is_trading_day(ts: pd.Timestamp, market: str = "NYSE") -> bool:
    if mcal is None:
        return True
    cal = mcal.get_calendar(market)
    schedule = cal.schedule(start_date=ts.normalize(), end_date=ts.normalize())
    return not schedule.empty
