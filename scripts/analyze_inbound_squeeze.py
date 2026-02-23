import pandas as pd
import sys

def analyze_squeeze(file_path):
    try:
        df = pd.read_csv(file_path)
        
        # High ADX (> 20) often means a strong trend is already in place
        # Low Squeeze Ratio suggests the 'coiling' is tighter or closer to firing
        
        # Sort by Squeeze Ratio ascending (tighter coiling)
        df_sorted = df.sort_values(by='Squeeze Ratio', ascending=True)
        
        print("# Squeeze Alpha Report\n")
        print("## Top Tighter Coils (Low Squeeze Ratio)")
        print(df_sorted.head(5)[['Symbol', 'Price', 'Squeeze Ratio', 'ADX']].to_string(index=False))
        
        print("\n## High ADX Momentum (Trend Strength)")
        df_adx = df[df['ADX'] > 20].sort_values(by='ADX', ascending=False)
        print(df_adx.head(5)[['Symbol', 'Price', 'Squeeze Ratio', 'ADX']].to_string(index=False))
        
        print("\n## Big Cap Squeezes (Market Cap > 50B)")
        df_big = df[df['Market Cap'] > 50000000000].sort_values(by='Squeeze Ratio')
        print(df_big[['Symbol', 'Price', 'Squeeze Ratio', 'ADX']].to_string(index=False))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_squeeze('scans/michael_inbound_squeeze.csv')
