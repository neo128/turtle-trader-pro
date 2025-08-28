import click, os, sys, json
import pandas as pd
import yaml
from .config import (TurtleConfig, SystemConfig, PyramidingConfig, MarketConfig,
                     RuleConfig, InstrumentConfig, PortfolioConfig, PortfolioRiskCaps)
from .backtest import run_backtest
from .data_sources import YFinanceSource, EFinanceSource
from .portfolio_backtest import run_portfolio_backtest
from .schema import PortfolioSchema

def load_turtle_config(y: dict) -> TurtleConfig:
    s1 = y.get("systems", {}).get("s1")
    s2 = y.get("systems", {}).get("s2")
    return TurtleConfig(
        risk_per_unit = y.get("risk_per_unit", 0.01),
        atr_len = y.get("atr_len", 20),
        s1 = SystemConfig(**s1) if s1 else None,
        s2 = SystemConfig(**s2) if s2 else None,
        pyramiding = PyramidingConfig(**y.get("pyramiding", {})),
        market = MarketConfig(**y.get("market", {})),
    )

def load_portfolio_config(path: str) -> PortfolioConfig:
    with open(path, "r") as f:
        y = yaml.safe_load(f)
        validated = PortfolioSchema(**y)   # 若不合法会抛错
        y = validated.model_dump()         # 之后按原逻辑转成 dataclass
        
    turtle = load_turtle_config(y.get("turtle", y))
    risk_caps = y.get("risk_caps", {}) or {}
    prc = PortfolioRiskCaps(
        max_units_total = risk_caps.get("max_units_total", 10),
        max_units_per_group = risk_caps.get("max_units_per_group", {})
    )
    instruments = []
    for item in y["instruments"]:
        rules = RuleConfig(**item.get("rules", {})) if item.get("rules") else RuleConfig()
        instruments.append(InstrumentConfig(
            symbol=item["symbol"],
            group=item.get("group","default"),
            csv=item.get("csv"),
            source=item.get("source"),
            start=item.get("start"),
            end=item.get("end"),
            interval=item.get("interval","1d"),
            dollar_per_point=item.get("dollar_per_point", 1.0),
            rules=rules
        ))
    return PortfolioConfig(
        account_init_equity = y.get("account",{}).get("init_equity", 100000.0),
        turtle = turtle,
        instruments = instruments,
        risk_caps = prc
    )

@click.group()
def main():
    """Turtle Trading CLI (single + portfolio)"""

@main.command()
@click.option("--csv", "csv_path", required=True)
@click.option("--config", "config_path", required=True)
@click.option("--out", "out_dir", default="./report")
def backtest(csv_path, config_path, out_dir):
    df = pd.read_csv(csv_path)
    cfg = load_turtle_config(yaml.safe_load(open(config_path)))
    res = run_backtest(df, cfg, out_dir=out_dir)
    click.echo(json.dumps(res["metrics"], indent=2))

@main.command()
@click.option("--source", type=click.Choice(["yfinance","efinance"]), required=True)
@click.option("--symbol", required=True)
@click.option("--interval", default="1d")
@click.option("--start", default=None)
@click.option("--end", default=None)
@click.option("--out", "out_csv", required=True)
def download(source, symbol, interval, start, end, out_csv):
    src = YFinanceSource() if source=="yfinance" else EFinanceSource()
    df = src.get_history(symbol, start, end, interval)
    df.to_csv(out_csv, index=False)
    click.echo(f"Wrote {out_csv} ({len(df)} rows)")

@main.command("portfolio-backtest")
@click.option("--config", "config_path", required=True)
@click.option("--out", "out_dir", default="./report_port")
@click.option("--auto_download", is_flag=True)
@click.option("--html_report", is_flag=True)
def portfolio_backtest_cmd(config_path, out_dir, auto_download,html_report):
    pcfg = load_portfolio_config(config_path)
    data_map = {}
    for ins in pcfg.instruments:
        if ins.csv and os.path.exists(ins.csv):
            df = pd.read_csv(ins.csv)
        elif auto_download and ins.source:
            src = YFinanceSource() if ins.source=="yfinance" else EFinanceSource()
            df = src.get_history(ins.symbol, ins.start, ins.end, ins.interval)
        else:
            raise click.ClickException(f"No data for {ins.symbol}. Provide csv or enable --auto_download with source.")
        data_map[ins.symbol] = df
    from .utils import unify_ohlcv
    for k in list(data_map.keys()):
        data_map[k] = unify_ohlcv(data_map[k])
    res = run_portfolio_backtest(data_map, pcfg, out_dir=out_dir)
    if html_report:
        from .report import save_html_report
        save_html_report(res, out_dir)
    click.echo(json.dumps(res["metrics"], indent=2))

@main.command("portfolio-live")
@click.option("--config", "config_path", required=True, help="YAML portfolio config")
@click.option("--paper_store", required=True, help="状态与成交的存储目录")
@click.option("--poll", default=60, help="轮询秒数")
@click.option("--nbars", default=300, help="每次拉取的历史K线数量（>= ATR窗口×4）")
@click.option("--use_closed", is_flag=True, help="只使用已收盘K线（倒数第二根）")
@click.option("--max_loops", default=0, help="最大迭代次数，0为无限循环")
# @click.option("--html_report", is_flag=True)
def portfolio_live_cmd(config_path, paper_store, poll, nbars, use_closed,max_loops):
    pcfg = load_portfolio_config(config_path)
    from .live_portfolio import run_portfolio_live
    run_portfolio_live(pcfg, paper_store, poll=poll, nbars=nbars, use_closed=use_closed, max_loops=max_loops)

if __name__ == "__main__":
    main()
