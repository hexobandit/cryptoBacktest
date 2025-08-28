"""Command-line interface for the backtesting system."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.cache import CacheManager
from app.config import settings
from app.report import generate_report, print_summary, save_json_report
from app.strategy import run_backtest


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Cryptocurrency backtesting tool with candlestick patterns and EMA filtering"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=settings.days_back,
        help=f"Number of days of historical data to fetch (default: {settings.days_back})",
    )
    
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force full re-download of data (ignore cache)",
    )
    
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear all cached data and exit",
    )
    
    parser.add_argument(
        "--symbols",
        nargs="+",
        help="Specific symbols to test (default: all configured symbols)",
    )
    
    parser.add_argument(
        "--timeframes",
        nargs="+",
        help="Specific timeframes to test (default: all configured timeframes)",
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point for CLI."""
    console = Console()
    args = parse_args()
    
    # Handle cache clearing
    if args.clear_cache:
        cache_manager = CacheManager()
        cache_manager.clear_cache()
        console.print("[green]Cache cleared successfully![/green]")
        sys.exit(0)
    
    # Update settings with CLI arguments
    if args.days:
        settings.days_back = args.days
    
    # Determine symbols and timeframes to test
    symbols = args.symbols if args.symbols else settings.symbols
    timeframes = args.timeframes if args.timeframes else settings.timeframes
    
    console.print("\n[bold cyan]═══ CRYPTO BACKTEST ENGINE ═══[/bold cyan]")
    console.print(f"\n[bold]Configuration:[/bold]")
    console.print(f"  Days back: {settings.days_back}")
    console.print(f"  Trade amount: ${settings.trade_amount}")
    console.print(f"  Take profit: {settings.take_profit_percent * 100:.1f}%")
    console.print(f"  Stop loss: {settings.stop_loss_percent * 100:.1f}%")
    console.print(f"  Fee: {settings.trade_fee_percent * 100:.1f}%")
    console.print(f"  EMA periods: {settings.ema_short_period}/{settings.ema_long_period} on {settings.ema_timeframe}")
    console.print(f"  Symbols: {len(symbols)}")
    console.print(f"  Timeframes: {', '.join(timeframes)}")
    
    # Run backtests
    results = []
    total_combinations = len(symbols) * len(timeframes)
    
    console.print(f"\n[bold]Running {total_combinations} backtests...[/bold]\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        for timeframe in timeframes:
            task = progress.add_task(
                f"Testing {timeframe}...",
                total=len(symbols)
            )
            
            for symbol in symbols:
                progress.update(
                    task,
                    description=f"Testing {symbol}/{timeframe}...",
                )
                
                try:
                    result = run_backtest(
                        symbol=symbol,
                        timeframe=timeframe,
                        days_back=settings.days_back,
                        force_refresh=args.refresh,
                    )
                    
                    if result is not None:
                        results.append(result)
                        
                        # Print quick result
                        if result.total_trades > 0:
                            win_rate = result.win_rate * 100
                            pnl = result.net_pnl
                            
                            if pnl >= 0:
                                console.print(
                                    f"  [green]✓[/green] {symbol}/{timeframe}: "
                                    f"{result.total_trades} trades, "
                                    f"{win_rate:.1f}% win rate, "
                                    f"[green]+${pnl:.2f}[/green]"
                                )
                            else:
                                console.print(
                                    f"  [yellow]✓[/yellow] {symbol}/{timeframe}: "
                                    f"{result.total_trades} trades, "
                                    f"{win_rate:.1f}% win rate, "
                                    f"[red]-${abs(pnl):.2f}[/red]"
                                )
                        else:
                            console.print(
                                f"  [dim]○[/dim] {symbol}/{timeframe}: No trades"
                            )
                
                except Exception as e:
                    console.print(
                        f"  [red]✗[/red] {symbol}/{timeframe}: Error - {str(e)}"
                    )
                
                progress.advance(task)
            
            progress.remove_task(task)
    
    # Generate and display report
    if results:
        report = generate_report(results)
        print_summary(report)
        save_json_report(report)
        
        console.print("\n[bold green]Backtest complete![/bold green]")
        console.print(f"Tested {len(results)} symbol/timeframe combinations")
        console.print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        console.print("\n[bold red]No results to report![/bold red]")
        console.print("Please check your API credentials and network connection.")


if __name__ == "__main__":
    main()