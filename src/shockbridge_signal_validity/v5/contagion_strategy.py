import pandas as pd
import numpy as np

class ContagionStrategySimulator:
    """
    Backtests the Asymmetrical Preemptive Short strategy based on Cross-Asset Contagion.
    Rule: If target asset (SOL) is mathematically healthy (Hazard < 10%), 
          BUT the anchor asset (BTC) was in critical decay (Hazard > 80%) 45-minutes ago,
          we enter a preemptive SHORT on SOL.
    """
    
    def __init__(self, initial_capital=10000.0, leverage=1.0, min_hazard_delta=5.0, stop_loss_pct=0.05):
        self.initial_capital = initial_capital
        self.leverage = leverage
        self.min_hazard_delta = min_hazard_delta
        self.stop_loss_pct = stop_loss_pct
        self.capital = initial_capital
        self.positions = []
        
    def backtest(self, df: pd.DataFrame, target_symbol="SOL") -> dict:
        """
        Runs the contagion backtest over the merged dataframe.
        df must contain: 'close', 'hazard_%', 'btc_hazard_%_lagged'
        """
        if 'btc_hazard_%_lagged' not in df.columns:
            raise ValueError("Dataframe must contain 'btc_hazard_%_lagged' from the Contagion Engine.")
            
        in_position = False
        entry_price = 0.0
        entry_time = None
        
        # Pre-compute the 50-period trend filter (prevent shorting into aggressive bull markets)
        price_col = 'Close' if 'Close' in df.columns else 'close'
        df['sma_50'] = df[price_col].rolling(window=50, min_periods=1).mean()
        
        trades = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Dynamically handle price column capitalization
            price_col = 'Close' if 'Close' in df.columns else 'close'
            
            # --- CONTAGION TRIGGER CONDITION ---
            # 1. Minimum Hazard Delta: Only execute if the predicted severity massively outweighs the 0.12% transaction fee
            hazard_delta = row['btc_hazard_%_lagged'] - row['hazard_%']
            
            # 2. Isotonic Calibrated Thresholds: BTC Hazard > 12%, Local Hazard < 12%
            # 3. Trend Filter: Do NOT short if the asset is parabolic (Price > SMA 50)
            contagion_signal = (row['hazard_%'] < 12.0) and (row['btc_hazard_%_lagged'] > 12.0) and (row[price_col] < row['sma_50']) and (hazard_delta > self.min_hazard_delta)
            
            if not in_position and contagion_signal:
                # Enter Short
                in_position = True
                entry_price = row[price_col]
                entry_time = row['Date'] if 'Date' in df.columns else df.index[i]
                entry_index = i
                
            elif in_position:
                # Exit condition: Either SOL catches the contagion and crashes (Take Profit), 
                # or BTC recovers (Stop Loss). 
                
                # 1. Contagion Hit (Take Profit)
                tp_signal = (row['hazard_%'] > 15.0)
                
                # 2. Stop Loss (Parametric)
                current_loss = (row[price_col] - entry_price) / entry_price
                sl_signal = current_loss > self.stop_loss_pct
                
                # 3. Time Stop (4 hours = 16 periods)
                # FIX: Because data is sparse, calculating row differences (i - entry_index) fails.
                # We must calculate strict datetime deltas.
                current_time = row['Date'] if 'Date' in df.columns else df.index[i]
                
                # Convert to proper datetime if it isn't already
                if isinstance(current_time, str):
                    current_time = pd.to_datetime(current_time)
                if isinstance(entry_time, str):
                    entry_time = pd.to_datetime(entry_time)
                    
                time_stop = False
                if pd.notnull(current_time) and pd.notnull(entry_time):
                    time_elapsed = current_time - entry_time
                    time_stop = time_elapsed >= pd.Timedelta(hours=4)
                
                if tp_signal or sl_signal or time_stop: 
                    exit_price = row[price_col]
                    exit_time = current_time
                    
                    # Calculate Short PnL
                    # PnL % = (Entry - Exit) / Entry
                    pnl_pct = (entry_price - exit_price) / entry_price
                    pnl_dollar = self.capital * pnl_pct * self.leverage
                    
                    self.capital += pnl_dollar
                    
                    trades.append({
                        "entry_time": entry_time,
                        "exit_time": exit_time,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_pct": pnl_pct * 100,
                        "pnl_dollar": pnl_dollar,
                        "capital_after": self.capital
                    })
                    
                    in_position = False
                    
        # Summary Statistics
        win_rate = sum(1 for t in trades if t['pnl_pct'] > 0) / len(trades) if trades else 0.0
        total_roi = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        return {
            "initial_capital": self.initial_capital,
            "final_capital": self.capital,
            "total_roi_percent": total_roi,
            "total_trades": len(trades),
            "win_rate_percent": win_rate * 100,
            "trades": trades
        }
