import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
import sys

def generate_contagion_heatmap():
    """
    Generates a heatmap demonstrating how Bitcoin's funding anomaly 
    bleeds into Solana's price over subsequent 15-minute intervals.
    """
    print("Generating V5 Cross-Asset Contagion Heatmap...")
    df = pd.read_csv("data/processed/sol_v5_master.csv")
    
    # Calculate Solana future returns: 15m, 30m, 45m, 60m
    df['SOL_Return_15m'] = df['Close'].pct_change(periods=-1) * -1
    df['SOL_Return_30m'] = df['Close'].pct_change(periods=-2) * -1
    df['SOL_Return_45m'] = df['Close'].pct_change(periods=-3) * -1
    df['SOL_Return_60m'] = df['Close'].pct_change(periods=-4) * -1
    
    # Focus only on severe Bitcoin Contagion events (BTC Funding Z < -2.0)
    # where institutional panic is already happening on BTC
    crash_events = df[df['btc_funding_z'] < -2.0].copy()
    
    # Select the columns to correlate
    features = ['btc_funding_z', 'SOL_Return_15m', 'SOL_Return_30m', 'SOL_Return_45m', 'SOL_Return_60m']
    corr_matrix = crash_events[features].corr()
    
    # Plotting
    plt.figure(figsize=(10, 8))
    sns.set_theme(style="darkgrid")
    
    # Create the heatmap
    ax = sns.heatmap(
        corr_matrix, 
        annot=True, 
        fmt=".2f", 
        cmap="coolwarm", 
        cbar=True,
        square=True,
        linewidths=.5,
        vmin=-1, vmax=1
    )
    
    plt.title("V5 Cross-Asset Contagion Matrix:\nBTC Funding Imbalance vs. Future SOL Returns", fontsize=14, pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # Ensure the docs directory exists
    os.makedirs("docs", exist_ok=True)
    out_path = "docs/contagion_heatmap.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Successfully saved Heatmap to {out_path}")

if __name__ == "__main__":
    generate_contagion_heatmap()
