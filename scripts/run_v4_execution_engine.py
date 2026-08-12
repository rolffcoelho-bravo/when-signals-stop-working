import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import log_loss, brier_score_loss

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.shockbridge_signal_validity.v4.alternative_data_adapter import AlternativeDataAdapter
from src.shockbridge_signal_validity.v4.signal_microstructure import MicrostructureSignals

def generate_target(df: pd.DataFrame, threshold: float = -0.03) -> pd.Series:
    """
    Defines the Panic Regime target: A crash of more than 3% in the next candle.
    """
    future_return = df['Close'].pct_change().shift(-1)
    return (future_return < threshold).astype(int)

def run_v4_pipeline(symbols=["SOL", "BTC", "ETH"]):
    print("--- SHOCKBRIDGE V4 EMPIRICAL EXECUTION ENGINE ---")
    
    results = []
    all_preds_string = ""
    
    for symbol in symbols:
        print(f"\nEvaluating Empirical Microstructure for {symbol}...")
        adapter = AlternativeDataAdapter()
        
        try:
            df = adapter.merge_with_price_data(symbol)
        except Exception as e:
            print(f"Skipping {symbol}: {e}")
            continue
            
        signals = MicrostructureSignals()
        features = signals.generate(df)
        
        target = generate_target(df, threshold=-0.03)
        dataset = pd.concat([features, target.rename('target')], axis=1).dropna()
        
        X = dataset.drop(columns=['target'])
        y = dataset['target']
        
        positive_class_ratio = y.mean()
        if positive_class_ratio == 0:
            print(f"Skipping {symbol}: No tail-risk events found.")
            continue
            
        print(f"Base Target Incidence: {positive_class_ratio:.4f} | Samples: {len(X)}")
        
        tscv = TimeSeriesSplit(n_splits=5, gap=1)
        out_of_sample_preds = []
        out_of_sample_trues = []
        
        for train_index, test_index in tscv.split(X):
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
            
            gbc = GradientBoostingClassifier(n_estimators=100, learning_rate=0.05, max_depth=3, random_state=42)
            calibrator = CalibratedClassifierCV(estimator=gbc, method='isotonic', cv=3)
            calibrator.fit(X_train, y_train)
            
            preds = calibrator.predict_proba(X_test)[:, 1]
            out_of_sample_preds.extend(preds)
            out_of_sample_trues.extend(y_test)
            
        y_true = np.array(out_of_sample_trues)
        y_pred = np.array(out_of_sample_preds)
        
        v4_log_loss = log_loss(y_true, y_pred)
        v4_brier = brier_score_loss(y_true, y_pred)
        
        random_preds = np.full_like(y_pred, positive_class_ratio)
        baseline_log_loss = log_loss(y_true, random_preds)
        baseline_brier = brier_score_loss(y_true, random_preds)
        
        results.append({
            "Asset": symbol,
            "Samples": len(y_pred),
            "Incidence": positive_class_ratio,
            "V4_Log_Loss": v4_log_loss,
            "Base_Log_Loss": baseline_log_loss,
            "V4_Brier": v4_brier,
            "Base_Brier": baseline_brier
        })
        
        all_preds_string += ",".join([f"{p:.6f}" for p in y_pred])
        
    print("\n5. Aggregating Multi-Asset Cryptographic Proof...")
    audit_hash = hashlib.sha256(all_preds_string.encode('utf-8')).hexdigest()
    
    audit_data = {
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "cryptographic_prediction_hash_sha256": audit_hash,
        "assets_evaluated": [r['Asset'] for r in results],
        "metrics": results
    }
    
    os.makedirs(os.path.join("outputs", "v4"), exist_ok=True)
    audit_file = os.path.join("outputs", "v4", "V4_EMPIRICAL_AUDIT.json")
    with open(audit_file, "w") as f:
        json.dump(audit_data, f, indent=4)
        
    print("\n--- MULTI-ASSET RESULTS TABLE ---")
    print(f"{'Asset':<10} | {'V4 Result (LogLoss)':<20} | {'Random Baseline':<20} | {'V3 Baseline (Failed)'}")
    print("-" * 80)
    for r in results:
        print(f"{r['Asset']:<10} | {r['V4_Log_Loss']:<20.4f} | {r['Base_Log_Loss']:<20.4f} | 0.7006")
    print("-" * 80)
    print(f"Audit Saved: {audit_file}")
    print(f"Cryptographic Hash: {audit_hash}")
    
if __name__ == "__main__":
    run_v4_pipeline()
