from tradingview_screener import Query, col
import pandas as pd
import datetime

def check_watchlist():
    tickers = ['AVGO', 'GLXY', 'UAMY', 'ONDS', 'AMD', 'MU', 'HOLX', 'F']
    premarket_cols = ['name', 'premarket_change', 'premarket_volume', 'premarket_gap', 'close']
    
    q = (Query().set_markets('america')
        .select(*premarket_cols)
        .where(col('name').isin(tickers)))
    
    count, df = q.get_scanner_data()
    print(f"\n### Watchlist Premarket Activity")
    if not df.empty:
        print(df.to_string(index=False))
    else:
        print("No watchlist data found.")

if __name__ == "__main__":
    check_watchlist()
