"""Test candlestick pattern detection."""

from __future__ import annotations

import pandas as pd
import pytest

from app.patterns import (
    detect_bearish_engulfing,
    detect_bullish_engulfing,
    detect_doji,
    detect_evening_star,
    detect_hammer,
    detect_morning_star,
    detect_shooting_star,
)


class TestSingleCandlePatterns:
    """Test single candle pattern detection."""
    
    def test_hammer_detection(self) -> None:
        """Test hammer pattern detection."""
        # Valid hammer: small body, long lower shadow
        hammer = pd.Series({
            "open": 100.0,
            "high": 100.5,
            "low": 98.0,
            "close": 100.2,
        })
        assert detect_hammer(hammer) is True
        
        # Invalid: body too large
        not_hammer = pd.Series({
            "open": 100.0,
            "high": 102.0,
            "low": 98.0,
            "close": 101.5,
        })
        assert detect_hammer(not_hammer) is False
        
        # Invalid: upper shadow too large
        not_hammer2 = pd.Series({
            "open": 100.0,
            "high": 102.0,
            "low": 98.0,
            "close": 100.2,
        })
        assert detect_hammer(not_hammer2) is False
    
    def test_shooting_star_detection(self) -> None:
        """Test shooting star pattern detection."""
        # Valid shooting star: small body, long upper shadow
        star = pd.Series({
            "open": 100.0,
            "high": 102.0,
            "low": 99.8,
            "close": 99.9,
        })
        assert detect_shooting_star(star) is True
        
        # Invalid: lower shadow too large
        not_star = pd.Series({
            "open": 100.0,
            "high": 102.0,
            "low": 98.0,
            "close": 99.9,
        })
        assert detect_shooting_star(not_star) is False
    
    def test_doji_detection(self) -> None:
        """Test doji pattern detection."""
        # Valid doji: very small body
        doji = pd.Series({
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.05,
        })
        assert detect_doji(doji) is True
        
        # Invalid: body too large (> 10% of range)
        not_doji = pd.Series({
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.3,
        })
        assert detect_doji(not_doji) is False


class TestTwoCandlePatterns:
    """Test two-candle pattern detection."""
    
    def test_bullish_engulfing(self) -> None:
        """Test bullish engulfing pattern detection."""
        # Valid: bearish followed by larger bullish
        prev = pd.Series({
            "open": 100.0,
            "high": 100.5,
            "low": 99.0,
            "close": 99.5,
        })
        curr = pd.Series({
            "open": 99.3,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
        })
        assert detect_bullish_engulfing(prev, curr) is True
        
        # Invalid: previous not bearish
        prev_bull = pd.Series({
            "open": 99.5,
            "high": 100.5,
            "low": 99.0,
            "close": 100.0,
        })
        assert detect_bullish_engulfing(prev_bull, curr) is False
    
    def test_bearish_engulfing(self) -> None:
        """Test bearish engulfing pattern detection."""
        # Valid: bullish followed by larger bearish
        prev = pd.Series({
            "open": 99.5,
            "high": 100.5,
            "low": 99.0,
            "close": 100.0,
        })
        curr = pd.Series({
            "open": 100.2,
            "high": 100.5,
            "low": 99.0,
            "close": 99.3,
        })
        assert detect_bearish_engulfing(prev, curr) is True
        
        # Invalid: current not bearish
        curr_bull = pd.Series({
            "open": 100.2,
            "high": 101.0,
            "low": 99.5,
            "close": 100.8,
        })
        assert detect_bearish_engulfing(prev, curr_bull) is False


class TestThreeCandlePatterns:
    """Test three-candle pattern detection."""
    
    def test_morning_star(self) -> None:
        """Test morning star pattern detection."""
        # Valid morning star
        first = pd.Series({
            "open": 100.0,
            "high": 100.5,
            "low": 98.0,
            "close": 98.5,  # Bearish
        })
        middle = pd.Series({
            "open": 98.3,
            "high": 98.7,
            "low": 98.0,
            "close": 98.5,  # Small body
        })
        third = pd.Series({
            "open": 98.6,
            "high": 100.0,
            "low": 98.5,
            "close": 99.8,  # Bullish, above midpoint
        })
        assert detect_morning_star(first, middle, third) is True
        
        # Invalid: middle body too large
        middle_large = pd.Series({
            "open": 98.0,
            "high": 99.5,
            "low": 97.5,
            "close": 99.2,  # Body > 50% of first
        })
        assert detect_morning_star(first, middle_large, third) is False
    
    def test_evening_star(self) -> None:
        """Test evening star pattern detection."""
        # Valid evening star
        first = pd.Series({
            "open": 98.5,
            "high": 100.5,
            "low": 98.0,
            "close": 100.0,  # Bullish
        })
        middle = pd.Series({
            "open": 100.1,
            "high": 100.4,
            "low": 99.9,
            "close": 100.2,  # Small body
        })
        third = pd.Series({
            "open": 100.1,
            "high": 100.2,
            "low": 98.5,
            "close": 98.8,  # Bearish, below midpoint
        })
        assert detect_evening_star(first, middle, third) is True
        
        # Invalid: third doesn't close below midpoint
        third_high = pd.Series({
            "open": 100.1,
            "high": 100.2,
            "low": 99.0,
            "close": 99.5,  # Still above midpoint (99.25)
        })
        assert detect_evening_star(first, middle, third_high) is False