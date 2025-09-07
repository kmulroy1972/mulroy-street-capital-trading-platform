import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import pandas as pd
from pathlib import Path

from packages.core.backtesting.engine import BacktestEngine, BacktestConfig, BacktestResults
from packages.core.backtesting.data_fetcher import HistoricalDataFetcher
from packages.strategies.strategy_loader import StrategyLoader

class StrategyBacktester:
    """Run backtests for strategies"""
    
    def __init__(self, api_key: str, secret_key: str):
        self.data_fetcher = HistoricalDataFetcher(api_key, secret_key)
        self.strategy_loader = StrategyLoader()
        self.results_cache: Dict[str, BacktestResults] = {}
        
    def run_backtest(
        self,
        strategy_name: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000,
        timeframe: str = "5Min"
    ) -> BacktestResults:
        """Run backtest for a strategy"""
        
        # Load strategy
        strategy = self.strategy_loader.load_strategy(strategy_name)
        if not strategy:
            raise ValueError(f"Strategy {strategy_name} not found")
        
        # Check for cached data first
        cache_key = f"{'-'.join(symbols)}_{timeframe}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        cached_data = self.data_fetcher.load_from_parquet(symbols, f"data/cache/{cache_key}")
        
        if all(not df.empty for df in cached_data.values()):
            print(f"Using cached data for {symbols}")
            market_data = cached_data
        else:
            # Fetch historical data
            print(f"Fetching historical data for {symbols}...")
            market_data = self.data_fetcher.fetch_bars(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe
            )
            
            # Cache the data
            if market_data:
                self.data_fetcher.save_to_parquet(market_data, f"data/cache/{cache_key}")
        
        # Configure backtest
        config = BacktestConfig(
            initial_capital=initial_capital,
            start_date=start_date,
            end_date=end_date,
            symbols=symbols,
            timeframe=timeframe,
            commission=0.0,  # Alpaca has no commissions
            slippage=0.01,
            allow_shorting=False,
            max_position_size=initial_capital * 0.2  # 20% max per position
        )
        
        # Run backtest
        print(f"Running backtest for {strategy_name}...")
        engine = BacktestEngine(config)
        results = engine.run(strategy, market_data)
        
        # Cache results
        cache_key = f"{strategy_name}_{start_date}_{end_date}"
        self.results_cache[cache_key] = results
        
        return results
    
    def run_optimization(
        self,
        strategy_name: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        parameter_grid: Dict[str, List],
        metric: str = "sharpe_ratio"
    ) -> Dict:
        """Optimize strategy parameters"""
        
        best_result = None
        best_params = None
        best_metric = float('-inf')
        
        # Generate parameter combinations
        import itertools
        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())
        
        total_combinations = len(list(itertools.product(*param_values)))
        print(f"Testing {total_combinations} parameter combinations...")
        
        for i, values in enumerate(itertools.product(*param_values)):
            params = dict(zip(param_names, values))
            
            print(f"[{i+1}/{total_combinations}] Testing parameters: {params}")
            
            # Load strategy with parameters
            strategy = self.strategy_loader.load_strategy(strategy_name)
            
            # Update strategy parameters
            for key, value in params.items():
                if hasattr(strategy, key):
                    setattr(strategy, key, value)
            
            # Run backtest
            try:
                results = self.run_backtest(
                    strategy_name=strategy_name,
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # Check if this is the best result
                current_metric = results.metrics.get(metric, float('-inf'))
                if current_metric > best_metric:
                    best_metric = current_metric
                    best_params = params
                    best_result = results
                    print(f"  ✅ New best {metric}: {best_metric:.4f}")
                else:
                    print(f"  📊 {metric}: {current_metric:.4f}")
                    
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                continue
        
        return {
            "best_params": best_params,
            "best_metric": best_metric,
            "best_result": best_result,
            "total_combinations": total_combinations
        }
    
    def walk_forward_analysis(
        self,
        strategy_name: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        training_period_days: int = 180,
        testing_period_days: int = 30
    ) -> List[BacktestResults]:
        """Perform walk-forward analysis"""
        
        results = []
        current_date = start_date
        period = 1
        
        while current_date + timedelta(days=training_period_days + testing_period_days) <= end_date:
            # Training period
            train_start = current_date
            train_end = current_date + timedelta(days=training_period_days)
            
            # Testing period
            test_start = train_end
            test_end = test_start + timedelta(days=testing_period_days)
            
            print(f"\nPeriod {period}:")
            print(f"  Training: {train_start.strftime('%Y-%m-%d')} to {train_end.strftime('%Y-%m-%d')}")
            print(f"  Testing: {test_start.strftime('%Y-%m-%d')} to {test_end.strftime('%Y-%m-%d')}")
            
            # Optimize on training data
            optimization_result = self.run_optimization(
                strategy_name=strategy_name,
                symbols=symbols,
                start_date=train_start,
                end_date=train_end,
                parameter_grid={
                    "lookback_period": [10, 20, 30],
                    "momentum_threshold": [0.01, 0.02, 0.03] if "momentum" in strategy_name else [0.01, 0.02, 0.03]
                }
            )
            
            # Test on out-of-sample data
            strategy = self.strategy_loader.load_strategy(strategy_name)
            if optimization_result["best_params"]:
                for key, value in optimization_result["best_params"].items():
                    if hasattr(strategy, key):
                        setattr(strategy, key, value)
            
            test_result = self.run_backtest(
                strategy_name=strategy_name,
                symbols=symbols,
                start_date=test_start,
                end_date=test_end
            )
            
            print(f"  Out-of-sample return: {test_result.metrics['return_pct']:.2f}%")
            results.append(test_result)
            
            # Move forward
            current_date += timedelta(days=testing_period_days)
            period += 1
        
        return results
    
    def generate_report(self, results: BacktestResults, output_path: str = "reports/backtest.html"):
        """Generate HTML report with charts"""
        try:
            from jinja2 import Template
            import plotly.graph_objects as go
            import plotly.offline as pyo
        except ImportError:
            print("Missing dependencies for report generation. Install: pip install jinja2 plotly")
            return
        
        # Create equity curve chart
        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(
            x=results.equity_curve.index,
            y=results.equity_curve['total_equity'],
            mode='lines',
            name='Equity',
            line=dict(color='#00ff88', width=2)
        ))
        fig_equity.update_layout(
            title='Equity Curve',
            xaxis_title='Date',
            yaxis_title='Equity ($)',
            template='plotly_dark'
        )
        equity_html = pyo.plot(fig_equity, output_type='div', include_plotlyjs=False)
        
        # Create drawdown chart
        equity = results.equity_curve['total_equity']
        running_max = equity.cummax()
        drawdown = (equity - running_max) / running_max * 100
        
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=drawdown.index,
            y=drawdown,
            mode='lines',
            fill='tozeroy',
            name='Drawdown',
            line=dict(color='#ff3b3b', width=1)
        ))
        fig_dd.update_layout(
            title='Drawdown',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            template='plotly_dark'
        )
        dd_html = pyo.plot(fig_dd, output_type='div', include_plotlyjs=False)
        
        # Create returns distribution
        fig_returns = go.Figure()
        fig_returns.add_trace(go.Histogram(
            x=results.daily_returns * 100,
            nbinsx=50,
            name='Daily Returns',
            marker_color='#00d4ff'
        ))
        fig_returns.update_layout(
            title='Returns Distribution',
            xaxis_title='Daily Return (%)',
            yaxis_title='Frequency',
            template='plotly_dark'
        )
        returns_html = pyo.plot(fig_returns, output_type='div', include_plotlyjs=False)
        
        # Generate HTML report
        template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Backtest Report</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
                h1 { color: #00ff88; }
                h2 { color: #00d4ff; margin-top: 30px; }
                .metrics { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
                .metric { background: #2a2a2a; padding: 15px; border-radius: 8px; }
                .metric-label { color: #888; font-size: 12px; }
                .metric-value { font-size: 24px; font-weight: bold; margin-top: 5px; }
                .positive { color: #00ff88; }
                .negative { color: #ff3b3b; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th { background: #2a2a2a; padding: 10px; text-align: left; }
                td { padding: 10px; border-bottom: 1px solid #333; }
            </style>
        </head>
        <body>
            <h1>Backtest Report</h1>
            
            <h2>Performance Metrics</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Total Return</div>
                    <div class="metric-value {{ 'positive' if metrics.return_pct > 0 else 'negative' }}">
                        {{ "%.2f"|format(metrics.return_pct) }}%
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Sharpe Ratio</div>
                    <div class="metric-value">{{ "%.2f"|format(metrics.sharpe_ratio) }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Max Drawdown</div>
                    <div class="metric-value negative">{{ "%.2f"|format(metrics.max_drawdown * 100) }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{{ "%.1f"|format(metrics.win_rate * 100) }}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value">{{ "%.2f"|format(metrics.profit_factor) }}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Trades</div>
                    <div class="metric-value">{{ metrics.total_trades }}</div>
                </div>
            </div>
            
            <h2>Equity Curve</h2>
            {{ equity_chart|safe }}
            
            <h2>Drawdown</h2>
            {{ drawdown_chart|safe }}
            
            <h2>Returns Distribution</h2>
            {{ returns_chart|safe }}
            
            <h2>Trade Log (Last 20)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>P&L</th>
                    </tr>
                </thead>
                <tbody>
                    {% for trade in trades[-20:] %}
                    <tr>
                        <td>{{ trade.timestamp.strftime('%Y-%m-%d %H:%M') }}</td>
                        <td>{{ trade.symbol }}</td>
                        <td>{{ trade.side.upper() }}</td>
                        <td>{{ trade.quantity }}</td>
                        <td>${{ "%.2f"|format(trade.price) }}</td>
                        <td class="{{ 'positive' if trade.pnl > 0 else 'negative' }}">
                            ${{ "%.2f"|format(trade.pnl) }}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </body>
        </html>
        """)
        
        html = template.render(
            metrics=results.metrics,
            equity_chart=equity_html,
            drawdown_chart=dd_html,
            returns_chart=returns_html,
            trades=results.trades
        )
        
        # Save report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"Report saved to {output_path}")