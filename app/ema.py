"""Exponential Moving Average calculation without look-ahead bias."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from app.candles import filter_complete_candles


def calculate_ema(prices: np.ndarray, period: int) -> np.ndarray:
    """
    Calculate Exponential Moving Average.
    
    Formula: EMA[i] = alpha * prices[i] + (1 - alpha) * EMA[i-1]
    Where alpha = 2 / (period + 1)
    
    Args:
        prices: Array of prices
        period: EMA period
    
    Returns:
        Array of EMA values
    """
    if len(prices) == 0:
        return np.array([])
    
    alpha = 2.0 / (period + 1)
    ema = np.zeros(len(prices))
    
    # First value is the price itself
    ema[0] = prices[0]
    
    # Calculate subsequent values
    for i in range(1, len(prices)):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]
    
    return ema


def get_ema_at_timestamp(
    df_4h: pd.DataFrame,
    target_timestamp: datetime,
    short_period: int = 1,
    long_period: int = 99,
) -> Tuple[Optional[float], Optional[float]]:
    """
    Get EMA values at a specific timestamp without look-ahead bias.
    
    Only uses 4h candles that closed strictly before the target timestamp.
    
    Args:
        df_4h: DataFrame with 4h candle data
        target_timestamp: Target timestamp for EMA calculation
        short_period: Short EMA period (default: 1)
        long_period: Long EMA period (default: 99)
    
    Returns:
        Tuple of (short_ema, long_ema) or (None, None) if not enough data
    """
    if df_4h.empty:
        return None, None
    
    # Filter to only completed candles before target timestamp
    completed_candles = filter_complete_candles(df_4h, target_timestamp)
    
    if len(completed_candles) == 0:
        return None, None
    
    # Need at least as many candles as the longest period
    if len(completed_candles) < max(short_period, long_period):
        return None, None
    
    # Get close prices
    prices = completed_candles["close"].values
    
    # Calculate EMAs
    ema_short_array = calculate_ema(prices, short_period)
    ema_long_array = calculate_ema(prices, long_period)
    
    # Return the last calculated values (most recent before target)
    ema_short = ema_short_array[-1] if len(ema_short_array) > 0 else None
    ema_long = ema_long_array[-1] if len(ema_long_array) > 0 else None
    
    return ema_short, ema_long


def is_ema_bullish(
    df_4h: pd.DataFrame,
    target_timestamp: datetime,
    short_period: int = 1,
    long_period: int = 99,
) -> bool:
    """
    Check if EMA configuration is bullish at timestamp.
    
    Bullish when short EMA > long EMA.
    
    Args:
        df_4h: DataFrame with 4h candle data
        target_timestamp: Target timestamp for check
        short_period: Short EMA period
        long_period: Long EMA period
    
    Returns:
        True if EMA configuration is bullish
    """
    ema_short, ema_long = get_ema_at_timestamp(
        df_4h, target_timestamp, short_period, long_period
    )
    
    if ema_short is None or ema_long is None:
        return False
    
    return ema_short > ema_long


def precompute_ema_series(
    df: pd.DataFrame,
    period: int,
) -> pd.Series:
    """
    Precompute EMA for entire series.
    
    Args:
        df: DataFrame with price data
        period: EMA period
    
    Returns:
        Series with EMA values aligned to DataFrame index
    """
    if df.empty:
        return pd.Series(dtype=float)
    
    prices = df["close"].values
    ema_values = calculate_ema(prices, period)
    
    return pd.Series(ema_values, index=df.index, name=f"ema_{period}")