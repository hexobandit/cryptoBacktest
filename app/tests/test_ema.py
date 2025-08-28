"""Test EMA calculation and look-ahead bias prevention."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from app.ema import calculate_ema, get_ema_at_timestamp


class TestEMACalculation:
    """Test EMA calculation correctness."""
    
    def test_ema_basic_calculation(self) -> None:
        """Test EMA calculation with known values."""
        # Small series with hand-computed values
        prices = np.array([10.0, 11.0, 12.0, 11.5, 13.0])
        
        # Period 1: alpha = 2/(1+1) = 1, so EMA = price
        ema_1 = calculate_ema(prices, 1)
        assert np.allclose(ema_1, prices, atol=1e-12)
        
        # Period 3: alpha = 2/(3+1) = 0.5
        ema_3 = calculate_ema(prices, 3)
        expected = np.array([10.0, 10.5, 11.25, 11.375, 12.1875])
        assert np.allclose(ema_3, expected, atol=1e-12)
    
    def test_ema_empty_array(self) -> None:
        """Test EMA with empty price array."""
        prices = np.array([])
        ema = calculate_ema(prices, 10)
        assert len(ema) == 0
    
    def test_ema_single_value(self) -> None:
        """Test EMA with single value."""
        prices = np.array([100.0])
        ema = calculate_ema(prices, 10)
        assert len(ema) == 1
        assert ema[0] == 100.0


class TestNoLookAheadBias:
    """Test that EMA calculation has no look-ahead bias."""
    
    def test_no_future_data_leak(self) -> None:
        """Ensure EMAs only use completed candles before target time."""
        # Create synthetic 4h candles
        base_time = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
        
        candle_data = []
        for i in range(10):
            open_time = base_time + timedelta(hours=4 * i)
            close_time = open_time + timedelta(hours=4) - timedelta(seconds=1)
            candle_data.append({
                "timestamp": open_time,
                "open": 100 + i,
                "high": 102 + i,
                "low": 99 + i,
                "close": 101 + i,
                "volume": 1000,
                "close_time": close_time,
            })
        
        df_4h = pd.DataFrame(candle_data)
        
        # Target time inside the 5th candle (index 4)
        # This candle opens at 16:00 and closes at 19:59:59
        target_time = base_time + timedelta(hours=18)  # 18:00
        
        # Get EMAs at target time
        ema_short, ema_long = get_ema_at_timestamp(df_4h, target_time, 1, 3)
        
        # Should only use candles 0-3 (first 4 candles)
        # The 5th candle (index 4) closes after target, so shouldn't be used
        assert ema_short is not None
        assert ema_long is not None
        
        # Verify values using only first 4 candles
        prices = df_4h.iloc[:4]["close"].values
        expected_ema_1 = calculate_ema(prices, 1)[-1]
        expected_ema_3 = calculate_ema(prices, 3)[-1]
        
        assert abs(ema_short - expected_ema_1) < 1e-10
        assert abs(ema_long - expected_ema_3) < 1e-10
    
    def test_insufficient_data(self) -> None:
        """Test behavior when insufficient data for EMA calculation."""
        df_4h = pd.DataFrame({
            "timestamp": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.0],
            "volume": [1000],
            "close_time": [datetime(2024, 1, 1, 3, 59, 59, tzinfo=timezone.utc)],
        })
        
        target_time = datetime(2024, 1, 2, tzinfo=timezone.utc)
        
        # Need at least 99 candles for EMA_99
        ema_short, ema_long = get_ema_at_timestamp(df_4h, target_time, 1, 99)
        
        assert ema_short is None
        assert ema_long is None