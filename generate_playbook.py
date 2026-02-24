import sys
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate Stock Playbook (Legacy Wrapper)")
    parser.add_argument('--ticker', type=str, required=True, help='Stock Ticker Symbol')
    args = parser.parse_args()

    print(f"--- 1. Fetching Playbook Data for {args.ticker} ---")
    subprocess.run([sys.executable, "fetch_playbook_data.py", "--ticker", args.ticker], check=True)
    
    print(f"\n--- 2. Generating Playbook Report for {args.ticker} ---")
    subprocess.run([sys.executable, "generate_playbook_report.py", "--ticker", args.ticker], check=True)
    
    print(f"\n--- 3. Capturing Dashboard Screenshot for {args.ticker} ---")
    subprocess.run([sys.executable, "capture_report.py", "--ticker", args.ticker, "--format", "png"], check=True)
    
    print(f"\n--- 4. Deploying Reports for {args.ticker} ---")
    subprocess.run([sys.executable, "deploy_reports.py", "--ticker", args.ticker], check=True)

if __name__ == "__main__":
    main()
