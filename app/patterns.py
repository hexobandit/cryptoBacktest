"""Candlestick pattern detection functions."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from app.types import PatternType


def detect_hammer(candle: pd.Series) -> bool:
    """
    Detect hammer pattern.
    
    Hammer criteria:
    - Small body at upper part of range
    - Lower shadow at least 2x body size
    - Little to no upper shadow
    
    Args:
        candle: Single candle data
    
    Returns:
        True if hammer pattern detected
    """
    body = abs(candle["close"] - candle["open"])
    total_range = candle["high"] - candle["low"]
    
    if total_range == 0:
        return False
    
    upper_shadow = candle["high"] - max(candle["open"], candle["close"])
    lower_shadow = min(candle["open"], candle["close"]) - candle["low"]
    
    # Small body relative to range
    if body > 0.3 * total_range:
        return False
    
    # Lower shadow at least 2x body
    if lower_shadow < 2 * body:
        return False
    
    # Upper shadow should be small
    if upper_shadow > 0.1 * total_range:
        return False
    
    return True


def detect_shooting_star(candle: pd.Series) -> bool:
    """
    Detect shooting star pattern.
    
    Shooting star criteria:
    - Small body at lower part of range
    - Upper shadow at least 2x body size
    - Little to no lower shadow
    
    Args:
        candle: Single candle data
    
    Returns:
        True if shooting star pattern detected
    """
    body = abs(candle["close"] - candle["open"])
    total_range = candle["high"] - candle["low"]
    
    if total_range == 0:
        return False
    
    upper_shadow = candle["high"] - max(candle["open"], candle["close"])
    lower_shadow = min(candle["open"], candle["close"]) - candle["low"]
    
    # Small body relative to range
    if body > 0.3 * total_range:
        return False
    
    # Upper shadow at least 2x body
    if upper_shadow < 2 * body:
        return False
    
    # Lower shadow should be small
    if lower_shadow > 0.1 * total_range:
        return False
    
    return True


def detect_doji(candle: pd.Series) -> bool:
    """
    Detect doji pattern.
    
    Doji criteria:
    - Body is very small relative to range (≤ 10%)
    
    Args:
        candle: Single candle data
    
    Returns:
        True if doji pattern detected
    """
    body = abs(candle["close"] - candle["open"])
    total_range = candle["high"] - candle["low"]
    
    if total_range == 0:
        return False
    
    return body <= 0.1 * total_range


def detect_bullish_engulfing(prev_candle: pd.Series, curr_candle: pd.Series) -> bool:
    """
    Detect bullish engulfing pattern.
    
    Bullish engulfing criteria:
    - Previous candle is bearish (close < open)
    - Current candle is bullish (close > open)
    - Current body completely engulfs previous body
    
    Args:
        prev_candle: Previous candle data
        curr_candle: Current candle data
    
    Returns:
        True if bullish engulfing pattern detected
    """
    # Previous candle must be bearish
    if prev_candle["close"] >= prev_candle["open"]:
        return False
    
    # Current candle must be bullish
    if curr_candle["close"] <= curr_candle["open"]:
        return False
    
    # Current open must be lower than previous close
    if curr_candle["open"] >= prev_candle["close"]:
        return False
    
    # Current close must be higher than previous open
    if curr_candle["close"] <= prev_candle["open"]:
        return False
    
    return True


def detect_bearish_engulfing(prev_candle: pd.Series, curr_candle: pd.Series) -> bool:
    """
    Detect bearish engulfing pattern.
    
    Bearish engulfing criteria:
    - Previous candle is bullish (close > open)
    - Current candle is bearish (close < open)
    - Current body completely engulfs previous body
    
    Args:
        prev_candle: Previous candle data
        curr_candle: Current candle data
    
    Returns:
        True if bearish engulfing pattern detected
    """
    # Previous candle must be bullish
    if prev_candle["close"] <= prev_candle["open"]:
        return False
    
    # Current candle must be bearish
    if curr_candle["close"] >= curr_candle["open"]:
        return False
    
    # Current open must be higher than previous close
    if curr_candle["open"] <= prev_candle["close"]:
        return False
    
    # Current close must be lower than previous open
    if curr_candle["close"] >= prev_candle["open"]:
        return False
    
    return True


def detect_morning_star(
    first: pd.Series, middle: pd.Series, third: pd.Series
) -> bool:
    """
    Detect morning star pattern.
    
    Morning star criteria:
    - First candle: bearish with significant body
    - Middle candle: small body (< 50% of first body)
    - Third candle: bullish, closes above midpoint of first candle
    
    Args:
        first: First candle data
        middle: Middle candle data
        third: Third candle data
    
    Returns:
        True if morning star pattern detected
    """
    # First candle must be bearish
    if first["close"] >= first["open"]:
        return False
    
    # Third candle must be bullish
    if third["close"] <= third["open"]:
        return False
    
    first_body = abs(first["close"] - first["open"])
    middle_body = abs(middle["close"] - middle["open"])
    
    # Middle candle must have small body
    if middle_body >= 0.5 * first_body:
        return False
    
    # Third candle should close above midpoint of first candle
    first_midpoint = (first["open"] + first["close"]) / 2
    if third["close"] <= first_midpoint:
        return False
    
    return True


def detect_evening_star(
    first: pd.Series, middle: pd.Series, third: pd.Series
) -> bool:
    """
    Detect evening star pattern.
    
    Evening star criteria:
    - First candle: bullish with significant body
    - Middle candle: small body (< 50% of first body)
    - Third candle: bearish, closes below midpoint of first candle
    
    Args:
        first: First candle data
        middle: Middle candle data
        third: Third candle data
    
    Returns:
        True if evening star pattern detected
    """
    # First candle must be bullish
    if first["close"] <= first["open"]:
        return False
    
    # Third candle must be bearish
    if third["close"] >= third["open"]:
        return False
    
    first_body = abs(first["close"] - first["open"])
    middle_body = abs(middle["close"] - middle["open"])
    
    # Middle candle must have small body
    if middle_body >= 0.5 * first_body:
        return False
    
    # Third candle should close below midpoint of first candle
    first_midpoint = (first["open"] + first["close"]) / 2
    if third["close"] >= first_midpoint:
        return False
    
    return True


def detect_patterns(
    df: pd.DataFrame, index: int
) -> Optional[PatternType]:
    """
    Detect all patterns at the given index.
    
    Args:
        df: DataFrame with candle data
        index: Current candle index
    
    Returns:
        Detected pattern type or None
    """
    if index < 0 or index >= len(df):
        return None
    
    current = df.iloc[index]
    
    # Single candle patterns
    if detect_hammer(current):
        return PatternType.HAMMER
    
    if detect_shooting_star(current):
        return PatternType.SHOOTING_STAR
    
    if detect_doji(current):
        return PatternType.DOJI
    
    # Two candle patterns (need at least 2 candles)
    if index >= 1:
        previous = df.iloc[index - 1]
        
        if detect_bullish_engulfing(previous, current):
            return PatternType.BULLISH_ENGULFING
        
        if detect_bearish_engulfing(previous, current):
            return PatternType.BEARISH_ENGULFING
    
    # Three candle patterns (need at least 3 candles)
    if index >= 2:
        first = df.iloc[index - 2]
        middle = df.iloc[index - 1]
        
        if detect_morning_star(first, middle, current):
            return PatternType.MORNING_STAR
        
        if detect_evening_star(first, middle, current):
            return PatternType.EVENING_STAR
    
    return None


def is_bullish_pattern(pattern: Optional[PatternType]) -> bool:
    """
    Check if a pattern is bullish.
    
    Args:
        pattern: Pattern type
    
    Returns:
        True if pattern is bullish
    """
    if pattern is None:
        return False
    
    bullish_patterns = {
        PatternType.HAMMER,
        PatternType.BULLISH_ENGULFING,
        PatternType.MORNING_STAR,
    }
    
    return pattern in bullish_patterns