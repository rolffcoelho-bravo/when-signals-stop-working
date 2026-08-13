import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.shockbridge_signal_validity.v5.alternative_data_adapter import AlternativeDataAdapter
from src.shockbridge_signal_validity.v5.contagion_strategy import ContagionStrategySimulator

def run():
    print("--- V5 Cross-Asset Contagion Strategy Backtest ---")
    print("Goal: Prove asymmetrical edge of preemptive shorts on SOL via BTC 45m Lag.\n")
    
    adapter = AlternativeDataAdapter(data_dir="data")
    
    print("1. Ingesting empirical 1m OHLCV and Microstructure data...")
    print("2. Computing Absolute Hazards & applying 45-minute lag shift...")
    
    targets = ["ETH", "SOL", "BNB", "AVAX"]
    
    for target in targets:
        print(f"\n\n==================================================")
        print(f"--- Testing Contagion on {target} ---")
        print(f"==================================================")
        try:
            # This triggers the merge and mathematically computes btc_hazard_%_lagged
            df = adapter.merge_with_price_data(target)
        except Exception as e:
            print(f"Error processing data for {target}: {e}")
            continue
            
        print(f"Dataset compiled: {len(df)} empirical intervals.")
        
        # We now have the `merged` dataframe which contains:
        # 'close', 'hazard_%' (target's hazard), and 'btc_hazard_%_lagged'
        
        # Compute target's hazard if it wasn't in the adapter yet
        if 'hazard_%' not in df.columns:
            from src.shockbridge_signal_validity.v5.microstructure_engine import MicrostructureEngine
            df['open_interest'] = df['Quote_Asset_Volume'] if 'Quote_Asset_Volume' in df.columns else df['Volume']
            df['hazard_%'] = MicrostructureEngine.calculate_liquidation_hazard(df)
            
        # Drop rows with NaN due to rolling windows
        df = df.dropna(subset=['hazard_%', 'btc_hazard_%_lagged'])
        
        print(f"\n3. Executing Institutional Contagion Simulator for {target} (10x Leverage, 1% Stop Loss)...")
        simulator = ContagionStrategySimulator(initial_capital=10000.0, leverage=10.0, min_hazard_delta=11.0, stop_loss_pct=0.01)
        
        results = simulator.backtest(df, target_symbol=target)
        
        print("\n--- RESULTS ---")
        print(f"Total Trades Taken: {results['total_trades']}")
        print(f"Win Rate: {results['win_rate_percent']:.2f}%")
        print(f"Starting Capital: ${results['initial_capital']:,.2f}")
        print(f"Ending Capital:   ${results['final_capital']:,.2f}")
        print(f"Total ROI:        {results['total_roi_percent']:.2f}%\n")
        
        if results['trades']:
            print("Sample of Best Trades (Preemptive Shorts):")
            sorted_trades = sorted(results['trades'], key=lambda x: x['pnl_pct'], reverse=True)
            for t in sorted_trades[:3]:
                print(f"  Entry: {t['entry_time']} @ ${t['entry_price']:.2f}")
                print(f"  Exit:  {t['exit_time']} @ ${t['exit_price']:.2f} | PnL: +{t['pnl_pct']:.2f}%")

if __name__ == "__main__":
    run()
