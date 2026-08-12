import os
import sys
import time
import ccxt
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
import argparse

# Add project root to sys path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shockbridge_signal_validity.data import fetch_ccxt_ohlcv

def parse_args():
    parser = argparse.ArgumentParser(description="Download 100% Empirical Data")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    # Match the V3 start date of 2021-01-01
    parser.add_argument("--start", default="2021-01-01T00:00:00Z")
    parser.add_argument("--end", default="2026-07-22T12:00:00Z")
    return parser.parse_args()

def fetch_all_funding_rates(exchange, symbol, since_ms, until_ms):
    """
    Paginates the Binance API to fetch empirical funding rates with zero synthetic data.
    """
    all_rates = []
    current_since = since_ms
    
    print(f"  Fetching empirical funding rates for {symbol}...")
    while current_since < until_ms:
        try:
            # Binance allows up to 1000 limit
            rates = exchange.fetch_funding_rate_history(symbol, since=current_since, limit=1000)
            if not rates:
                break
                
            all_rates.extend(rates)
            
            # The next 'since' is the timestamp of the last rate + 1 ms
            last_ts = rates[-1]['timestamp']
            if last_ts <= current_since:
                break # prevent infinite loop if api returns same data
            current_since = last_ts + 1
            
            # Sleep to respect rate limits
            time.sleep(0.5)
        except Exception as e:
            print(f"  API Error fetching {symbol}: {e}")
            time.sleep(2)
            
    df = pd.DataFrame(all_rates)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['Date', 'fundingRate']].rename(columns={'fundingRate': 'funding_rate'})
        df = df.sort_values('Date').drop_duplicates('Date').reset_index(drop=True)
    return df

def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Download ETH OHLCV (BTC and SOL are already in raw/)
    print("Downloading ETH empirical spot OHLCV data...")
    eth = fetch_ccxt_ohlcv(
        symbol="ETH/USDT",
        timeframe="4h",
        start=args.start,
        end=args.end,
        exchange_id="binance"
    )
    eth_path = args.output_dir / "eth_usdt_4h.csv"
    eth_out = eth.copy()
    eth_out.index.name = "Date"
    eth_out.reset_index().to_csv(eth_path, index=False)
    print(f"  Saved ETH OHLCV to {eth_path} ({len(eth)} rows)")
    
    # 2. Download Empirical Funding Rates
    b = ccxt.binanceusdm()
    start_dt = datetime.strptime(args.start, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(args.end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    
    since_ms = int(start_dt.timestamp() * 1000)
    until_ms = int(end_dt.timestamp() * 1000)
    
    assets = ["BTC", "ETH", "SOL"]
    for asset in assets:
        symbol = f"{asset}/USDT:USDT"
        df = fetch_all_funding_rates(b, symbol, since_ms, until_ms)
        
        # We must drop Open Interest as Binance only allows 30-day historical access.
        # Zero fake data means we only use exactly what we can fetch empirically.
        
        if not df.empty:
            out_path = args.output_dir / f"{asset.lower()}_microstructure.csv"
            df.to_csv(out_path, index=False)
            print(f"  Saved empirical funding rates for {asset} to {out_path} ({len(df)} rows)")
        else:
            print(f"  WARNING: No empirical funding data found for {asset}.")

if __name__ == "__main__":
    main()
