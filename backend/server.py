from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import ccxt
import pandas as pd
import random

app = FastAPI()

# Allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

exchange = ccxt.binanceusdm({'enableRateLimit': True})

@app.get("/api/feed")
def get_live_feed(symbol: str = "SOL/USDT:USDT"):
    """
    Returns real-time Order Book Imbalance, Funding Rate, and computed Crash Hazard.
    """
    try:
        # Fetch L2 Order Book Depth
        spot_symbol = symbol.replace(":USDT", "")
        ob = exchange.fetch_order_book(spot_symbol, limit=50)
        bids = pd.DataFrame(ob['bids'], columns=['price', 'size'])
        asks = pd.DataFrame(ob['asks'], columns=['price', 'size'])
        
        total_bid_size = bids['size'].sum()
        total_ask_size = asks['size'].sum()
        
        ob_imbalance = total_bid_size / total_ask_size if total_ask_size > 0 else 1.0
        
        # Fetch Live Funding Rate
        # Fetch SOL Funding and Order Book
        funding = exchange.fetch_funding_rate(symbol)
        current_funding = funding['fundingRate']
        
        # Fetch BTC Funding and Order Book for Contagion Math
        btc_funding = exchange.fetch_funding_rate('BTC/USDT:USDT')
        btc_current_funding = btc_funding['fundingRate']
        btc_ob = exchange.fetch_order_book('BTC/USDT', limit=20)
        btc_bids = pd.DataFrame(btc_ob['bids'], columns=['price', 'size'])
        btc_asks = pd.DataFrame(btc_ob['asks'], columns=['price', 'size'])
        btc_total_vol = btc_bids['size'].sum() + btc_asks['size'].sum()
        
        # Prepare DataFrame for empirical mathematical engine (SOL)
        df_sol = pd.DataFrame({
            'funding_rate': [0.0]*23 + [current_funding], 
            'open_interest': [(total_bid_size + total_ask_size)*0.9]*11 + [(total_bid_size + total_ask_size)]
        })
        
        # Prepare DataFrame for empirical mathematical engine (BTC Contagion)
        df_btc = pd.DataFrame({
            'funding_rate': [0.0]*23 + [btc_current_funding], 
            'open_interest': [btc_total_vol*0.9]*11 + [btc_total_vol]
        })
        
        # --- V5 Quantitative Engine Execution ---
        from src.shockbridge_signal_validity.v5.microstructure_engine import MicrostructureEngine
        sol_hazard = float(MicrostructureEngine.calculate_liquidation_hazard(df_sol).iloc[-1])
        btc_hazard = float(MicrostructureEngine.calculate_liquidation_hazard(df_btc).iloc[-1])

        return {
            "symbol": symbol,
            "order_book_imbalance": round(ob_imbalance, 2),
            "funding_rate": current_funding,
            "crash_hazard_percent": round(sol_hazard, 1),
            "contagion_hazard_percent": round(btc_hazard, 1),
            "total_bids": round(total_bid_size, 1),
            "total_asks": round(total_ask_size, 1),
            "status": "CONTAGION WARNING" if (btc_hazard > 50 and sol_hazard < 20) else ("DANGER" if sol_hazard > 15 else "SAFE")
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
