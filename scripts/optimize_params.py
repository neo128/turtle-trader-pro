import optuna, yaml, pandas as pd, os
from turtletrader.config import TurtleConfig, SystemConfig, MarketConfig
from turtletrader.strategy import TurtleStrategy, TurtleState
from turtletrader.utils import annual_return

def objective(trial: optuna.Trial):
    s1 = SystemConfig(
        entry_lookback=trial.suggest_int("s1_entry", 15, 30),
        exit_lookback=trial.suggest_int("s1_exit", 7, 15),
        use_s1_filter=True,
    )
    s2 = SystemConfig(
        entry_lookback=trial.suggest_int("s2_entry", 45, 65),
        exit_lookback=trial.suggest_int("s2_exit", 15, 25),
        use_s1_filter=False,
    )
    cfg = TurtleConfig(risk_per_unit=0.01, atr_len=trial.suggest_int("atr_len", 14, 30), s1=s1, s2=s2)
    df = pd.read_csv("aapl.csv")  # 先用单标演示；可扩展到组合
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True).set_index("date")
    strat = TurtleStrategy(cfg)
    ind = strat.prepare_indicators(df)
    st = TurtleState()
    pos = 0; cash = 100_000; eqs=[]
    for dt, row in ind.iterrows():
        step = strat.step(row=row, state=st, equity=cash+pos*row["close"], dollar_per_point=1.0, today=dt)
        for _, size, price in step["fills"]:
            cash -= price*size; pos += size
        eqs.append((dt, cash+pos*row["close"]))
    s = pd.Series({d:v for d,v in eqs})
    return annual_return(s)

if __name__ == "__main__":
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=30)
    print("Best:", study.best_params)
