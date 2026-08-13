import pandas as pd
import numpy as np

class MicrostructureEngine:
    """
    Computes mathematical signals from raw Microstructure Alternative Data
    (Funding Rates, Open Interest).
    """
    
    @staticmethod
    def calculate_funding_premium(df: pd.DataFrame, window: int = 12) -> pd.Series:
        """
        Calculates the Z-Score of the funding rate to detect extreme 
        over-leverage in either the Long or Short direction.
        Positive spike = Longs are over-leveraged (bearish signal).
        Negative spike = Shorts are heavily shorting (bullish signal).
        """
        if 'funding_rate' not in df.columns:
            return pd.Series(0, index=df.index)
            
        rolling_mean = df['funding_rate'].rolling(window=window, min_periods=1).mean()
        rolling_std = df['funding_rate'].rolling(window=window, min_periods=1).std().replace(0, 1e-8)
        
        z_score = (df['funding_rate'] - rolling_mean) / rolling_std
        return z_score.fillna(0)
        
    @staticmethod
    def calculate_oi_velocity(df: pd.DataFrame, window: int = 6) -> pd.Series:
        """
        Measures how fast money is entering or leaving the derivatives market.
        Rapid increase + Price increase = Euphoria (danger).
        Rapid decrease = Liquidation cascade in progress.
        """
        if 'open_interest' not in df.columns:
            return pd.Series(0, index=df.index)
            
        # Percentage change over the window
        oi_pct = df['open_interest'].pct_change(periods=window)
        return oi_pct.fillna(0)
        
    @staticmethod
    def calculate_liquidation_hazard(df: pd.DataFrame) -> pd.Series:
        """
        A composite feature: If funding is extremely high AND OI is building rapidly,
        the hazard of a downward liquidation cascade is critically high.
        """
        if 'funding_rate' not in df.columns or 'open_interest' not in df.columns:
            return pd.Series(0, index=df.index)
            
        funding_z = MicrostructureEngine.calculate_funding_premium(df, window=24)
        oi_vel = MicrostructureEngine.calculate_oi_velocity(df, window=12)
        
        # Hazard should scale with        # Compute raw multiplier feature
        abs_z = np.abs(funding_z)
        vel_multiplier = np.clip(1.0 + (oi_vel * 2.0), 1.0, 2.5)
        raw_hazard_feature = abs_z * vel_multiplier
        
        # Rigorous LogLoss Calibration via Non-Parametric Isotonic Regression
        from src.shockbridge_signal_validity.v5.calibration import V5Calibrator
        calibrator = V5Calibrator()
        
        # Predict True Empirical Probabilities (returns bounded 0-1)
        calibrated_probs = calibrator.predict_proba(raw_hazard_feature.fillna(0).values)
        
        # Convert back to Series and multiply by 100 for percentage visualization
        return pd.Series(calibrated_probs * 100.0, index=df.index)
