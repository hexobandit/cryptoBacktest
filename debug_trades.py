"""Debug script to analyze trade exits."""

import json
from pathlib import Path

# Load the results
results_file = Path("backtest_results_ema_4h.json")

if not results_file.exists():
    print("No results file found. Run a backtest first.")
    exit(1)

with open(results_file) as f:
    data = json.load(f)

# Analyze exit reasons
exit_reasons = {}
losing_trades_detail = []

for result in data["results"]:
    symbol = result["symbol"]
    timeframe = result["timeframe"]
    
    for position in result["positions"]:
        exit_reason = position["exit_reason"]
        net_pnl = position["net_pnl"]
        
        if exit_reason not in exit_reasons:
            exit_reasons[exit_reason] = {"count": 0, "total_pnl": 0, "losses": 0}
        
        exit_reasons[exit_reason]["count"] += 1
        exit_reasons[exit_reason]["total_pnl"] += net_pnl
        
        if net_pnl < 0:
            exit_reasons[exit_reason]["losses"] += 1
            
            # Track losing trades
            losing_trades_detail.append({
                "symbol": symbol,
                "timeframe": timeframe,
                "entry_time": position["entry_time"],
                "exit_time": position["exit_time"],
                "exit_reason": exit_reason,
                "pnl_percent": position["pnl_percent"] * 100,
                "net_pnl": net_pnl,
                "pattern": position["pattern"]
            })

# Print summary
print("\n=== EXIT REASON ANALYSIS ===\n")
for reason, stats in exit_reasons.items():
    print(f"{reason}:")
    print(f"  Total trades: {stats['count']}")
    print(f"  Losing trades: {stats['losses']}")
    print(f"  Total P&L: ${stats['total_pnl']:.2f}")
    print()

# Show losing trades
print("\n=== LOSING TRADES DETAILS ===\n")
losing_trades_detail.sort(key=lambda x: x["pnl_percent"])

for i, trade in enumerate(losing_trades_detail[:10], 1):  # Show worst 10
    print(f"{i}. {trade['symbol']}/{trade['timeframe']}")
    print(f"   Pattern: {trade['pattern']}")
    print(f"   Exit: {trade['exit_reason']}")
    print(f"   Loss: {trade['pnl_percent']:.2f}%")
    print(f"   Net P&L: ${trade['net_pnl']:.2f}")
    print(f"   Entry: {trade['entry_time'][:19]}")
    print(f"   Exit: {trade['exit_time'][:19]}")
    print()

# Check for actual stop losses
stop_losses = [t for t in losing_trades_detail if t["exit_reason"] == "Stop Loss"]
if stop_losses:
    print(f"\n!!! WARNING: Found {len(stop_losses)} stop loss exits!")
    print("These should not exist if nothing dropped 50%:")
    for sl in stop_losses:
        print(f"  - {sl['symbol']}: {sl['pnl_percent']:.2f}%")