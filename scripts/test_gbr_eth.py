import sys
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.shockbridge_signal_validity.v5.alternative_data_adapter import AlternativeDataAdapter
from src.shockbridge_signal_validity.v5.microstructure_engine import MicrostructureEngine

def run_gbr_test():
    print("Loading empirical data...")
    adapter = AlternativeDataAdapter(data_dir="data")
    df = adapter.merge_with_price_data('ETH')

    if 'hazard_%' not in df.columns:
        df['open_interest'] = df['Quote_Asset_Volume'] if 'Quote_Asset_Volume' in df.columns else df['Volume']
        df['hazard_%'] = MicrostructureEngine.calculate_liquidation_hazard(df)

    df = df.dropna(subset=['hazard_%', 'btc_hazard_%_lagged']).copy()
    
    # 1. Define the Target: Actual ROI at the 45-minute close!
    # If we train it to predict the final close, the model will naturally learn to avoid rubber-band trades!
    print("Calculating target 45-minute Close ROI...")
    df['close_after_45m'] = df['Close'].shift(-45)
    df['actual_close_roi_%'] = ((df['Close'] - df['close_after_45m']) / df['Close']) * 100.0
    
    # Features for GBR
    df['hazard_delta'] = df['btc_hazard_%_lagged'] - df['hazard_%']
    features = ['hazard_%', 'btc_hazard_%_lagged', 'hazard_delta', 'Volume', 'funding_rate']
    
    ml_df = df.dropna(subset=features + ['actual_close_roi_%']).copy()
    
    # Train/Test Split (Sequential to prevent lookahead bias)
    split_idx = int(len(ml_df) * 0.8)
    train_df = ml_df.iloc[:split_idx]
    test_df = ml_df.iloc[split_idx:]
    
    X_train = train_df[features]
    y_train = train_df['actual_close_roi_%']
    X_test = test_df[features]
    y_test = test_df['actual_close_roi_%']
    
    print("Training Gradient Boosting Regressor...")
    model = HistGradientBoostingRegressor(random_state=42, max_iter=200, min_samples_leaf=50)
    model.fit(X_train, y_train)
    
    ml_df['predicted_close_roi_%'] = model.predict(ml_df[features])
    
    # Evaluate Strategy on the Test Set
    print("\n--- Running Strategy on Test Set (Last 20% of data) ---")
    
    test_df_with_preds = ml_df.iloc[split_idx:].copy()
    
    # We only trade if the Isotonic Oracle fires AND GBR predicts the FINAL CLOSE will be > 0.30%
    trade_signals = test_df_with_preds[(test_df_with_preds['hazard_delta'] > 11.0) & (test_df_with_preds['predicted_close_roi_%'] > 0.30)].copy()
    print(f"Total Isotonic Signals in Test Set: {len(test_df_with_preds[test_df_with_preds['hazard_delta'] > 11.0])}")
    print(f"Signals surviving GBR filter (>0.30% final close profit): {len(trade_signals)}")
    
    if len(trade_signals) == 0:
        print("No trades survived the filter.")
        return
        
    # Align the trades using a walk-forward loop with a strict cooldown lock (no overlapping trades)
    trade_results = []
    in_position_until = -1
    
    for idx, row in trade_signals.iterrows():
        loc = ml_df.index.get_loc(idx)
        
        # Enforce the same cooldown lock as V5: do not enter if already in a position
        if loc <= in_position_until:
            continue
            
        pnl_pct = None
        stop_loss_price = row['Close'] * 1.01  # 1% stop loss (Shorts get stopped out if price goes UP 1%)
        
        # Walk forward minute-by-minute for a maximum of 45 minutes to check if stop loss triggers
        for step in range(1, 46):
            if loc + step >= len(ml_df):
                break
                
            future_row = ml_df.iloc[loc + step]
            
            if future_row['High'] >= stop_loss_price:
                pnl_pct = -0.01  # 1% Stop Loss Hit
                in_position_until = loc + step  # Free up capital at the exact minute the stop hit
                break
                
        # If stop loss didn't trigger, exit at the 45-minute mark
        if pnl_pct is None:
            pnl_pct = row['actual_close_roi_%'] / 100.0
            in_position_until = loc + 45
            
        trade_results.append(pnl_pct)
        
    # Calculate Institutional ROI (1x Leverage, 0.00% Fees, Compounding Capital)
    inst_capital = 10000.0
    for pnl in trade_results:
        # Full capital allocation on 1x leverage
        inst_capital += inst_capital * (pnl * 1.0)
    inst_roi = ((inst_capital - 10000.0) / 10000.0) * 100.0
    
    # Calculate Non-Institutional ROI (1x Leverage, 0.12% Total Taker Fee, Compounding Capital)
    non_inst_capital = 10000.0
    for pnl in trade_results:
        # Full capital allocation on 1x leverage, subtracting 0.12% total fee to match V5 comparison
        non_inst_capital += non_inst_capital * (pnl - 0.0012)
    non_inst_roi = ((non_inst_capital - 10000.0) / 10000.0) * 100.0
    
    print(f"\n--- Gradient Boosting Results ---")
    print(f"Total Trades Taken: {len(trade_results)}")
    print(f"Win Rate: {len([x for x in trade_results if x > 0]) / len(trade_results) * 100:.2f}%")
    print(f"Institutional ROI (1x, 0% Fee): {inst_roi:.2f}%")
    print(f"Non-Institutional ROI (1x, 0.12% Fee): {non_inst_roi:.2f}%")
    
if __name__ == "__main__":
    run_gbr_test()
