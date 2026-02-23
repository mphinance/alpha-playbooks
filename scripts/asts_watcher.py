import sys
import json
import subprocess

TARGET_PRICE = 100.5
SYMBOL = "ASTS"

def get_price():
    try:
        # Run the yahoo-data-fetcher skill
        result = subprocess.run(
            ["node", "/home/sam/.openclaw/workspace/skills/yahoo-data-fetcher/index.js", SYMBOL],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        if isinstance(data, list) and len(data) > 0:
            return float(data[0].get("price", 0))
    except Exception as e:
        print(f"Error fetching price: {e}")
    return None

def alert(price):
    msg = f"⚠️ $ASTS Alert: Price dropped to ${price:.2f} (Target: < $100.50)"
    subprocess.run([
        "openclaw", "message", "send",
        "--target", "8024985134",
        "--message", msg
    ])
    # Cleanup: remove the cron job once triggered
    subprocess.run(["openclaw", "cron", "remove", "--jobId", "asts-price-watcher"])

price = get_price()
if price is not None and price < TARGET_PRICE:
    alert(price)
else:
    print(f"Current price: {price}")
