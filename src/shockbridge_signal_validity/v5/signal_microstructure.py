import pandas as pd
import numpy as np
from typing import Dict, Any

# We assume a Base Signal class exists in the architecture.
# In V3 it's likely in src.shockbridge_signal_validity.v3.signal_math or similar.
# For v5, we'll implement this independently.

from src.shockbridge_signal_validity.v5.microstructure_engine import MicrostructureEngine

class MicrostructureSignals:
    """
    A signal generator that outputs a DataFrame of microstructure features
    compatible with the existing feature matrix.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.window = self.config.get('window', 12)
        self.velocity_period = self.config.get('velocity_period', 6)
        
    def generate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates all Microstructure signals and appends them to a feature DataFrame.
        """
        features = pd.DataFrame(index=data.index)
        df = data

        if 'funding_rate' not in df.columns:
            raise KeyError("Empirical 'funding_rate' column missing. Must merge with empirical alternative data first.")
            
        # 1. Funding Premium Z-Score (Z_F)
        rolling_mean = df['funding_rate'].rolling(window=self.window, min_periods=1).mean()
        rolling_std = df['funding_rate'].rolling(window=self.window, min_periods=1).std().replace(0, 1e-9)
        features['micro_funding_z'] = (df['funding_rate'] - rolling_mean) / rolling_std
        
        # 2. Empirical Institutional Volume Velocity (V_Vol)
        # Using empirical Quote_Asset_Volume as a strict replacement for fake Open Interest
        if 'Quote_Asset_Volume' in df.columns:
            vol_shifted = df['Quote_Asset_Volume'].shift(self.velocity_period).replace(0, 1e-9)
            features['micro_vol_vel'] = (df['Quote_Asset_Volume'] - vol_shifted) / vol_shifted
        elif 'Volume' in df.columns:
            vol_shifted = df['Volume'].shift(self.velocity_period).replace(0, 1e-9)
            features['micro_vol_vel'] = (df['Volume'] - vol_shifted) / vol_shifted
        else:
            features['micro_vol_vel'] = 0
            
        # 3. Liquidation Hazard Flag
        # Hazard is high when Volume spikes heavily alongside extreme absolute funding skew
        abs_z = np.abs(features['micro_funding_z'])
        k = 2.5
        z_prob = 1 / (1 + np.exp(-k * (abs_z - 1.5)))
        vel_multiplier = np.clip(1.0 + (features['micro_vol_vel'] * 2.0), 1.0, 2.5)
        
        features['micro_liq_hazard'] = np.clip(z_prob * vel_multiplier * 100, 0.0, 100.0)
        
        # Forward-fill any NaNs to prevent statistical bias from zeroes
        features.ffill(inplace=True)
        return features
