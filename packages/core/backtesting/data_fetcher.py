import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import asyncio
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)

class HistoricalDataFetcher:
    """Fetch historical data from Alpaca for backtesting"""
    
    def __init__(self, api_key: str, secret_key: str):
        self.client = StockHistoricalDataClient(api_key, secret_key)
        
    def fetch_bars(
        self,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1Min"
    ) -> Dict[str, pd.DataFrame]:
        """Fetch historical bars from Alpaca"""
        
        # Map timeframe string to Alpaca TimeFrame
        timeframe_map = {
            "1Min": TimeFrame(1, TimeFrameUnit.Minute),
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "15Min": TimeFrame(15, TimeFrameUnit.Minute),
            "30Min": TimeFrame(30, TimeFrameUnit.Minute),
            "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
            "1Day": TimeFrame(1, TimeFrameUnit.Day),
        }
        
        alpaca_timeframe = timeframe_map.get(timeframe, TimeFrame(1, TimeFrameUnit.Minute))
        
        logger.info(f"Fetching {timeframe} bars for {symbols} from {start_date} to {end_date}")
        
        # Create request
        request = StockBarsRequest(
            symbol_or_symbols=symbols,
            start=start_date,
            end=end_date,
            timeframe=alpaca_timeframe,
            limit=10000  # Max bars per request
        )
        
        # Fetch data
        try:
            bars_data = self.client.get_stock_bars(request)
            
            # Convert to DataFrames
            result = {}
            for symbol in symbols:
                if symbol in bars_data:
                    df = bars_data[symbol].df
                    df.index = pd.to_datetime(df.index)
                    result[symbol] = df
                    logger.info(f"Fetched {len(df)} bars for {symbol}")
                else:
                    logger.warning(f"No data found for {symbol}")
                    result[symbol] = pd.DataFrame()
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return {}
    
    def fetch_trades(
        self,
        symbols: List[str],
        date: datetime,
        limit: int = 10000
    ) -> Dict[str, pd.DataFrame]:
        """Fetch historical trades for more accurate backtesting"""
        # Implementation for trade-level data
        pass
    
    async def fetch_fundamental_data(self, symbol: str) -> Dict:
        """Fetch fundamental data for the symbol"""
        # Could integrate with other APIs for fundamental data
        pass
    
    def save_to_parquet(self, data: Dict[str, pd.DataFrame], directory: str = "data/historical"):
        """Save historical data to Parquet files for faster loading"""
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        for symbol, df in data.items():
            if not df.empty:
                filepath = f"{directory}/{symbol}.parquet"
                df.to_parquet(filepath)
                logger.info(f"Saved {symbol} data to {filepath}")
    
    def load_from_parquet(self, symbols: List[str], directory: str = "data/historical") -> Dict[str, pd.DataFrame]:
        """Load historical data from Parquet files"""
        result = {}
        
        for symbol in symbols:
            filepath = f"{directory}/{symbol}.parquet"
            try:
                df = pd.read_parquet(filepath)
                result[symbol] = df
                logger.info(f"Loaded {symbol} data from {filepath}")
            except FileNotFoundError:
                logger.warning(f"No cached data found for {symbol}")
                result[symbol] = pd.DataFrame()
        
        return result