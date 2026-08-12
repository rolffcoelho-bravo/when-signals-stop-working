import os
import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AlternativeDataAdapter:
    """
    V4 Data Adapter: Ingests alternative data (Funding Rates, Open Interest)
    for crypto microstructure analysis.
    """
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.processed_dir = os.path.join(data_dir, "processed")
        
    def fetch_binance_funding_rates(self, symbol: str) -> pd.DataFrame:
        """
        Loads empirical historical funding rates and open interest for the asset.
        If the data is missing, it explicitly fails to guarantee no fictional data is used.
        """
        filepath = os.path.join(self.raw_dir, f"{symbol.lower()}_microstructure.csv")
        
        if os.path.exists(filepath):
            logger.info(f"Loading empirical microstructure from {filepath}")
            # Ensure timestamp is parsed properly
            df = pd.read_csv(filepath)
            # Standardize date column
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
            elif 'timestamp' in df.columns:
                df['Date'] = pd.to_datetime(df['timestamp'])
            return df
            
        raise FileNotFoundError(f"Empirical microstructure data for {symbol} not found at {filepath}. Run download_empirical_microstructure.py first. ARTIFICIAL DATA IS STRICTLY PROHIBITED.")

    def merge_with_price_data(self, symbol: str) -> pd.DataFrame:
        """
        Merges traditional OHLCV data with the new V4 Microstructure data.
        """
        price_file = os.path.join(self.raw_dir, f"{symbol.lower()}_usdt_4h.csv")
        price_df = pd.read_csv(price_file, parse_dates=["Date"])
        
        micro_df = self.fetch_binance_funding_rates(symbol)
        # Merge on Date (strip timezones to prevent merge errors)
        price_df['Date'] = price_df['Date'].dt.tz_localize(None)
        micro_df['Date'] = micro_df['Date'].dt.tz_localize(None)
        
        merged = pd.merge(price_df, micro_df, on="Date", how="inner")
        
        out_path = os.path.join(self.processed_dir, f"{symbol.lower()}_v4_master.csv")
        os.makedirs(self.processed_dir, exist_ok=True)
        merged.to_csv(out_path, index=False)
        return merged
