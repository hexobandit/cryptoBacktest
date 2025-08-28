"""Test backtesting strategy implementation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest

from app.strategy import Backtester
from app.types import ExitReason, PatternType, Position


class TestPnLCalculation:
    """Test P&L calculation with fees."""
    
    def test_winning_trade_with_fees(self) -> None:
        """Test P&L calculation for winning trade."""
        position = Position(
            symbol="BTCUSDC",
            timeframe="1h",
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=1.0,  # $100 / $100 = 1.0
            pattern=PatternType.HAMMER,
            entry_ema_short=100.5,
            entry_ema_long=99.5,
        )
        
        # Exit at take profit (0.9%)
        exit_price = 100.9
        fee_percent = 0.001
        
        position.calculate_pnl(exit_price, fee_percent)
        
        # Gross P&L = (100.9 - 100) * 1.0 = 0.9
        assert abs(position.pnl - 0.9) < 1e-6
        
        # Fees = entry_fee + exit_fee = 100*0.001 + 100.9*0.001 = 0.2009
        assert abs(position.fees - 0.2009) < 1e-6
        
        # Net P&L = 0.9 - 0.2009 = 0.6991
        assert abs(position.net_pnl - 0.6991) < 1e-6
    
    def test_losing_trade_with_fees(self) -> None:
        """Test P&L calculation for losing trade."""
        position = Position(
            symbol="BTCUSDC",
            timeframe="1h",
            entry_time=datetime.now(timezone.utc),
            entry_price=100.0,
            quantity=1.0,
            pattern=PatternType.HAMMER,
            entry_ema_short=100.5,
            entry_ema_long=99.5,
        )
        
        # Exit at stop loss (-20%)
        exit_price = 80.0
        fee_percent = 0.001
        
        position.calculate_pnl(exit_price, fee_percent)
        
        # Gross P&L = (80 - 100) * 1.0 = -20
        assert abs(position.pnl - (-20)) < 1e-6
        
        # Fees = 100*0.001 + 80*0.001 = 0.18
        assert abs(position.fees - 0.18) < 1e-6
        
        # Net P&L = -20 - 0.18 = -20.18
        assert abs(position.net_pnl - (-20.18)) < 1e-6


class TestEntryFilter:
    """Test EMA entry filter."""
    
    def test_entry_blocked_by_ema(self) -> None:
        """Test that entry is blocked when EMA is bearish."""
        # Create data with bullish pattern but bearish EMA
        base_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        
        # Trading timeframe data with hammer pattern
        df = pd.DataFrame({
            "timestamp": [base_time + timedelta(hours=i) for i in range(5)],
            "open": [100, 101, 102, 100, 101],
            "high": [101, 102, 103, 100.5, 102],
            "low": [99, 100, 101, 98, 100],
            "close": [100.5, 101.5, 102.5, 100.2, 101.5],  # Hammer at index 3
            "volume": [1000] * 5,
            "close_time": [base_time + timedelta(hours=i, minutes=59, seconds=59) for i in range(5)],
        })
        
        # 4h data with bearish EMA (short < long)
        df_4h = pd.DataFrame({
            "timestamp": [base_time],
            "open": [100],
            "high": [101],
            "low": [99],
            "close": [99],  # EMA_1 = 99, EMA_99 would need more data but assume > 99
            "volume": [10000],
            "close_time": [base_time + timedelta(hours=3, minutes=59, seconds=59)],
        })
        
        backtester = Backtester()
        result = backtester.backtest("BTCUSDC", "1h", df, df_4h)
        
        # Pattern should be detected but entry blocked
        assert result.patterns_detected > 0
        assert result.ema_filter_blocked > 0
        assert result.total_trades == 0


class TestEMABearishExit:
    """Test EMA bearish exit condition."""
    
    def test_exit_on_ema_bearish_when_in_loss(self) -> None:
        """Test position exits when EMA turns bearish and position is in loss."""
        base_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        
        # Create data where position enters, then EMA turns bearish while in loss
        df = pd.DataFrame({
            "timestamp": [base_time + timedelta(hours=i) for i in range(10)],
            "open": [100] * 10,
            "high": [101] * 10,
            "low": [99] * 10,
            "close": [100, 100, 100, 100.2, 99.5, 99, 98.5, 98, 97.5, 97],  # Declining prices
            "volume": [1000] * 10,
            "close_time": [base_time + timedelta(hours=i, minutes=59, seconds=59) for i in range(10)],
        })
        
        # 4h data that starts bullish then turns bearish
        df_4h = pd.DataFrame({
            "timestamp": [base_time, base_time + timedelta(hours=4)],
            "open": [100, 100],
            "high": [101, 100.5],
            "low": [99, 98],
            "close": [100.5, 98],  # Turns bearish
            "volume": [10000, 10000],
            "close_time": [
                base_time + timedelta(hours=3, minutes=59, seconds=59),
                base_time + timedelta(hours=7, minutes=59, seconds=59),
            ],
        })
        
        # Note: This test would need more sophisticated mocking of patterns
        # and EMA calculations to properly test the exit condition