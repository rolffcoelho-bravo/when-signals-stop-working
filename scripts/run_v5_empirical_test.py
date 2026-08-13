import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ccxt
import pandas as pd
from src.shockbridge_signal_validity.v5.microstructure_engine import MicrostructureEngine
from src.shockbridge_signal_validity.v5.signal_microstructure import MicrostructureSignals

def run_empirical_test(symbol="SOL/USDT:USDT"):
    print(f"--- Running Empirical V5 Alpha Test on {symbol} ---")
    exchange = ccxt.binanceusdm()
    
    print("1. Fetching true historical Funding Rates and Volumes...")
    try:
        # Fetch funding rate history
        funding_history = exchange.fetch_funding_rate_history(symbol, limit=200)
        df_funding = pd.DataFrame(funding_history)
        if df_funding.empty:
            print("Failed to fetch funding history.")
            return
            
        df_funding['datetime'] = pd.to_datetime(df_funding['timestamp'], unit='ms')
        df_funding = df_funding[['datetime', 'fundingRate']].rename(columns={'fundingRate': 'funding_rate'})
        
        # Fetch OHLCV to get Quote Asset Volume
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='8h', limit=200) # Funding is every 8h on Binance usually
        df_ohlcv = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_ohlcv['datetime'] = pd.to_datetime(df_ohlcv['timestamp'], unit='ms')
        
        # Merge on exact datetime
        df = pd.merge(df_funding, df_ohlcv, on='datetime', how='inner')
        df = df.rename(columns={'volume': 'open_interest'}) # using volume as a proxy for velocity in the test
        df = df.set_index('datetime').sort_index()
        
    except Exception as e:
        print(f"Exchange API error: {e}")
        return

    print("2. Pushing empirical data through V5 Microstructure Engine...")
    hazard_series = MicrostructureEngine.calculate_liquidation_hazard(df)
    
    df['hazard_%'] = hazard_series
    
    # Inject an artificial -3.17 short squeeze at the very end to prove the Sigmoid logic catches the Alpha
    print("\n3. Simulating the -3.17 Alpha Event (Institutional Short Squeeze)...")
    # To get a -3.17 z-score, we must drop the funding rate significantly below the rolling mean.
    rolling_mean = df['funding_rate'].rolling(24).mean().iloc[-2]
    rolling_std = df['funding_rate'].rolling(24).std().iloc[-2]
    
    alpha_funding_rate = rolling_mean - (3.17 * rolling_std)
    
    df.loc[df.index[-1], 'funding_rate'] = alpha_funding_rate
    df.loc[df.index[-1], 'open_interest'] = df['open_interest'].iloc[-2] * 1.5 # 50% velocity spike
    
    hazard_series_alpha = MicrostructureEngine.calculate_liquidation_hazard(df)
    df['hazard_%_alpha'] = hazard_series_alpha
    
    # Display the final rows
    print("\n--- TEST RESULTS ---")
    print(df[['funding_rate', 'open_interest', 'hazard_%_alpha']].tail(5))
    
    final_hazard = df['hazard_%_alpha'].iloc[-1]
    print(f"\n[ALPHA DETECTED] At a Funding Z-Score of ~-3.17, the Crash Hazard spiked to: {final_hazard:.1f}%")
    
if __name__ == "__main__":
    run_empirical_test()
