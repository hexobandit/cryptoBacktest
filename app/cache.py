"""Cache management for historical kline data."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from app.config import settings
from app.types import CacheData, CacheMetadata


class CacheManager:
    """Manages caching of kline data."""
    
    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """Initialize cache manager."""
        self.cache_dir = cache_dir or settings.cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
    
    def get_cache_file(self, symbol: str, timeframe: str) -> Path:
        """Get cache file path for a symbol/timeframe."""
        return self.cache_dir / f"{symbol}_{timeframe}.json"
    
    def is_cache_valid(self, symbol: str, timeframe: str) -> bool:
        """
        Check if cache exists and is not expired.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
        
        Returns:
            True if cache is valid and recent
        """
        cache_file = self.get_cache_file(symbol, timeframe)
        
        if not cache_file.exists():
            return False
        
        try:
            with open(cache_file, "r") as f:
                cache_data = CacheData(**json.load(f))
            
            cached_at = datetime.fromisoformat(cache_data.cached_at)
            expiry_time = cached_at + timedelta(hours=settings.cache_expiry_hours)
            
            return datetime.now(timezone.utc) < expiry_time
        
        except (json.JSONDecodeError, ValueError):
            return False
    
    def load_cache(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Load cached kline data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
        
        Returns:
            DataFrame with kline data or None if not cached
        """
        cache_file = self.get_cache_file(symbol, timeframe)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, "r") as f:
                cache_data = CacheData(**json.load(f))
            
            if not cache_data.klines:
                return None
            
            df = pd.DataFrame(cache_data.klines)
            
            # Convert timestamps to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["close_time"] = pd.to_datetime(df["close_time"])
            
            # Ensure proper dtypes
            numeric_columns = ["open", "high", "low", "close", "volume", "quote_volume",
                             "taker_buy_base_volume", "taker_buy_quote_volume"]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            df["trades"] = pd.to_numeric(df["trades"], errors="coerce", downcast="integer")
            
            # Sort by timestamp
            df = df.sort_values("timestamp").reset_index(drop=True)
            
            return df
        
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error loading cache for {symbol}/{timeframe}: {e}")
            return None
    
    def save_cache(self, symbol: str, timeframe: str, df: pd.DataFrame) -> None:
        """
        Save kline data to cache.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            df: DataFrame with kline data
        """
        cache_file = self.get_cache_file(symbol, timeframe)
        
        # Prepare data for JSON serialization
        klines_data = df.copy()
        klines_data["timestamp"] = klines_data["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        klines_data["close_time"] = klines_data["close_time"].dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        
        cache_data = CacheData(
            klines=klines_data.to_dict("records"),
            last_update=df["timestamp"].max().isoformat() if len(df) > 0 else datetime.now(timezone.utc).isoformat(),
            cached_at=datetime.now(timezone.utc).isoformat(),
        )
        
        with open(cache_file, "w") as f:
            json.dump(cache_data.model_dump(), f, indent=2)
        
        # Update metadata
        self.update_metadata(symbol, timeframe, df)
    
    def merge_with_cache(
        self, symbol: str, timeframe: str, new_df: pd.DataFrame, days_back: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Merge new data with cached data, removing duplicates.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            new_df: New DataFrame to merge
            days_back: Number of days to keep (optional)
        
        Returns:
            Merged DataFrame
        """
        cached_df = self.load_cache(symbol, timeframe)
        
        if cached_df is None or len(cached_df) == 0:
            return new_df
        
        # Concatenate dataframes
        combined_df = pd.concat([cached_df, new_df], ignore_index=True)
        
        # Remove duplicates based on timestamp, keeping last (most recent)
        combined_df = combined_df.drop_duplicates(subset=["timestamp"], keep="last")
        
        # Sort by timestamp
        combined_df = combined_df.sort_values("timestamp").reset_index(drop=True)
        
        # Trim to days_back range if specified
        if days_back is not None:
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_back)
            combined_df = combined_df[combined_df["timestamp"] >= cutoff_time]
        
        return combined_df
    
    def get_last_cached_timestamp(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """
        Get the timestamp of the last cached candle.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
        
        Returns:
            Last timestamp or None
        """
        cached_df = self.load_cache(symbol, timeframe)
        
        if cached_df is None or len(cached_df) == 0:
            return None
        
        return cached_df["timestamp"].max()
    
    def update_metadata(self, symbol: str, timeframe: str, df: pd.DataFrame) -> None:
        """
        Update cache metadata file.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe string
            df: DataFrame with kline data
        """
        metadata = {}
        
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)
            except json.JSONDecodeError:
                pass
        
        if "symbols" not in metadata:
            metadata["symbols"] = {}
        
        key = f"{symbol}_{timeframe}"
        metadata["symbols"][key] = {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(df),
            "first_candle": df["timestamp"].min().isoformat() if len(df) > 0 else None,
            "last_candle": df["timestamp"].max().isoformat() if len(df) > 0 else None,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }
        
        metadata["last_update"] = datetime.now(timezone.utc).isoformat()
        
        with open(self.metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        print(f"Cache cleared: {self.cache_dir}")