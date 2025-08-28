# Context for AI Code Review/Refactor

- Core:
  - `turtletrader/strategy.py`: Turtle 策略与进出场规则
  - `turtletrader/portfolio.py`: 组合账户、风控与成交逻辑
  - `turtletrader/portfolio_backtest.py`: 组合回测主循环
  - `turtletrader/live_portfolio.py`: 组合纸面实盘轮询
- Non-goals:
  - 暂不接入真实券商下单
- Keep stable:
  - CLI 接口 (`turtletrader/cli.py`) 的参数名与行为
- Improve:
  - 类型注解、边界条件处理
  - 性能（向量化）、日志、错误恢复
  - 单测补齐（特别是 A 股规则：T+1、涨跌停）


在仓库根新建 DOCS_FOR_AI.md，简要说明：
• 项目目的与边界
• 最重要的文件（策略、回测、实盘入口）
• 如何本地跑最小 demo
• 代码风格、类型约束
• 哪些文件不希望被动（例如公共 API）
• 希望 AI 优化的方向（如性能、类型、结构、测试）
目的：把这个文件链接给 AI 助手，它会更“懂你的仓库”。