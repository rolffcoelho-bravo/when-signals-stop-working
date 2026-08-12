import pandas as pd
from typing import Dict, Any

# We assume a Base Signal class exists in the architecture.
# In V3 it's likely in src.shockbridge_signal_validity.v3.signal_math or similar.
# For V4, we'll implement this independently.

from src.shockbridge_signal_validity.v4.microstructure_engine import MicrostructureEngine

class MicrostructureSignals:
    """
    A signal generator that outputs a DataFrame of microstructure features
    compatible with the existing feature matrix.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
    def generate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates all Microstructure signals and appends them to a feature DataFrame.
        """
        features = pd.DataFrame(index=data.index)
        
        # 1. Funding Premium
        features['micro_funding_z'] = MicrostructureEngine.calculate_funding_premium(data, window=12)
        
        # 2. OI Velocity
        features['micro_oi_vel'] = MicrostructureEngine.calculate_oi_velocity(data, window=6)
        
        # 3. Liquidation Hazard
        features['micro_liq_hazard'] = MicrostructureEngine.calculate_liquidation_hazard(data)
        
        return features
