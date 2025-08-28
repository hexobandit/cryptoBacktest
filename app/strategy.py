"""Backtesting engine with trading strategy implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pandas as pd

from app.candles import load_klines
from app.config import settings
from app.ema import get_ema_at_timestamp, is_ema_bullish
from app.patterns import detect_patterns, is_bullish_pattern
from app.types import BacktestResult, ExitReason, Position


class Backtester:
    """Backtesting engine for candlestick pattern strategy."""
    
    def __init__(
        self,
        trade_amount: float = None,
        fee_percent: float = None,
        take_profit: float = None,
        stop_loss: float = None,
    ) -> None:
        """
        Initialize backtester.
        
        Args:
            trade_amount: Amount to trade per position
            fee_percent: Fee percentage per trade
            take_profit: Take profit percentage
            stop_loss: Stop loss percentage
        """
        self.trade_amount = trade_amount or settings.trade_amount
        self.fee_percent = fee_percent or settings.trade_fee_percent
        self.take_profit = take_profit or settings.take_profit_percent
        self.stop_loss = stop_loss or settings.stop_loss_percent
        self.ema_short_period = settings.ema_short_period
        self.ema_long_period = settings.ema_long_period
    
    def backtest(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        df_4h: pd.DataFrame,
    ) -> BacktestResult:
        """
        Run backtest on historical data.
        
        Args:
            symbol: Trading symbol
            timeframe: Trading timeframe
            df: DataFrame with candle data for trading timeframe
            df_4h: DataFrame with 4h candle data for EMA calculation
        
        Returns:
            Backtest results
        """
        result = BacktestResult(
            symbol=symbol,
            timeframe=timeframe,
            start_date=df["timestamp"].min() if len(df) > 0 else None,
            end_date=df["timestamp"].max() if len(df) > 0 else None,
        )
        
        if len(df) < 3:  # Need at least 3 candles for patterns
            return result
        
        # Calculate HODL benchmark
        if len(df) > 0:
            result.first_price = df.iloc[0]["close"]
            result.last_price = df.iloc[-1]["close"]
            result.hodl_return = (result.last_price - result.first_price) / result.first_price
            result.hodl_pnl = self.trade_amount * result.hodl_return
        
        current_position: Optional[Position] = None
        
        # Iterate through candles (starting from index 2 for 3-candle patterns)
        for i in range(2, len(df)):
            candle = df.iloc[i]
            timestamp = candle["timestamp"]
            
            # Check for pattern
            pattern = detect_patterns(df, i)
            
            if pattern is not None:
                result.patterns_detected += 1
            
            # Handle open position first
            if current_position is not None:
                exit_reason = None
                exit_price = candle["close"]
                
                # Check exit conditions
                current_return = (exit_price - current_position.entry_price) / current_position.entry_price
                
                # Take profit
                if current_return >= self.take_profit:
                    exit_reason = ExitReason.TAKE_PROFIT
                    exit_price = current_position.entry_price * (1 + self.take_profit)
                
                # Stop loss
                elif current_return <= self.stop_loss:
                    exit_reason = ExitReason.STOP_LOSS
                    exit_price = current_position.entry_price * (1 + self.stop_loss)
                
                # EMA bearish exit (only if in loss)
                elif current_return < 0:
                    ema_short, ema_long = get_ema_at_timestamp(
                        df_4h, timestamp, self.ema_short_period, self.ema_long_period
                    )
                    if ema_short is not None and ema_long is not None and ema_short < ema_long:
                        exit_reason = ExitReason.EMA_BEARISH
                
                # Exit position if conditions met
                if exit_reason is not None:
                    current_position.exit_time = timestamp
                    current_position.exit_price = exit_price
                    current_position.exit_reason = exit_reason
                    
                    # Get exit EMAs
                    exit_ema_short, exit_ema_long = get_ema_at_timestamp(
                        df_4h, timestamp, self.ema_short_period, self.ema_long_period
                    )
                    current_position.exit_ema_short = exit_ema_short
                    current_position.exit_ema_long = exit_ema_long
                    
                    # Calculate P&L
                    current_position.calculate_pnl(exit_price, self.fee_percent)
                    
                    # Add to results
                    result.positions.append(current_position)
                    result.total_trades += 1
                    
                    if current_position.net_pnl > 0:
                        result.winning_trades += 1
                    else:
                        result.losing_trades += 1
                    
                    current_position = None
            
            # Check for entry if no position
            if current_position is None and pattern is not None and is_bullish_pattern(pattern):
                # Check EMA filter
                ema_short, ema_long = get_ema_at_timestamp(
                    df_4h, timestamp, self.ema_short_period, self.ema_long_period
                )
                
                if ema_short is not None and ema_long is not None:
                    if ema_short > ema_long:
                        # Enter position
                        entry_price = candle["close"]
                        quantity = self.trade_amount / entry_price
                        
                        current_position = Position(
                            symbol=symbol,
                            timeframe=timeframe,
                            entry_time=timestamp,
                            entry_price=entry_price,
                            quantity=quantity,
                            pattern=pattern,
                            entry_ema_short=ema_short,
                            entry_ema_long=ema_long,
                        )
                    else:
                        # EMA filter blocked entry
                        result.ema_filter_blocked += 1
        
        # Force close any open position at end
        if current_position is not None:
            last_candle = df.iloc[-1]
            current_position.exit_time = last_candle["timestamp"]
            current_position.exit_price = last_candle["close"]
            current_position.exit_reason = ExitReason.FORCED_CLOSE
            
            # Get exit EMAs
            exit_ema_short, exit_ema_long = get_ema_at_timestamp(
                df_4h, last_candle["timestamp"], self.ema_short_period, self.ema_long_period
            )
            current_position.exit_ema_short = exit_ema_short
            current_position.exit_ema_long = exit_ema_long
            
            # Calculate P&L
            current_position.calculate_pnl(last_candle["close"], self.fee_percent)
            
            # Add to results
            result.positions.append(current_position)
            result.total_trades += 1
            
            if current_position.net_pnl > 0:
                result.winning_trades += 1
            else:
                result.losing_trades += 1
        
        # Calculate aggregate statistics
        if result.total_trades > 0:
            result.win_rate = result.winning_trades / result.total_trades
            result.total_pnl = sum(p.pnl for p in result.positions)
            result.total_fees = sum(p.fees for p in result.positions)
            result.net_pnl = sum(p.net_pnl for p in result.positions)
            
            winning_positions = [p for p in result.positions if p.net_pnl > 0]
            losing_positions = [p for p in result.positions if p.net_pnl <= 0]
            
            if winning_positions:
                result.avg_win = sum(p.net_pnl for p in winning_positions) / len(winning_positions)
            
            if losing_positions:
                result.avg_loss = sum(p.net_pnl for p in losing_positions) / len(losing_positions)
        
        return result


def run_backtest(
    symbol: str,
    timeframe: str,
    days_back: int = None,
    force_refresh: bool = False,
) -> Optional[BacktestResult]:
    """
    Run backtest for a symbol/timeframe combination.
    
    Args:
        symbol: Trading symbol
        timeframe: Trading timeframe
        days_back: Number of days of historical data
        force_refresh: Force refresh of cached data
    
    Returns:
        Backtest results or None if data unavailable
    """
    # Load trading timeframe data
    df = load_klines(symbol, timeframe, days_back, force_refresh)
    
    if df.empty:
        print(f"No data available for {symbol}/{timeframe}")
        return None
    
    # Load 4h data for EMA calculation
    df_4h = load_klines(symbol, "4h", days_back, force_refresh)
    
    if df_4h.empty:
        print(f"No 4h data available for {symbol}")
        return None
    
    # Run backtest
    backtester = Backtester()
    result = backtester.backtest(symbol, timeframe, df, df_4h)
    
    return result