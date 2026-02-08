"""
🏈 ALPHA SCOUT: THE OFFENSIVE PLAY CARD FOR TRADERS
Part of the Alpha-Playbooks Series by @mphinance

This is a beginner-friendly script designed to show you how to pull 
real-time market data, calculate basic technicals, and aggregate news.

Requirements:
pip install yfinance pandas
"""

import yfinance as yf
import pandas as pd
import datetime

def run_scout(ticker="UAMY"):
    print(f"--- 🏈 SCOUTING REPORT: {ticker} ---")
    
    # 1. Fetch Price Data
    # We pull 1 year of daily data to calculate moving averages
    stock = yf.Ticker(ticker)
    df = stock.history(period="1y")
    
    if df.empty:
        print(f"Error: Could not find data for {ticker}")
        return

    # Flatten columns if MultiIndex (common in newer yfinance versions)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. The Technical Stack (The Formation)
    latest_price = df['Close'].iloc[-1]
    sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
    sma_200 = df['Close'].rolling(window=200).mean().iloc[-1]
    
    # 3. The Scout Report (Trend Analysis)
    sentiment = "NEUTRAL"
    if latest_price > sma_50 > sma_200:
        sentiment = "BULLISH STACKED (Sailing with the wind)"
    elif latest_price < sma_50 < sma_200:
        sentiment = "BEARISH STACKED (Heading into a storm)"
        
    print(f"LATEST PRICE: ${latest_price:.2f}")
    print(f"50-DAY SMA:   ${sma_50:.2f}")
    print(f"200-DAY SMA:  ${sma_200:.2f}")
    print(f"SENTIMENT:    {sentiment}")
    
    # 4. Recent Headlines (The Snap)
    print("\n--- 📰 RECENT HEADLINES ---")
    news = stock.news
    for item in news[:5]: # Show top 5
        title = item.get('title')
        publisher = item.get('publisher')
        print(f"- {title} ({publisher})")

    print(f"\n--- 🏈 SCOUT COMPLETE ---")
    print(f"For the full deep-dive, visit: https://mphinance.substack.com")

if __name__ == "__main__":
    import sys
    # Use command line arg if provided, else default to UAMY
    target = sys.argv[1] if len(sys.argv) > 1 else "UAMY"
    run_scout(target)
