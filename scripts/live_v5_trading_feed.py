import ccxt
import time
import pandas as pd
from datetime import datetime

def live_v5_orderbook_liquidation_feed(symbol="SOL/USDT"):
    """
    V5 Live Trading Feed (Forward Testing Only)
    
    This script continuously polls the exchange for:
    1. Order Book Imbalance (L2 Depth)
    2. Funding Rates (Live)
    
    Historical L2 and Liquidation data is not free, so this script is used 
    to feed the V5 Microstructure engine in real-time.
    """
    exchange = ccxt.binanceusdm({
        'enableRateLimit': True,
    })
    
    print(f"=== INITIALIZING V5 LIVE MICROSTRUCTURE FEED FOR {symbol} ===")
    print("Warning: This is for Forward Testing on Live Markets.\n")
    
    try:
        while True:
            # 1. Fetch Order Book (Level 2)
            ob = exchange.fetch_order_book(symbol, limit=50)
            bids = pd.DataFrame(ob['bids'], columns=['price', 'size'])
            asks = pd.DataFrame(ob['asks'], columns=['price', 'size'])
            
            total_bid_size = bids['size'].sum()
            total_ask_size = asks['size'].sum()
            
            # Imbalance < 1 means sellers dominate (crash hazard)
            # Imbalance > 1 means buyers dominate
            ob_imbalance = total_bid_size / total_ask_size if total_ask_size > 0 else 1.0
            
            # 2. Fetch Live Funding Rate
            funding = exchange.fetch_funding_rate(symbol)
            current_funding = funding['fundingRate']
            
            # 3. Print the Live V5 State
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"[{now}] {symbol}")
            print(f"  Live Funding Rate : {current_funding:.6f}")
            print(f"  L2 Bid/Ask Ratio  : {ob_imbalance:.2f} (Bids: {total_bid_size:.1f}, Asks: {total_ask_size:.1f})")
            
            if ob_imbalance < 0.5 and current_funding < -0.001:
                print("  >> [!V5 ALERT!] EXTREME LIQUIDITY VOID & NEGATIVE FUNDING. CRASH IMMINENT.")
            
            print("-" * 60)
            
            # Sleep 10 seconds before next poll
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nV5 Live Feed Terminated by User.")
    except Exception as e:
        print(f"Live Feed Error: {e}")

if __name__ == "__main__":
    live_v5_orderbook_liquidation_feed("SOL/USDT:USDT")
