import os
import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AlternativeDataAdapter:
    """
    v5 Data Adapter: Ingests alternative data (Funding Rates, Open Interest)
    for crypto microstructure analysis and High-Frequency Contagion.
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
        Merges traditional OHLCV data with the new v5 Microstructure data.
        Applies Cross-Asset Contagion if the symbol is an altcoin.
        """
        price_file = os.path.join(self.raw_dir, f"{symbol.lower()}_usdt_15m.csv")
        price_df = pd.read_csv(price_file, parse_dates=["Date"])
        
        micro_df = self.fetch_binance_funding_rates(symbol)
        # Merge on Date (strip timezones to prevent merge errors)
        price_df['Date'] = price_df['Date'].dt.tz_localize(None)
        micro_df['Date'] = micro_df['Date'].dt.tz_localize(None)
        
        merged = pd.merge(price_df, micro_df, on="Date", how="inner")
        
        # --- V5 Cross-Asset Contagion ---
        if symbol.upper() != "BTC":
            logger.info(f"Injecting BTC Contagion Matrix into {symbol}...")
            btc_price = pd.read_csv(os.path.join(self.raw_dir, "btc_usdt_15m.csv"), parse_dates=["Date"])
            btc_micro = self.fetch_binance_funding_rates("BTC")
            btc_price['Date'] = btc_price['Date'].dt.tz_localize(None)
            btc_micro['Date'] = btc_micro['Date'].dt.tz_localize(None)
            btc_merged = pd.merge(btc_price, btc_micro, on="Date", how="inner")
            
            # Compute BTC features
            rolling_mean = btc_merged['funding_rate'].rolling(window=12, min_periods=1).mean()
            rolling_std = btc_merged['funding_rate'].rolling(window=12, min_periods=1).std().replace(0, 1e-9)
            btc_merged['btc_funding_z'] = (btc_merged['funding_rate'] - rolling_mean) / rolling_std
            
            vol_col = 'Quote_Asset_Volume' if 'Quote_Asset_Volume' in btc_merged.columns else 'Volume'
            vol_shifted = btc_merged[vol_col].shift(6).replace(0, 1e-9)
            btc_merged['btc_vol_vel'] = (btc_merged[vol_col] - vol_shifted) / vol_shifted
            
            # Merge BTC contagion features into altcoin
            btc_features = btc_merged[['Date', 'btc_funding_z', 'btc_vol_vel']]
            merged = pd.merge(merged, btc_features, on="Date", how="left")
            merged['btc_funding_z'] = merged['btc_funding_z'].fillna(0)
            merged['btc_vol_vel'] = merged['btc_vol_vel'].fillna(0)
        
        out_path = os.path.join(self.processed_dir, f"{symbol.lower()}_v5_master.csv")
        os.makedirs(self.processed_dir, exist_ok=True)
        merged.to_csv(out_path, index=False)
        return merged
