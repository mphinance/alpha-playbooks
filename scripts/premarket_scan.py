from tradingview_screener import Query, col
import pandas as pd
import datetime

def run_premarket_scan():
    print(f"--- Pre-Market Scan: {datetime.datetime.now(datetime.timezone.utc)} ---")
    
    # Selecting relevant pre-market columns
    premarket_cols = ['name', 'premarket_change', 'premarket_volume', 'premarket_gap', 'close', 'description']
    
    try:
        # Top Gainers (>2% change)
        q_gainers = (Query().set_markets('america')
                    .select(*premarket_cols)
                    .where(col('premarket_change') > 2)
                    .order_by('premarket_change', ascending=False)
                    .limit(10))
        
        count_g, df_gainers = q_gainers.get_scanner_data()
        print(f"\n### Top Premarket Gainers (>2%) - Count: {count_g}")
        if not df_gainers.empty:
            print(df_gainers.to_string(index=False))
        else:
            print("No significant gainers found.")

        # Volume Leaders
        q_volume = (Query().set_markets('america')
                   .select(*premarket_cols)
                   .order_by('premarket_volume', ascending=False)
                   .limit(10))
        
        count_v, df_volume = q_volume.get_scanner_data()
        print(f"\n### Premarket Volume Leaders - Count: {count_v}")
        if not df_volume.empty:
            print(df_volume.to_string(index=False))
        else:
            print("No volume data found.")
            
    except Exception as e:
        print(f"Error during scan: {e}")

if __name__ == "__main__":
    run_premarket_scan()
