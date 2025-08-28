"""Binance API client with retry logic and rate limiting."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from binance.spot import Spot
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from app.config import settings


class BinanceClient:
    """Binance API client with retry logic."""
    
    def __init__(self) -> None:
        """Initialize Binance client."""
        self.client = Spot(
            api_key=settings.binance_api_key,
            api_secret=settings.binance_api_secret,
            base_url=settings.api_base_url,
        )
        self.rate_limit_delay = settings.rate_limit_delay
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10) + wait_random(0, 1),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )
    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000,
    ) -> list[list[Any]]:
        """
        Fetch klines from Binance with retry logic.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval (1m, 5m, 15m, etc.)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            limit: Number of klines to fetch (max 1000)
        
        Returns:
            List of kline data
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
        }
        
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        
        response = self.client.klines(**params)
        
        # Add small delay to respect rate limits
        time.sleep(self.rate_limit_delay)
        
        return response
    
    def fetch_klines_batch(
        self,
        symbol: str,
        interval: str,
        days_back: int,
        end_time: Optional[datetime] = None,
    ) -> list[list[Any]]:
        """
        Fetch multiple batches of klines to cover the requested period.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            days_back: Number of days of historical data
            end_time: End time for data (default: now)
        
        Returns:
            Combined list of all klines
        """
        if end_time is None:
            end_time = datetime.now(timezone.utc)
        
        start_time = end_time - timedelta(days=days_back)
        
        # Convert to milliseconds
        start_ms = int(start_time.timestamp() * 1000)
        end_ms = int(end_time.timestamp() * 1000)
        
        all_klines = []
        current_start = start_ms
        
        while current_start < end_ms:
            # Fetch batch
            batch = self.fetch_klines(
                symbol=symbol,
                interval=interval,
                start_time=current_start,
                end_time=end_ms,
                limit=settings.klines_limit,
            )
            
            if not batch:
                break
            
            all_klines.extend(batch)
            
            # Update start time for next batch
            # Use the close time of the last candle plus 1ms
            last_close_time = batch[-1][6]  # Close time is at index 6
            current_start = last_close_time + 1
            
            # Check if we've reached the end
            if len(batch) < settings.klines_limit:
                break
        
        # Remove duplicates while preserving order
        seen_timestamps = set()
        unique_klines = []
        for kline in all_klines:
            timestamp = kline[0]
            if timestamp not in seen_timestamps:
                seen_timestamps.add(timestamp)
                unique_klines.append(kline)
        
        return unique_klines
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol exists on Binance.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            True if symbol is valid
        """
        try:
            self.client.exchange_info(symbol=symbol)
            return True
        except Exception:
            return False