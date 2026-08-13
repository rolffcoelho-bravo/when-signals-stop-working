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
        filepath = os.path.join(self.raw_dir, f"{symbol.lower()}_microstructure_1m.csv")
        
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
        price_file = os.path.join(self.raw_dir, f"{symbol.lower()}_usdt_1m.csv")
        price_df = pd.read_csv(price_file, parse_dates=["Date"])
        
        micro_df = self.fetch_binance_funding_rates(symbol)
        # Merge on Date (strip timezones to prevent merge errors)
        price_df['Date'] = price_df['Date'].dt.tz_localize(None)
        micro_df['Date'] = micro_df['Date'].dt.tz_localize(None)
        
        # Use a LEFT merge and forward fill the funding rates
        merged = pd.merge(price_df, micro_df, on="Date", how="left").ffill()
        
        # --- V5 Cross-Asset Contagion ---
        if symbol.upper() != "BTC":
            logger.info(f"Injecting BTC Contagion Matrix into {symbol}...")
            btc_price = pd.read_csv(os.path.join(self.raw_dir, "btc_usdt_1m.csv"), parse_dates=["Date"])
            btc_micro = self.fetch_binance_funding_rates("BTC")
            btc_price['Date'] = btc_price['Date'].dt.tz_localize(None)
            btc_micro['Date'] = btc_micro['Date'].dt.tz_localize(None)
            
            # Use a LEFT merge and forward fill here as well
            btc_merged = pd.merge(btc_price, btc_micro, on="Date", how="left").ffill()
            
            # Compute True BTC Contagion Hazard using the V5 Engine math
            from src.shockbridge_signal_validity.v5.microstructure_engine import MicrostructureEngine
            
            # Use empirical Quote_Asset_Volume as Open Interest proxy for velocity if missing
            if 'open_interest' not in btc_merged.columns:
                btc_merged['open_interest'] = btc_merged['Quote_Asset_Volume'] if 'Quote_Asset_Volume' in btc_merged.columns else btc_merged['Volume']
                
            btc_merged['btc_hazard_%'] = MicrostructureEngine.calculate_liquidation_hazard(btc_merged)
            
            # --- THE 45-MINUTE CONTAGION LAG ---
            # At 1-minute intervals, a 45-minute predictive lag is exactly a shift of 45.
            # This ensures we use BTC's hazard from 45 minutes ago to predict the altcoin's price right now.
            btc_merged['btc_hazard_%_lagged'] = btc_merged['btc_hazard_%'].shift(45).fillna(0)
            
            # Merge BTC contagion features into altcoin
            btc_features = btc_merged[['Date', 'btc_hazard_%', 'btc_hazard_%_lagged']]
            merged = pd.merge(merged, btc_features, on="Date", how="left").ffill()
            merged['btc_hazard_%_lagged'] = merged['btc_hazard_%_lagged'].fillna(0)
        
        out_path = os.path.join(self.processed_dir, f"{symbol.lower()}_v5_master.csv")
        os.makedirs(self.processed_dir, exist_ok=True)
        merged.to_csv(out_path, index=False)
        return merged
