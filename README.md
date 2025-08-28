# Cryptocurrency Backtesting Tool

A Python 3.11 backtesting tool for cryptocurrency trading strategies using candlestick patterns and EMA filtering on Binance Spot market data.

## Features

- **Data Source**: Binance Spot historical klines for 12 major cryptocurrencies
- **Timeframes**: Support for 1m, 5m, 15m, 30m, 1h, and 4h
- **Strategy**: Long-only positions with candlestick pattern entries filtered by 4h EMA trend
- **Pattern Detection**: 7 candlestick patterns (Hammer, Shooting Star, Doji, Bullish/Bearish Engulfing, Morning/Evening Star)
- **Risk Management**: Take profit (+0.9%), Stop loss (-20%), EMA bearish exit
- **Caching**: Intelligent data caching with incremental updates
- **Reporting**: Comprehensive JSON reports and console summaries

## Installation

### Prerequisites

- Python 3.11 or higher
- Binance API credentials (optional for public data)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd cryptoBacktest
```

2. Install dependencies:
```bash
pip install -e .
```

Or for development:
```bash
pip install -e ".[dev]"
```

3. Configure API credentials (optional):
```bash
cp .env.example .env
# Edit .env with your Binance API credentials
```

## Usage

### Basic Usage

Run backtest with default settings (100 days of data):
```bash
python -m app
```

### Command-line Options

```bash
python -m app [OPTIONS]

Options:
  --days DAYS          Number of days of historical data (default: 100)
  --refresh            Force full re-download of data
  --clear-cache        Clear all cached data and exit
  --symbols SYMBOLS    Specific symbols to test
  --timeframes TF      Specific timeframes to test
```

### Examples

Test specific symbols for 30 days:
```bash
python -m app --days 30 --symbols BTCUSDC ETHUSDC
```

Test specific timeframes with fresh data:
```bash
python -m app --timeframes 1h 4h --refresh
```

Clear cache:
```bash
python -m app --clear-cache
```

## Strategy Details

### Entry Conditions
- Bullish candlestick pattern detected (Hammer, Bullish Engulfing, Morning Star)
- 4h EMA_1 > EMA_99 (trend filter)
- No existing open position

### Exit Conditions (First Hit)
1. **Take Profit**: +0.9% from entry
2. **Stop Loss**: -20% from entry
3. **EMA Bearish Exit**: Position in loss AND 4h EMA_1 < EMA_99
4. **Forced Close**: End of dataset

### Fees
- 0.1% per side (entry and exit)
- Applied to both winning and losing trades

## Configuration

Default settings in `app/config.py`:
- Trade amount: $100 per position
- Take profit: 0.9%
- Stop loss: -20%
- EMA periods: 1 and 99 on 4h timeframe
- Symbols: BTC, ETH, BNB, ADA, XRP, DOGE, SOL, PEPE, SHIB, XLM, LINK, IOTA (all USDC pairs)

## Output

### Console Summary
- Overall statistics (trades, win rate, P&L)
- Timeframe performance comparison
- Top performing symbol/timeframe combinations

### JSON Report
Saved as `backtest_results_ema_4h.json` containing:
- Configuration parameters
- Overall statistics
- Best performing timeframe
- Detailed results per symbol/timeframe
- Individual position details with entry/exit data

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app
```

## Project Structure

```
cryptoBacktest/
├── app/
│   ├── __init__.py
│   ├── __main__.py       # Entry point
│   ├── config.py         # Configuration settings
│   ├── binance.py        # Binance API client
│   ├── cache.py          # Cache management
│   ├── candles.py        # Candlestick data processing
│   ├── ema.py            # EMA calculations
│   ├── patterns.py       # Pattern detection
│   ├── strategy.py       # Backtesting engine
│   ├── report.py         # Report generation
│   ├── cli.py            # CLI interface
│   ├── types.py          # Data models
│   └── tests/            # Test suite
├── data_cache/           # Cached market data
├── pyproject.toml        # Project configuration
├── .env.example          # Environment variables template
└── README.md
```

## API Rate Limits

The tool respects Binance API rate limits:
- Automatic retry with exponential backoff
- Small delays between requests
- Efficient chunking for large data requests

## Data Integrity

- No look-ahead bias: EMAs computed only on completed candles
- UTC timestamps throughout
- Duplicate removal in cache merging
- Deterministic calculations

## Limitations

- Requires internet connection for initial data fetch
- Cache expires after 24 hours
- Maximum 1000 candles per API request
- Binance API rate limits apply

## Security

- API credentials stored in environment variables
- Never commit `.env` file
- Credentials optional for public market data

## License

See LICENSE file for details.
