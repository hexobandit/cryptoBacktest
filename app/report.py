"""Report generation and output formatting."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from app.config import settings
from app.types import (
    BacktestReport,
    BacktestResult,
    PositionReport,
    SymbolTimeframeResult,
    TimeframeSummary,
)


def format_percentage(value: float) -> str:
    """Format percentage value for display."""
    return f"{value * 100:.2f}%"


def format_currency(value: float) -> str:
    """Format currency value for display."""
    return f"${value:.2f}"


def create_position_report(position: Any) -> PositionReport:
    """
    Convert Position to PositionReport for JSON serialization.
    
    Args:
        position: Position object
    
    Returns:
        PositionReport object
    """
    return PositionReport(
        entry_time=position.entry_time.isoformat(),
        entry_price=round(position.entry_price, 8),
        exit_time=position.exit_time.isoformat() if position.exit_time else "",
        exit_price=round(position.exit_price, 8) if position.exit_price else 0,
        quantity=round(position.quantity, 8),
        pattern=position.pattern.value,
        exit_reason=position.exit_reason.value if position.exit_reason else "",
        entry_ema_short=round(position.entry_ema_short, 8),
        entry_ema_long=round(position.entry_ema_long, 8),
        exit_ema_short=round(position.exit_ema_short, 8) if position.exit_ema_short else 0,
        exit_ema_long=round(position.exit_ema_long, 8) if position.exit_ema_long else 0,
        pnl=round(position.pnl, 2),
        pnl_percent=round(position.pnl_percent, 4),
        fees=round(position.fees, 2),
        net_pnl=round(position.net_pnl, 2),
    )


def create_symbol_timeframe_result(result: BacktestResult) -> SymbolTimeframeResult:
    """
    Convert BacktestResult to SymbolTimeframeResult for JSON.
    
    Args:
        result: BacktestResult object
    
    Returns:
        SymbolTimeframeResult object
    """
    return SymbolTimeframeResult(
        symbol=result.symbol,
        timeframe=result.timeframe,
        total_trades=result.total_trades,
        winning_trades=result.winning_trades,
        losing_trades=result.losing_trades,
        win_rate=round(result.win_rate, 4),
        total_pnl=round(result.total_pnl, 2),
        total_fees=round(result.total_fees, 2),
        net_pnl=round(result.net_pnl, 2),
        avg_win=round(result.avg_win, 2),
        avg_loss=round(result.avg_loss, 2),
        hodl_return=round(result.hodl_return, 4),
        hodl_pnl=round(result.hodl_pnl, 2),
        first_price=round(result.first_price, 8) if result.first_price else 0,
        last_price=round(result.last_price, 8) if result.last_price else 0,
        start_date=result.start_date.isoformat() if result.start_date else "",
        end_date=result.end_date.isoformat() if result.end_date else "",
        ema_filter_blocked=result.ema_filter_blocked,
        patterns_detected=result.patterns_detected,
        positions=[create_position_report(p) for p in result.positions],
    )


def generate_report(results: list[BacktestResult]) -> BacktestReport:
    """
    Generate complete backtest report.
    
    Args:
        results: List of backtest results
    
    Returns:
        BacktestReport object
    """
    # Filter out empty results
    valid_results = [r for r in results if r is not None]
    
    # Calculate timeframe summaries
    timeframe_stats: dict[str, dict[str, Any]] = {}
    
    for result in valid_results:
        tf = result.timeframe
        if tf not in timeframe_stats:
            timeframe_stats[tf] = {
                "total_trades": 0,
                "total_pnl": 0,
                "net_pnl": 0,
                "win_rates": [],
                "symbols_traded": set(),
            }
        
        timeframe_stats[tf]["total_trades"] += result.total_trades
        timeframe_stats[tf]["total_pnl"] += result.total_pnl
        timeframe_stats[tf]["net_pnl"] += result.net_pnl
        
        if result.total_trades > 0:
            timeframe_stats[tf]["win_rates"].append(result.win_rate)
            timeframe_stats[tf]["symbols_traded"].add(result.symbol)
    
    # Create timeframe summaries
    timeframe_summaries = []
    for tf, stats in timeframe_stats.items():
        avg_win_rate = (
            sum(stats["win_rates"]) / len(stats["win_rates"])
            if stats["win_rates"]
            else 0
        )
        
        timeframe_summaries.append(
            TimeframeSummary(
                timeframe=tf,
                total_trades=stats["total_trades"],
                total_pnl=round(stats["total_pnl"], 2),
                net_pnl=round(stats["net_pnl"], 2),
                avg_win_rate=round(avg_win_rate, 4),
                symbols_traded=len(stats["symbols_traded"]),
            )
        )
    
    # Sort summaries by net P&L
    timeframe_summaries.sort(key=lambda x: x.net_pnl, reverse=True)
    
    # Determine best timeframe
    best_timeframe = timeframe_summaries[0].timeframe if timeframe_summaries else ""
    
    # Calculate overall statistics
    total_trades = sum(r.total_trades for r in valid_results)
    total_winning = sum(r.winning_trades for r in valid_results)
    total_losing = sum(r.losing_trades for r in valid_results)
    total_pnl = sum(r.total_pnl for r in valid_results)
    total_fees = sum(r.total_fees for r in valid_results)
    net_pnl = sum(r.net_pnl for r in valid_results)
    
    overall_win_rate = total_winning / total_trades if total_trades > 0 else 0
    
    ema_filter_blocked = sum(r.ema_filter_blocked for r in valid_results)
    patterns_detected = sum(r.patterns_detected for r in valid_results)
    
    overall_stats = {
        "total_trades": total_trades,
        "winning_trades": total_winning,
        "losing_trades": total_losing,
        "win_rate": round(overall_win_rate, 4),
        "total_pnl": round(total_pnl, 2),
        "total_fees": round(total_fees, 2),
        "net_pnl": round(net_pnl, 2),
        "ema_filter_blocked": ema_filter_blocked,
        "patterns_detected": patterns_detected,
    }
    
    # Create configuration summary
    configuration = {
        "trade_amount": settings.trade_amount,
        "fee_percent": settings.trade_fee_percent,
        "take_profit_percent": settings.take_profit_percent,
        "stop_loss_percent": settings.stop_loss_percent,
        "ema_short_period": settings.ema_short_period,
        "ema_long_period": settings.ema_long_period,
        "ema_timeframe": settings.ema_timeframe,
        "days_back": settings.days_back,
        "symbols": settings.symbols,
        "timeframes": settings.timeframes,
    }
    
    # Create full report
    report = BacktestReport(
        generated_at=datetime.now().isoformat(),
        configuration=configuration,
        overall_stats=overall_stats,
        best_timeframe=best_timeframe,
        timeframe_summaries=timeframe_summaries,
        results=[create_symbol_timeframe_result(r) for r in valid_results],
    )
    
    return report


def save_json_report(report: BacktestReport, filename: str = "backtest_results_ema_4h.json") -> None:
    """
    Save report to JSON file.
    
    Args:
        report: BacktestReport object
        filename: Output filename
    """
    output_path = Path(filename)
    
    with open(output_path, "w") as f:
        json.dump(report.model_dump(), f, indent=2)
    
    print(f"\nReport saved to {output_path}")


def print_summary(report: BacktestReport) -> None:
    """
    Print formatted summary to console.
    
    Args:
        report: BacktestReport object
    """
    console = Console()
    
    # Overall summary
    console.print("\n[bold cyan]═══ BACKTEST SUMMARY ═══[/bold cyan]\n")
    
    stats = report.overall_stats
    console.print(f"[bold]Total Trades:[/bold] {stats['total_trades']}")
    console.print(f"[bold]Winning Trades:[/bold] {stats['winning_trades']}")
    console.print(f"[bold]Losing Trades:[/bold] {stats['losing_trades']}")
    console.print(f"[bold]Win Rate:[/bold] {format_percentage(stats['win_rate'])}")
    console.print(f"[bold]Net P&L:[/bold] {format_currency(stats['net_pnl'])}")
    console.print(f"[bold]Total Fees:[/bold] {format_currency(stats['total_fees'])}")
    console.print(f"[bold]Patterns Detected:[/bold] {stats['patterns_detected']}")
    console.print(f"[bold]EMA Filter Blocked:[/bold] {stats['ema_filter_blocked']}")
    
    # Best timeframe
    console.print(f"\n[bold green]Best Timeframe:[/bold green] {report.best_timeframe}")
    
    # Timeframe summary table
    if report.timeframe_summaries:
        console.print("\n[bold cyan]═══ TIMEFRAME PERFORMANCE ═══[/bold cyan]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Timeframe", style="cyan")
        table.add_column("Trades", justify="right")
        table.add_column("Win Rate", justify="right")
        table.add_column("Net P&L", justify="right")
        table.add_column("Symbols", justify="right")
        
        for summary in report.timeframe_summaries:
            win_rate_str = format_percentage(summary.avg_win_rate)
            pnl_str = format_currency(summary.net_pnl)
            
            # Color code P&L
            if summary.net_pnl > 0:
                pnl_str = f"[green]{pnl_str}[/green]"
            elif summary.net_pnl < 0:
                pnl_str = f"[red]{pnl_str}[/red]"
            
            table.add_row(
                summary.timeframe,
                str(summary.total_trades),
                win_rate_str,
                pnl_str,
                str(summary.symbols_traded),
            )
        
        console.print(table)
    
    # Per-symbol results
    console.print("\n[bold cyan]═══ TOP PERFORMERS ═══[/bold cyan]\n")
    
    # Sort results by net P&L
    sorted_results = sorted(report.results, key=lambda x: x.net_pnl, reverse=True)
    
    # Show top 5 performers
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Symbol", style="cyan")
    table.add_column("Timeframe", style="yellow")
    table.add_column("Trades", justify="right")
    table.add_column("Win Rate", justify="right")
    table.add_column("Net P&L", justify="right")
    table.add_column("HODL P&L", justify="right")
    
    for i, result in enumerate(sorted_results[:5]):
        win_rate_str = format_percentage(result.win_rate)
        pnl_str = format_currency(result.net_pnl)
        hodl_str = format_currency(result.hodl_pnl)
        
        # Color code P&L
        if result.net_pnl > 0:
            pnl_str = f"[green]{pnl_str}[/green]"
        elif result.net_pnl < 0:
            pnl_str = f"[red]{pnl_str}[/red]"
        
        if result.hodl_pnl > 0:
            hodl_str = f"[green]{hodl_str}[/green]"
        elif result.hodl_pnl < 0:
            hodl_str = f"[red]{hodl_str}[/red]"
        
        table.add_row(
            result.symbol,
            result.timeframe,
            str(result.total_trades),
            win_rate_str,
            pnl_str,
            hodl_str,
        )
    
    console.print(table)