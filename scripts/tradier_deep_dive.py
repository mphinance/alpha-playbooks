import requests
import os
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TRADIER_ACCESS_TOKEN")
ACCOUNT_ID = os.getenv("TRADIER_ACCOUNT_ID")

def get_options_chains(symbol):
    print(f"\n--- Tradier Options Deep-Dive: {symbol} ---")
    if not TOKEN or not ACCOUNT_ID:
        print("Missing Tradier credentials.")
        return

    # 1. Get Expirations
    url = f"https://api.tradier.com/v1/markets/options/expirations?symbol={symbol}&includeAllRoots=true"
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error fetching expirations: {resp.text}")
        return
        
    expirations_data = resp.json().get('expirations')
    if not expirations_data:
        print(f"No expirations found for {symbol}.")
        return
    expirations = expirations_data.get('date', [])
    if not expirations:
        print("No expirations found.")
        return
        
    next_expiry = expirations[0]
    print(f"Analyzing nearest expiry: {next_expiry}")

    # 2. Get Chain for nearest expiry
    url = f"https://api.tradier.com/v1/markets/options/chains?symbol={symbol}&expiration={next_expiry}&greeks=true"
    resp = requests.get(url, headers=headers)
    
    if resp.status_code != 200:
        print(f"Error fetching chain: {resp.text}")
        return
        
    options = resp.json().get('options', {}).get('option', [])
    if not options:
        print("No options data.")
        return

    # Focus on OTM calls/puts with high IV or volume
    sorted_options = sorted(options, key=lambda x: x.get('volume', 0), reverse=True)
    
    print(f"{'Option':<20} {'Price':<8} {'Vol':<8} {'IV':<8} {'Delta':<8}")
    for opt in sorted_options[:10]:
        greeks = opt.get('greeks', {})
        last = opt.get('last') if opt.get('last') is not None else 0.0
        volume = opt.get('volume') if opt.get('volume') is not None else 0
        mid_iv = greeks.get('mid_iv') if greeks.get('mid_iv') is not None else 0.0
        delta = greeks.get('delta') if greeks.get('delta') is not None else 0.0
        print(f"{opt.get('description', 'N/A'):<20} {last:<8} {volume:<8} {round(mid_iv*100, 1):<8} {delta:<8}")

if __name__ == "__main__":
    # Tickers from pre-market scan with high volume/change
    for ticker in ['MU', 'AMD', 'UAMY', 'STKH', 'BEPC', 'ZM']:
        get_options_chains(ticker)
