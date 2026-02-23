#!/bin/bash
SPREADSHEET_ID="1afuWcQ-cYyACqkS0BUzVAu3HdOuHJIwcS1JFbNnWUoo"
ACCOUNT="mphanko@gmail.com"
OUTPUT_DIR="scan_summaries/Screens_v2"
export GOG_KEYRING_PASSWORD=openclaw

# Read sheet titles from metadata, handling spaces by using mapfile or while read
mapfile -t SHEETS < <(jq -r '.sheets[].properties.title' "$OUTPUT_DIR/metadata.json")

echo "Starting export for $SPREADSHEET_ID..."

for SHEET in "${SHEETS[@]}"; do
    echo "Exporting: $SHEET"
    # Fetch as JSON first
    gog sheets get "$SPREADSHEET_ID" "'$SHEET'!A1:Z500" --account "$ACCOUNT" --json > "$OUTPUT_DIR/tmp.json"
    
    # Check if we actually got values
    if [[ $(jq '.values | length' "$OUTPUT_DIR/tmp.json") -eq 0 ]]; then
        echo "Sheet $SHEET is empty, skipping."
        rm "$OUTPUT_DIR/tmp.json"
        continue
    fi

    # Sanitize sheet name for filename (replace spaces with underscores)
    SAFE_NAME=$(echo "$SHEET" | tr ' ' '_')
    
    echo "# $SHEET" > "$OUTPUT_DIR/$SAFE_NAME.md"
    echo "" >> "$OUTPUT_DIR/$SAFE_NAME.md"
    
    # Improved jq for MD table generation
    jq -r '.values | .[0] as $h | ( "| " + (.[0] | join(" | ")) + " |"), ( "| " + (.[0] | map("---") | join(" | ")) + " |"), (.[1:] | .[] | "| " + (map(if . == null then " " else . end) | join(" | ")) + " |")' "$OUTPUT_DIR/tmp.json" >> "$OUTPUT_DIR/$SAFE_NAME.md"
    
    rm "$OUTPUT_DIR/tmp.json"
done

echo "Done."
