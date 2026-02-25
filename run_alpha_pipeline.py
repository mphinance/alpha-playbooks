import sys
import os
import subprocess

# List of tickers to process
TICKERS = ["AAPL", "AMD", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA", "SPY", "QQQ"]

def main():
    print("Starting Daily Alpha Pipeline...")
    
    for ticker in TICKERS:
        print(f"\n[{ticker}] Processing...")
        try:
            # Run the standalone script
            subprocess.run([sys.executable, "alpha_standalone.py", "--ticker", ticker], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[{ticker}] Failed: {e}")
            continue

    print("\nPipeline Complete.")

if __name__ == "__main__":
    main()
