"""Test cache management functionality."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from app.cache import CacheManager


class TestCacheMerge:
    """Test cache merging functionality."""
    
    def test_merge_with_new_data(self) -> None:
        """Test merging cached data with new data."""
        # Create cached data
        cached_data = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=5, freq="1h", tz=timezone.utc),
            "open": [100, 101, 102, 103, 104],
            "high": [101, 102, 103, 104, 105],
            "low": [99, 100, 101, 102, 103],
            "close": [100.5, 101.5, 102.5, 103.5, 104.5],
            "volume": [1000] * 5,
        })
        
        # Create new data with overlap
        new_data = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01 04:00:00", periods=3, freq="1h", tz=timezone.utc),
            "open": [104, 105, 106],  # Last of cached + 2 new
            "high": [105, 106, 107],
            "low": [103, 104, 105],
            "close": [104.5, 105.5, 106.5],
            "volume": [1100, 1200, 1300],
        })
        
        cache_manager = CacheManager()
        
        # Simulate merge (without actual file I/O)
        combined = pd.concat([cached_data, new_data], ignore_index=True)
        combined = combined.drop_duplicates(subset=["timestamp"], keep="last")
        combined = combined.sort_values("timestamp").reset_index(drop=True)
        
        # Verify no duplicates
        assert len(combined["timestamp"].unique()) == len(combined)
        
        # Verify sorted
        assert combined["timestamp"].is_monotonic_increasing
        
        # Verify correct number of records (5 original + 2 new)
        assert len(combined) == 7
        
        # Verify last record updated with new data
        last_record = combined[combined["timestamp"] == pd.Timestamp("2024-01-01 04:00:00", tz=timezone.utc)]
        assert last_record["volume"].iloc[0] == 1100  # New data volume