#!/usr/bin/env python3
"""
Backtest CLI Tool
Run backtests for strategies from command line
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime, timedelta
import json
import asyncio

def main():
    parser = argparse.ArgumentParser(description="Backtest Trading Strategies")
    parser.add_argument("strategy", help="Strategy name to backtest")
    parser.add_argument("--symbols", nargs="+", default=["SPY"], help="Symbols to trade")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)", 
                       default=(datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"))
    parser.add_argument("--end", help="End date (YYYY-MM-DD)", 
                       default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--capital", type=float, default=100000, help="Initial capital")
    parser.add_argument("--timeframe", default="5Min", 
                       choices=["1Min", "5Min", "15Min", "30Min", "1Hour", "1Day"])
    parser.add_argument("--optimize", action="store_true", help="Run parameter optimization")
    parser.add_argument("--walk-forward", action="store_true", help="Run walk-forward analysis")
    parser.add_argument("--report", help="Generate HTML report at path")
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")
    
    # Initialize backtester
    api_key = os.getenv("APCA_API_KEY_ID", "AKHT4KA9CHH6IPIF24TF")
    secret_key = os.getenv("APCA_API_SECRET_KEY", "jEXQa4rgIma8p9umGVSfYb0se7EzRUKKjnUwIzIV")
    
    try:
        from packages.strategies.backtest_runner import StrategyBacktester
        from tabulate import tabulate
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Install with: pip install pandas numpy tabulate")
        sys.exit(1)
    
    backtester = StrategyBacktester(api_key, secret_key)
    
    print(f"\n{'='*60}")
    print(f"Backtesting {args.strategy}")
    print(f"{'='*60}")
    print(f"Symbols: {', '.join(args.symbols)}")
    print(f"Period: {args.start} to {args.end}")
    print(f"Capital: ${args.capital:,.0f}")
    print(f"Timeframe: {args.timeframe}")
    print(f"{'='*60}\n")
    
    if args.optimize:
        # Run optimization
        print("Running parameter optimization...")
        result = backtester.run_optimization(
            strategy_name=args.strategy,
            symbols=args.symbols,
            start_date=start_date,
            end_date=end_date,
            parameter_grid={
                "lookback_period": [10, 20, 30, 40],
                "entry_threshold": [0.01, 0.02, 0.03],
                "stop_loss": [0.02, 0.03, 0.05]
            }
        )
        
        print(f"\nBest Parameters: {result['best_params']}")
        print(f"Best Sharpe Ratio: {result['best_metric']:.2f}")
        
        results = result['best_result']
        
    elif args.walk_forward:
        # Run walk-forward analysis
        print("Running walk-forward analysis...")
        results_list = backtester.walk_forward_analysis(
            strategy_name=args.strategy,
            symbols=args.symbols,
            start_date=start_date,
            end_date=end_date,
            training_period_days=180,
            testing_period_days=30
        )
        
        # Aggregate results
        total_return = sum(r.metrics['return_pct'] for r in results_list)
        avg_sharpe = sum(r.metrics['sharpe_ratio'] for r in results_list) / len(results_list)
        
        print(f"\nWalk-Forward Results:")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Average Sharpe: {avg_sharpe:.2f}")
        
        results = results_list[-1]  # Use last period for report
        
    else:
        # Standard backtest
        results = backtester.run_backtest(
            strategy_name=args.strategy,
            symbols=args.symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=args.capital,
            timeframe=args.timeframe
        )
    
    # Display results
    metrics_table = [
        ["Total Return", f"{results.metrics['return_pct']:.2f}%"],
        ["Total P&L", f"${results.metrics['total_pnl']:,.2f}"],
        ["Sharpe Ratio", f"{results.metrics['sharpe_ratio']:.2f}"],
        ["Sortino Ratio", f"{results.metrics['sortino_ratio']:.2f}"],
        ["Max Drawdown", f"{results.metrics['max_drawdown']*100:.2f}%"],
        ["Win Rate", f"{results.metrics['win_rate']*100:.1f}%"],
        ["Total Trades", results.metrics['total_trades']],
        ["Winning Trades", results.metrics['winning_trades']],
        ["Losing Trades", results.metrics['losing_trades']],
        ["Avg Win", f"${results.metrics['avg_win']:.2f}"],
        ["Avg Loss", f"${results.metrics['avg_loss']:.2f}"],
        ["Profit Factor", f"{results.metrics['profit_factor']:.2f}"],
        ["Calmar Ratio", f"{results.metrics['calmar_ratio']:.2f}"],
    ]
    
    print("\n" + tabulate(metrics_table, headers=["Metric", "Value"], tablefmt="grid"))
    
    # Show last trades
    if results.trades:
        print(f"\nLast 10 Trades:")
        trade_table = []
        for trade in results.trades[-10:]:
            trade_table.append([
                trade.timestamp.strftime("%Y-%m-%d %H:%M"),
                trade.symbol,
                trade.side.upper(),
                trade.quantity,
                f"${trade.price:.2f}",
                f"${trade.pnl:.2f}"
            ])
        
        print(tabulate(trade_table, 
                      headers=["Date", "Symbol", "Side", "Qty", "Price", "P&L"],
                      tablefmt="grid"))
    
    # Generate report if requested
    if args.report:
        print(f"\nGenerating report: {args.report}")
        backtester.generate_report(results, args.report)
        print(f"Report saved to {args.report}")
    
    # Save results to JSON
    results_dict = results.to_dict()
    results_file = f"results_{args.strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results_dict, f, indent=2)
    print(f"\nResults saved to {results_file}")

if __name__ == "__main__":
    main()