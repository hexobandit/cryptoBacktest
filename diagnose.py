"""Diagnostic script to understand low trade count."""

import json
from pathlib import Path
from datetime import datetime

# Load the results
results_file = Path("backtest_results_ema_4h.json")

if not results_file.exists():
    print("No results file found. Run a backtest first.")
    exit(1)

with open(results_file) as f:
    data = json.load(f)

print("\n=== BACKTEST DIAGNOSTIC ===\n")

# Get overall stats
overall = data["overall_stats"]
print(f"Total Trades: {overall['total_trades']}")
print(f"Patterns Detected: {overall['patterns_detected']}")
print(f"EMA Filter Blocked: {overall['ema_filter_blocked']}")
print(f"Block Rate: {overall['ema_filter_blocked'] / max(overall['patterns_detected'], 1) * 100:.1f}%\n")

# Configuration check
config = data["configuration"]
print("=== CONFIGURATION ===")
print(f"Days Back: {config['days_back']}")
print(f"Take Profit: {config['take_profit_percent']*100:.1f}%")
print(f"Stop Loss: {config['stop_loss_percent']*100:.1f}%")
print(f"EMA Periods: {config['ema_short_period']}/{config['ema_long_period']}")
print()

# Per-timeframe analysis
print("=== TIMEFRAME BREAKDOWN ===")
timeframe_data = {}

for result in data["results"]:
    tf = result["timeframe"]
    if tf not in timeframe_data:
        timeframe_data[tf] = {
            "trades": 0,
            "patterns": 0,
            "blocked": 0,
            "symbols": 0
        }
    
    timeframe_data[tf]["trades"] += result["total_trades"]
    timeframe_data[tf]["patterns"] += result["patterns_detected"]
    timeframe_data[tf]["blocked"] += result["ema_filter_blocked"]
    if result["total_trades"] > 0 or result["patterns_detected"] > 0:
        timeframe_data[tf]["symbols"] += 1

for tf, stats in sorted(timeframe_data.items()):
    print(f"\n{tf}:")
    print(f"  Trades: {stats['trades']}")
    print(f"  Patterns: {stats['patterns']}")
    print(f"  Blocked by EMA: {stats['blocked']}")
    if stats['patterns'] > 0:
        print(f"  Block rate: {stats['blocked']/stats['patterns']*100:.1f}%")
    print(f"  Active symbols: {stats['symbols']}")

# Sample some individual results
print("\n=== SAMPLE SYMBOL ANALYSIS (first 3) ===")
for i, result in enumerate(data["results"][:3]):
    print(f"\n{result['symbol']}/{result['timeframe']}:")
    print(f"  Date range: {result['start_date'][:10]} to {result['end_date'][:10]}")
    
    # Calculate days
    start = datetime.fromisoformat(result['start_date'])
    end = datetime.fromisoformat(result['end_date'])
    days = (end - start).days
    print(f"  Days of data: {days}")
    
    print(f"  Trades: {result['total_trades']}")
    print(f"  Patterns detected: {result['patterns_detected']}")
    print(f"  EMA blocked: {result['ema_filter_blocked']}")
    
    # Check for specific issues
    if result['patterns_detected'] == 0:
        print("  ⚠️ NO PATTERNS DETECTED!")
    elif result['ema_filter_blocked'] == result['patterns_detected']:
        print("  ⚠️ ALL PATTERNS BLOCKED BY EMA!")
    
    if i >= 2:
        break

# Check for common issues
print("\n=== POTENTIAL ISSUES ===")

if overall['patterns_detected'] < 100:
    print("❌ Very few patterns detected. Pattern detection might be too strict.")

if overall['ema_filter_blocked'] > overall['patterns_detected'] * 0.9:
    print("❌ Over 90% of patterns blocked by EMA filter. Market might be bearish or EMA calculation issue.")

if overall['total_trades'] < overall['patterns_detected'] * 0.1:
    print("❌ Very low trade-to-pattern ratio. Check entry conditions.")

# Check date ranges
min_start = min(datetime.fromisoformat(r['start_date']) for r in data['results'] if r['start_date'])
max_end = max(datetime.fromisoformat(r['end_date']) for r in data['results'] if r['end_date'])
actual_days = (max_end - min_start).days
print(f"\nActual data range: {actual_days} days")
if actual_days < config['days_back'] * 0.9:
    print(f"⚠️ Data range ({actual_days} days) is less than requested ({config['days_back']} days)")