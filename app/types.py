"""Type definitions and data models for the backtesting system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import pandas as pd
from pydantic import BaseModel, Field


class Timeframe(str, Enum):
    """Supported trading timeframes."""
    
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"


class PatternType(str, Enum):
    """Candlestick pattern types."""
    
    HAMMER = "Hammer"
    SHOOTING_STAR = "Shooting Star"
    DOJI = "Doji"
    BULLISH_ENGULFING = "Bullish Engulfing"
    BEARISH_ENGULFING = "Bearish Engulfing"
    MORNING_STAR = "Morning Star"
    EVENING_STAR = "Evening Star"


class ExitReason(str, Enum):
    """Position exit reasons."""
    
    TAKE_PROFIT = "Take Profit"
    STOP_LOSS = "Stop Loss"
    EMA_BEARISH = "EMA Bearish Exit"
    FORCED_CLOSE = "Forced Close"


@dataclass
class Kline:
    """Single candlestick data."""
    
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: datetime
    quote_volume: float
    trades: int
    taker_buy_base_volume: float
    taker_buy_quote_volume: float


@dataclass
class Position:
    """Trading position data."""
    
    symbol: str
    timeframe: str
    entry_time: datetime
    entry_price: float
    quantity: float
    pattern: PatternType
    entry_ema_short: float
    entry_ema_long: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    exit_ema_short: Optional[float] = None
    exit_ema_long: Optional[float] = None
    pnl: float = 0.0
    pnl_percent: float = 0.0
    fees: float = 0.0
    net_pnl: float = 0.0
    
    def calculate_pnl(self, exit_price: float, fee_percent: float) -> None:
        """Calculate P&L including fees."""
        if self.exit_price is None:
            self.exit_price = exit_price
        
        gross_pnl = (self.exit_price - self.entry_price) * self.quantity
        entry_fee = self.entry_price * self.quantity * fee_percent
        exit_fee = self.exit_price * self.quantity * fee_percent
        self.fees = entry_fee + exit_fee
        self.pnl = gross_pnl
        self.net_pnl = gross_pnl - self.fees
        self.pnl_percent = (self.exit_price - self.entry_price) / self.entry_price


@dataclass
class BacktestResult:
    """Results for a single symbol/timeframe backtest."""
    
    symbol: str
    timeframe: str
    positions: list[Position] = field(default_factory=list)
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_fees: float = 0.0
    net_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    hodl_return: float = 0.0
    hodl_pnl: float = 0.0
    first_price: float = 0.0
    last_price: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ema_filter_blocked: int = 0
    patterns_detected: int = 0


class CacheData(BaseModel):
    """Cache file structure."""
    
    klines: list[dict[str, Any]] = Field(default_factory=list)
    last_update: str = Field(...)
    cached_at: str = Field(...)


class CacheMetadata(BaseModel):
    """Cache metadata structure."""
    
    last_update: str = Field(...)
    symbols: dict[str, dict[str, Any]] = Field(default_factory=dict)


class PositionReport(BaseModel):
    """Position data for JSON report."""
    
    entry_time: str
    entry_price: float
    exit_time: str
    exit_price: float
    quantity: float
    pattern: str
    exit_reason: str
    entry_ema_short: float
    entry_ema_long: float
    exit_ema_short: float
    exit_ema_long: float
    pnl: float
    pnl_percent: float
    fees: float
    net_pnl: float


class SymbolTimeframeResult(BaseModel):
    """Results for a symbol/timeframe combination."""
    
    symbol: str
    timeframe: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_fees: float
    net_pnl: float
    avg_win: float
    avg_loss: float
    hodl_return: float
    hodl_pnl: float
    first_price: float
    last_price: float
    start_date: str
    end_date: str
    ema_filter_blocked: int
    patterns_detected: int
    positions: list[PositionReport]


class TimeframeSummary(BaseModel):
    """Summary statistics for a timeframe."""
    
    timeframe: str
    total_trades: int
    total_pnl: float
    net_pnl: float
    avg_win_rate: float
    symbols_traded: int


class BacktestReport(BaseModel):
    """Complete backtest report."""
    
    generated_at: str
    configuration: dict[str, Any]
    overall_stats: dict[str, Any]
    best_timeframe: str
    timeframe_summaries: list[TimeframeSummary]
    results: list[SymbolTimeframeResult]