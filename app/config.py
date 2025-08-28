"""Configuration settings for the backtesting system."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # API credentials
    binance_api_key: Optional[str] = os.getenv("BINANCE_API_KEY")
    binance_api_secret: Optional[str] = os.getenv("BINANCE_API_SECRET")
    
    # Trading parameters
    trade_amount: float = 100.0
    trade_fee_percent: float = 0.001
    take_profit_percent: float = 0.08
    stop_loss_percent: float = -0.06
    
    # EMA parameters
    ema_short_period: int = 1
    ema_long_period: int = 99
    ema_timeframe: str = "4h"
    
    # Data parameters
    days_back: int = 100
    cache_dir: Path = Path("data_cache")
    cache_expiry_hours: int = 24
    
    # Symbols to trade
    symbols: list[str] = [
        "BTCUSDC",
        "ETHUSDC",
        "BNBUSDC",
        "ADAUSDC",
        "XRPUSDC",
        "DOGEUSDC",
        "SOLUSDC",
        "PEPEUSDC",
        "SHIBUSDC",
        "XLMUSDC",
        "LINKUSDC",
        "IOTAUSDC",
    ]
    
    # Timeframes to test
    timeframes: list[str] = ["1m", "5m", "15m", "30m", "1h", "4h"]
    
    # Binance API settings
    api_base_url: str = "https://api.binance.com"
    klines_limit: int = 1000
    rate_limit_delay: float = 0.1
    
    class Config:
        """Pydantic config."""
        
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()