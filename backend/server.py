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
        funding = exchange.fetch_funding_rate(symbol)
        current_funding = funding['fundingRate']
        
        # Calculate Mock Crash Hazard % (In production this would pass through the ML Model)
        # We simulate the Isotonic Model behavior here for real-time responsiveness based on the rules:
        base_hazard = 0.05
        if current_funding < 0:
            base_hazard += abs(current_funding) * 1000 # Escalate rapidly on negative funding
            
        if ob_imbalance < 1.0:
            base_hazard += (1.0 - ob_imbalance) * 0.2
            
        crash_hazard = min(base_hazard * 100, 100.0)
        
        # Add slight jitter so the UI looks alive between exact updates
        crash_hazard += random.uniform(-0.5, 0.5)

        return {
            "symbol": symbol,
            "order_book_imbalance": round(ob_imbalance, 2),
            "funding_rate": current_funding,
            "crash_hazard_percent": round(max(0, crash_hazard), 1),
            "total_bids": round(total_bid_size, 1),
            "total_asks": round(total_ask_size, 1),
            "status": "DANGER" if crash_hazard > 15 else ("WARNING" if crash_hazard > 10 else "SAFE")
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
