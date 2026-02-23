#!/bin/bash
# scripts/get_live_price.sh - Get real-time price using ticker CLI

TICKER_BIN="/home/sam/.openclaw/workspace/tools/ticker/ticker"
SYMBOL=$1

if [ -z "$SYMBOL" ]; then
    echo "Usage: $0 <SYMBOL>"
    exit 1
fi

# Run ticker with timeout and PTY
# We use a short timeout to let it fetch the data
# Then we strip ANSI escape codes and find the symbol line
RESULT=$(timeout 4 stdbuf -oL script -q -c "$TICKER_BIN -w $SYMBOL" /dev/null | sed 's/\x1b\[[0-9;]*[mGKHJK]//g' | tr -d '\r')

# Extract price (look for symbol and pull the first number after it)
PRICE=$(echo "$RESULT" | grep -A 1 "^$SYMBOL" | head -n 1 | grep -oE '[0-9]+\.[0-9]+' | head -n 1)
CHANGE=$(echo "$RESULT" | grep -A 1 "^$SYMBOL" | tail -n 1 | grep -oE '[↑↓] [0-9]+\.[0-9]+ \([0-9]+\.[0-9]+%\)')

if [ -z "$PRICE" ]; then
    # Fallback: maybe symbol is on same line as price
    PRICE=$(echo "$RESULT" | grep "$SYMBOL" | grep -oE '[0-9]+\.[0-9]+' | head -n 1)
fi

echo "SYMBOL: $SYMBOL"
echo "PRICE: $PRICE"
echo "CHANGE: $CHANGE"
