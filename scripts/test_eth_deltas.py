import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.shockbridge_signal_validity.v5.alternative_data_adapter import AlternativeDataAdapter
from src.shockbridge_signal_validity.v5.contagion_strategy import ContagionStrategySimulator

adapter = AlternativeDataAdapter(data_dir="data")
df = adapter.merge_with_price_data('ETH')

if 'hazard_%' not in df.columns:
    from src.shockbridge_signal_validity.v5.microstructure_engine import MicrostructureEngine
    df['open_interest'] = df['Quote_Asset_Volume'] if 'Quote_Asset_Volume' in df.columns else df['Volume']
    df['hazard_%'] = MicrostructureEngine.calculate_liquidation_hazard(df)

df = df.dropna(subset=['hazard_%', 'btc_hazard_%_lagged'])

# Ensure we test with 1x leverage and standard 5.0% stop loss
print("Testing ETH with 1x Leverage, 5.0% Stop Loss...")
for delta in [11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0]:
    simulator = ContagionStrategySimulator(initial_capital=10000.0, leverage=1.0, min_hazard_delta=delta, stop_loss_pct=0.05)
    res = simulator.backtest(df, target_symbol='ETH')
    print(f"Delta: {delta}% | Trades: {res['total_trades']} | Win Rate: {res['win_rate_percent']:.2f}% | ROI: {res['total_roi_percent']:.2f}%")
