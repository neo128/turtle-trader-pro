# Turtle Trader Pro (组合 + 实盘纸面)

- 组合回测：多标的共享账户与风险配额  
- A股规则（可配）：T+1、涨跌停、可卖空开关  
- API 数据：yfinance（全球）、efinance（A股）  
- 组合纸面实盘：`portfolio-live` 轮询多标的、执行到本地 Paper 账户（可持久化）  
- `--use_closed`：只用已收盘的倒数第二根K线生成信号，避免半截K线造成的“假突破”

## 安装
```bash
pip install -e .[yahoo,china]
# 可选：交易日历（上交所/深交所/NYSE）
pip install -e .[cal]

## 用 conda 安装（推荐）

```bash
# 在仓库根目录
conda env create -f environment.yml
conda activate turtle-pro
# 首次建议安装 pre-commit
pre-commit install

### macOS 图形后端
如遇到 `matplotlib` 后端报错，可在运行脚本前设置：
```bash
export MPLBACKEND=Agg


# 单元测试
pytest -q

# 组合回测 + HTML 报告（带自动下载）
turtle-backtest portfolio-backtest \
  --config examples/portfolio_sample.yaml \
  --out report_port \
  --auto_download \
  --html_report

# 组合 live（可控循环3次）
TURTLE_LOG_LEVEL=INFO \
turtle-backtest portfolio-live \
  --config examples/portfolio_sample.yaml \
  --paper_store ./paper_port_state \
  --poll 10 \
  --nbars 300 \
  --use_closed \
  --max_loops 3


## Roadmap
- [ ] 数据源抽象：支持 ccxt（加密）与更多股票数据适配器
- [ ] 交易日历：引入 pandas_market_calendars，过滤非交易时段
- [ ] 组合回测加权：多货币/点值支持（dollar_per_point 更细化）
- [ ] 绩效模块：新增 Calmar、Sortino、胜率、期望收益等指标
- [ ] 策略参数搜索：网格 + 贝叶斯优化（optuna）
- [ ] 可视化：Plotly 交互式图表 + html 报告导出
- [ ] CLI UX：支持 JSON/YAML 输出规范化以及丰富的日志等级
- [ ] 单测覆盖率提升至 85%+





