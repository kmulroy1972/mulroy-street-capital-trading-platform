.PHONY: fmt lint test run-api run-engine build-docker dev-up install docker-build-engine help test-connection test-live test-all strategy-create strategy-test strategy-backtest strategy-watch strategy-list monitor-setup monitor-health monitor-metrics monitor-alerts monitor-prometheus monitor-logs deploy-setup deploy-azure deploy-rollback deploy-monitor dev-azure dev-local dev-monitoring

help:
	@echo "Available targets:"
	@echo "  install      - Install Python dependencies"
	@echo "  fmt          - Format code in all packages"
	@echo "  lint         - Run linting checks"
	@echo "  test         - Run test suites"
	@echo "  run-api      - Start the API server"
	@echo "  run-engine   - Start the trading engine"
	@echo "  build-docker - Build Docker images"
	@echo "  docker-build-engine - Build engine Docker image"
	@echo "  dev-up       - Start development environment"
	@echo "  test-connection - Test Alpaca live connection"
	@echo "  test-live    - Run live trading tests"
	@echo "  test-all     - Run all tests including live"
	@echo "  strategy-create - Create new strategy from template"
	@echo "  strategy-test   - Test strategy with live data"
	@echo "  strategy-backtest - Run strategy backtest"
	@echo "  backtest         - Run interactive backtest with CLI"
	@echo "  backtest-optimize - Run parameter optimization"
	@echo "  backtest-walkforward - Run walk-forward analysis"
	@echo "  strategy-watch  - Watch strategies for hot-reload"
	@echo "  strategy-list   - List all available strategies"
	@echo "  monitor-setup   - Setup monitoring system"
	@echo "  monitor-health  - Check system health"
	@echo "  monitor-metrics - Get system metrics"
	@echo "  monitor-alerts  - Get active alerts"
	@echo "  monitor-logs    - Tail structured logs"
	@echo "  deploy-setup    - Setup GitHub secrets for deployment"
	@echo "  deploy-azure    - Deploy to Azure Container Apps"
	@echo "  deploy-rollback - Rollback Azure deployment"
	@echo "  deploy-monitor  - Setup Azure monitoring"
	@echo "  dev-azure       - Start development with Azure services"
	@echo "  dev-local       - Start local development environment"
	@echo "  dev-monitoring  - Start with full monitoring stack"

install:
	pip install -r requirements-dev.txt

fmt:
	ruff format .

lint:
	ruff check .
	mypy --strict apps/ packages/

test:
	pytest tests/ -v --cov=apps --cov=packages

docker-build-engine:
	docker build -f apps/engine/Dockerfile -t alpaca-engine .

run-api:
	@echo "Starting API server..."
	@cd apps/api && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-engine:
	@echo "Starting trading engine..."
	@cd apps/engine && python main.py

build-docker:
	@echo "Building Docker images..."
	@docker-compose build

dev-up:
	@echo "Starting development environment..."
	@docker-compose up -d

test-connection:
	@echo "Testing Alpaca Live Connection..."
	python3.11 test_alpaca_connection.py

test-live: test-connection
	@echo "Running live trading tests..."
	python3.11 -m pytest tests/test_live_alpaca.py -v -s

test-all: test test-live
	@echo "All tests complete"

# Strategy Development Commands
strategy-create:
	@echo "Creating new strategy..."
	@read -p "Strategy name: " name; \
	python scripts/dev_strategy.py create $$name

strategy-test:
	@echo "Testing strategy with live data..."
	@read -p "Strategy name: " name; \
	read -p "Symbols (space-separated, default SPY): " symbols; \
	read -p "Duration in minutes (default 30): " duration; \
	symbols=$${symbols:-SPY}; \
	duration=$${duration:-30}; \
	python scripts/dev_strategy.py test $$name --symbols $$symbols --duration $$duration

strategy-backtest:
	@echo "Running strategy backtest..."
	@read -p "Strategy name: " name; \
	read -p "Start date (YYYY-MM-DD): " start; \
	read -p "End date (YYYY-MM-DD): " end; \
	read -p "Symbols (space-separated, default SPY): " symbols; \
	symbols=$${symbols:-SPY}; \
	python scripts/dev_strategy.py backtest $$name --start $$start --end $$end --symbols $$symbols

strategy-watch:
	@echo "Starting strategy file watcher..."
	python scripts/dev_strategy.py watch

strategy-list:
	@echo "Listing available strategies..."
	python scripts/dev_strategy.py list

# Backtesting Commands
backtest:
	@echo "Running interactive backtest..."
	@read -p "Strategy name: " name; \
	read -p "Symbols (space-separated, default SPY): " symbols; \
	read -p "Start date (YYYY-MM-DD, default 1 year ago): " start; \
	read -p "End date (YYYY-MM-DD, default today): " end; \
	read -p "Initial capital (default 100000): " capital; \
	read -p "Timeframe (1Min/5Min/15Min/30Min/1Hour/1Day, default 5Min): " timeframe; \
	read -p "Generate HTML report? (y/N): " report; \
	symbols=$${symbols:-SPY}; \
	capital=$${capital:-100000}; \
	timeframe=$${timeframe:-5Min}; \
	cmd="python scripts/backtest.py $$name --symbols $$symbols --capital $$capital --timeframe $$timeframe"; \
	if [ "$$start" ]; then cmd="$$cmd --start $$start"; fi; \
	if [ "$$end" ]; then cmd="$$cmd --end $$end"; fi; \
	if [ "$$report" = "y" ] || [ "$$report" = "Y" ]; then \
		report_file="reports/backtest_$$name_$(shell date +%Y%m%d_%H%M%S).html"; \
		cmd="$$cmd --report $$report_file"; \
	fi; \
	$$cmd

backtest-optimize:
	@echo "Running parameter optimization..."
	@read -p "Strategy name: " name; \
	read -p "Symbols (space-separated, default SPY): " symbols; \
	read -p "Start date (YYYY-MM-DD, default 1 year ago): " start; \
	read -p "End date (YYYY-MM-DD, default today): " end; \
	symbols=$${symbols:-SPY}; \
	cmd="python scripts/backtest.py $$name --symbols $$symbols --optimize"; \
	if [ "$$start" ]; then cmd="$$cmd --start $$start"; fi; \
	if [ "$$end" ]; then cmd="$$cmd --end $$end"; fi; \
	$$cmd

backtest-walkforward:
	@echo "Running walk-forward analysis..."
	@read -p "Strategy name: " name; \
	read -p "Symbols (space-separated, default SPY): " symbols; \
	read -p "Start date (YYYY-MM-DD, default 2 years ago): " start; \
	read -p "End date (YYYY-MM-DD, default today): " end; \
	symbols=$${symbols:-SPY}; \
	cmd="python scripts/backtest.py $$name --symbols $$symbols --walk-forward"; \
	if [ "$$start" ]; then cmd="$$cmd --start $$start"; fi; \
	if [ "$$end" ]; then cmd="$$cmd --end $$end"; fi; \
	$$cmd

# Monitoring Commands
monitor-setup:
	@echo "Setting up monitoring system..."
	python scripts/setup_alerts.py

monitor-health:
	@echo "Checking system health..."
	curl -s http://localhost:8000/api/monitoring/health/detailed | jq .

monitor-metrics:
	@echo "Getting system metrics..."
	curl -s http://localhost:8000/api/monitoring/metrics | jq .

monitor-alerts:
	@echo "Getting active alerts..."
	curl -s http://localhost:8000/api/monitoring/alerts | jq .

monitor-prometheus:
	@echo "Getting Prometheus metrics..."
	curl -s http://localhost:8000/api/monitoring/prometheus

monitor-logs:
	@echo "Tailing structured logs..."
	tail -f logs/trading_$(shell date +%Y%m%d).jsonl | jq .

# Deployment Commands
deploy-setup:
	@echo "Setting up deployment environment..."
	./scripts/setup_github_secrets.sh

deploy-azure:
	@echo "Deploying to Azure..."
	./scripts/deploy.sh

deploy-rollback:
	@echo "Rolling back deployment..."
	@read -p "Component to rollback (api/engine/web): " component; \
	./scripts/rollback.sh $$component

deploy-monitor:
	@echo "Setting up Azure monitoring..."
	./scripts/setup_azure_monitoring.sh

# Local development with Azure services
dev-azure:
	@echo "Starting development with Azure services..."
	docker-compose -f docker-compose.azure.yml up -d

dev-local:
	@echo "Starting local development environment..."
	docker-compose -f docker-compose.azure.yml --profile local up -d

dev-monitoring:
	@echo "Starting with monitoring stack..."
	docker-compose -f docker-compose.azure.yml --profile monitoring --profile local up -d