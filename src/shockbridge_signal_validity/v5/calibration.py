import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import pandas as pd
import numpy as np
import joblib
from sklearn.isotonic import IsotonicRegression
from src.shockbridge_signal_validity.v5.alternative_data_adapter import AlternativeDataAdapter
from src.shockbridge_signal_validity.v5.microstructure_engine import MicrostructureEngine

class V5Calibrator:
    """
    Calibrates the raw V5 Microstructure mathematical features into true empirical probabilities 
    using Non-Parametric Isotonic Regression to strictly optimize LogLoss.
    """
    def __init__(self, model_path="data/models/isotonic_calibrator.joblib"):
        self.model_path = model_path
        self.calibrator = None
        
        # Create model directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
    def train(self, target_symbol="BTC"):
        """
        Trains the Isotonic Regression model on historical data.
        Target (y): A forward 4-period price crash > 3%.
        Features (X): Absolute Funding Z-Score * Volume Velocity multiplier.
        """
        print(f"Training Isotonic Calibrator on {target_symbol} historical data...")
        adapter = AlternativeDataAdapter(data_dir="data")
        try:
            # We fetch price data and merge to get future returns
            df = adapter.merge_with_price_data(target_symbol)
            # 'close' column is the price
            price_col = 'Close' if 'Close' in df.columns else 'close'
            
            # Forward 4-period return
            df['future_return'] = df[price_col].shift(-4) / df[price_col] - 1.0
            
            # Define Crash Event (y): Drop > 3%
            df['crash_event'] = np.where(df['future_return'] <= -0.03, 1, 0)
            
            # Compute Raw Features (X)
            funding_z = MicrostructureEngine.calculate_funding_premium(df, window=24)
            oi_vel = MicrostructureEngine.calculate_oi_velocity(df, window=12)
            
            abs_z = np.abs(funding_z)
            vel_multiplier = np.clip(1.0 + (oi_vel * 2.0), 1.0, 2.5)
            
            # The raw combined feature (Monotonically increasing with risk)
            df['raw_hazard_feature'] = abs_z * vel_multiplier
            
            df = df.dropna(subset=['raw_hazard_feature', 'crash_event'])
            
            if df.empty or len(df) < 50:
                print("Insufficient data to train Isotonic Calibrator.")
                return False
                
            X = df['raw_hazard_feature'].values
            y = df['crash_event'].values
            
            self.calibrator = IsotonicRegression(out_of_bounds='clip')
            self.calibrator.fit(X, y)
            
            joblib.dump(self.calibrator, self.model_path)
            print(f"Isotonic Calibrator trained and saved to {self.model_path}")
            
            # Show a sample of the calibration mapping
            sample_X = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0])
            sample_y = self.calibrator.predict(sample_X)
            print("Calibration Map (Raw Feature -> Calibrated Probability):")
            for sx, sy in zip(sample_X, sample_y):
                print(f"  Feature {sx:.1f} -> {sy*100:.2f}% Probability")
                
            return True
            
        except Exception as e:
            print(f"Calibration training failed: {e}")
            return False
            
    def load(self):
        """Loads the pre-trained calibrator."""
        if os.path.exists(self.model_path):
            self.calibrator = joblib.load(self.model_path)
            return True
        return False
        
    def predict_proba(self, raw_features: np.ndarray) -> np.ndarray:
        """Transforms raw features into strict LogLoss-optimized probabilities."""
        if self.calibrator is None:
            if not self.load():
                # Fallback to a very flat dummy output if model missing
                return np.clip(raw_features * 0.01, 0, 1.0) 
        return self.calibrator.predict(raw_features)

if __name__ == "__main__":
    calibrator = V5Calibrator()
    calibrator.train("BTC")
