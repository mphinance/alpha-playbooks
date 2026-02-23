import json
import subprocess
import time

WATCHLIST_FILE = "alpha_watchlist.json"
SCRIPT_PATH = "generate_playbook.py"

def run_pulse():
    print(f"--- GHOST PULSE START: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    try:
        with open(WATCHLIST_FILE, 'r') as f:
            config = json.load(f)
            tickers = config.get("tickers", [])
    except Exception as e:
        print(f"Error loading watchlist: {e}")
        return

    for ticker in tickers:
        print(f"\n[!] PROCESSING: {ticker}")
        try:
            # Run the playbook generator
            subprocess.run(["python3", SCRIPT_PATH, "--ticker", ticker], check=True)
            print(f"[+] SUCCESS: {ticker}")
        except subprocess.CalledProcessError as e:
            print(f"[-] FAILED: {ticker} (Exit code: {e.returncode})")
        except Exception as e:
            print(f"[-] ERROR: {ticker} - {e}")
            
    print(f"\n--- GHOST PULSE COMPLETE ---")

if __name__ == "__main__":
    run_pulse()