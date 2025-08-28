"""Candlestick data processing and loading utilities."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from app.binance import BinanceClient
from app.cache import CacheManager
from app.config import settings


def parse_kline(kline: list[Any]) -> dict[str, Any]:
    """
    Parse a single kline from Binance API response.
    
    Args:
        kline: Raw kline data from API
    
    Returns:
        Parsed kline dictionary
    """
    return {
        "timestamp": pd.to_datetime(kline[0], unit="ms", utc=True),
        "open": float(kline[1]),
        "high": float(kline[2]),
        "low": float(kline[3]),
        "close": float(kline[4]),
        "volume": float(kline[5]),
        "close_time": pd.to_datetime(kline[6], unit="ms", utc=True),
        "quote_volume": float(kline[7]),
        "trades": int(kline[8]),
        "taker_buy_base_volume": float(kline[9]),
        "taker_buy_quote_volume": float(kline[10]),
    }


def klines_to_dataframe(klines: list[list[Any]]) -> pd.DataFrame:
    """
    Convert raw klines to pandas DataFrame.
    
    Args:
        klines: List of raw kline data
    
    Returns:
        DataFrame with parsed kline data
    """
    if not klines:
        return pd.DataFrame()
    
    parsed_klines = [parse_kline(kline) for kline in klines]
    df = pd.DataFrame(parsed_klines)
    
    # Ensure timestamps are UTC aware
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], utc=True)
    
    # Sort by timestamp
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    return df


def load_klines(
    symbol: str,
    timeframe: str,
    days_back: int = None,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Load kline data with caching support.
    
    Args:
        symbol: Trading pair symbol
        timeframe: Timeframe string
        days_back: Number of days of historical data
        force_refresh: Force re-download of data
    
    Returns:
        DataFrame with kline data
    """
    if days_back is None:
        days_back = settings.days_back
    
    cache_manager = CacheManager()
    client = BinanceClient()
    
    # Check if we should use cache
    if not force_refresh and cache_manager.is_cache_valid(symbol, timeframe):
        # Try incremental update
        cached_df = cache_manager.load_cache(symbol, timeframe)
        
        if cached_df is not None and len(cached_df) > 0:
            last_timestamp = cache_manager.get_last_cached_timestamp(symbol, timeframe)
            
            if last_timestamp is not None:
                # Fetch only new data
                new_klines = client.fetch_klines_batch(
                    symbol=symbol,
                    interval=timeframe,
                    days_back=1,  # Fetch recent data only
                    end_time=datetime.now(timezone.utc),
                )
                
                if new_klines:
                    new_df = klines_to_dataframe(new_klines)
                    
                    # Filter to get only candles after last cached
                    new_df = new_df[new_df["timestamp"] > last_timestamp]
                    
                    if len(new_df) > 0:
                        # Merge with cache, passing days_back parameter
                        df = cache_manager.merge_with_cache(symbol, timeframe, new_df, days_back)
                        cache_manager.save_cache(symbol, timeframe, df)
                    else:
                        df = cached_df
                else:
                    df = cached_df
                
                # Trim to requested days_back range
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_back)
                df = df[df["timestamp"] >= cutoff_time].copy()
                
                return df
    
    # Full download
    print(f"Fetching {days_back} days of {timeframe} data for {symbol}...")
    
    klines = client.fetch_klines_batch(
        symbol=symbol,
        interval=timeframe,
        days_back=days_back,
    )
    
    if not klines:
        print(f"No data received for {symbol}/{timeframe}")
        return pd.DataFrame()
    
    df = klines_to_dataframe(klines)
    
    # Save to cache
    cache_manager.save_cache(symbol, timeframe, df)
    
    print(f"Fetched {len(df)} candles for {symbol}/{timeframe}")
    
    return df


def filter_complete_candles(df: pd.DataFrame, before_timestamp: datetime) -> pd.DataFrame:
    """
    Filter to only include candles that closed before the given timestamp.
    
    Args:
        df: DataFrame with candle data
        before_timestamp: Cutoff timestamp
    
    Returns:
        Filtered DataFrame
    """
    if df.empty:
        return df
    
    # Ensure timestamp comparison is done with UTC aware datetimes
    if before_timestamp.tzinfo is None:
        before_timestamp = before_timestamp.replace(tzinfo=timezone.utc)
    
    return df[df["close_time"] < before_timestamp].copy()