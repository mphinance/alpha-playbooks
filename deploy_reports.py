import os
import argparse
import subprocess
from datetime import datetime

from config import VULTR_ALIAS, VULTR_WEB_ROOT, VENUS_STORAGE

def deploy_to_vultr(ticker):
    """Sync the local reports to Vultr web root."""
    print(f"Deploying {ticker} to Vultr...")
    try:
        remote_dir = f"{VULTR_WEB_ROOT}/{ticker}"
        subprocess.run(["ssh", VULTR_ALIAS, f"mkdir -p {remote_dir}"], check=True)
        
        local_dir = f"reports/{ticker}"
        subprocess.run(["scp", "-r", local_dir, f"{VULTR_ALIAS}:{VULTR_WEB_ROOT}/"], check=True)
        
        # Upload Root Index
        if os.path.exists("index.html"):
            subprocess.run(["scp", "index.html", f"{VULTR_ALIAS}:{VULTR_WEB_ROOT}/index.html"], check=True)
            
        # Create symlink for latest.html
        date_str = datetime.now().strftime('%Y-%m-%d')
        subprocess.run([
            "ssh", VULTR_ALIAS, 
            f"ln -sf {VULTR_WEB_ROOT}/{ticker}/{date_str}.html {VULTR_WEB_ROOT}/{ticker}/latest.html"
        ], check=True)
        
        print(f"Deployment to Vultr complete: https://mphinance.com/alpha/{ticker}/latest.html")
    except Exception as e:
        print(f"Vultr Deployment Error: {e}")

def backup_to_venus():
    """Sync the local reports to Venus large storage."""
    print("Backing up to Venus...")
    try:
        subprocess.run(["mkdir", "-p", VENUS_STORAGE], check=True)
        subprocess.run(["rsync", "-avz", "reports/", VENUS_STORAGE], check=True)
        print(f"Backup to Venus complete: {VENUS_STORAGE}")
    except Exception as e:
        print(f"Venus Backup Error: {e}")

def deploy_global_docs():
    """Deploy docs directory for options dashboard if exists"""
    try:
        if os.path.exists("docs/index.html"):
            print("Deploying Global Docs/Indices...")
            subprocess.run(["ssh", VULTR_ALIAS, f"mkdir -p {VULTR_WEB_ROOT}/docs"], check=True)
            subprocess.run(["scp", "docs/index.html", f"{VULTR_ALIAS}:{VULTR_WEB_ROOT}/docs/index.html"], check=True)
    except Exception as e:
        print(f"Docs Deployment Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Deploy Playbook Reports")
    parser.add_argument('--ticker', type=str, required=True, help='Stock Ticker Symbol')
    args = parser.parse_args()

    deploy_to_vultr(args.ticker)
    deploy_global_docs()
    backup_to_venus()

if __name__ == "__main__":
    main()
