# Contributing

感谢贡献！请遵循以下流程：
1. Fork 本仓库并创建分支：`git checkout -b feat/your-feature`
2. 在本地安装：
   ```bash
   pip install -e '.[yahoo,china]'
   pre-commit install
3. 运行快速校验（单测/格式检查）：
    pytest -q
    pre-commit run --all-files
4. 提交 PR 并阐述变更、动机与影响面。

### 代码规范:
Python 3.9+
类型注解（mypy 友好）
模块/函数必须加 docstring
变更逻辑配套最小单测

### 提交信息
使用约定式提交（conventional commits）
feat, fix, refactor, docs, test, chore, ci

