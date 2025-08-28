.PHONY: env dev fmt lint type test backtest live

env:
	conda env create -f environment.yml || true
	conda activate turtle-pro && pre-commit install

dev:
	conda env create -f environment-dev.yml || true
	conda activate turtle-pro-dev && pre-commit install

fmt:
	black .

lint:
	flake8 .

type:
	mypy turtletrader

test:
	pytest -q

backtest:
	turtle-backtest portfolio-backtest \
	  --config examples/portfolio_sample.yaml \
	  --out report_port \
	  --auto_download

live:
	turtle-backtest portfolio-live \
	  --config examples/portfolio_sample.yaml \
	  --paper_store ./paper_port_state \
	  --poll 60 \
	  --nbars 300 \
	  --use_closed
