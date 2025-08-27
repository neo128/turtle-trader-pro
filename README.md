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







