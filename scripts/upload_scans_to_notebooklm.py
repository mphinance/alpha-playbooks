#!/usr/bin/env python3
"""
Upload today's scan CSVs to NotebookLM "Screens v2" notebook
Builds time series automatically - NotebookLM accumulates historical data
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add notebooklm-py to path
sys.path.append(str(Path.home() / "anti/notebooklm-py/src"))

from notebooklm.client import NotebookLMClient

SCREENS_V2_NOTEBOOK_ID = "2c9be559-2b90-4a91-8ad5-d2e4f0b655bb"
WORKSPACE = Path("/home/sam/.openclaw/workspace")
SCANS_DIR = WORKSPACE / "scans"

async def upload_todays_scans():
    """Upload all today's scan CSVs to NotebookLM"""
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Find all CSV files
    csv_files = list(SCANS_DIR.glob("*.csv"))
    
    if not csv_files:
        print(f"⚠️ No CSV files found in {SCANS_DIR}")
        return
    
    print(f"📊 Found {len(csv_files)} scan files")
    
    print("\n🔐 Connecting to NotebookLM...")
    async with await NotebookLMClient.from_storage() as client:
        
        # Get notebook
        notebook = await client.notebooks.get(SCREENS_V2_NOTEBOOK_ID)
        print(f"📓 Notebook: {notebook.title}")
        
        # Upload each CSV
        uploaded = 0
        for csv_file in csv_files:
            strategy_name = csv_file.stem.replace("Screens_v2 - ", "")
            source_title = f"{strategy_name} - {today}"
            
            print(f"\n📤 Uploading: {csv_file.name}")
            print(f"   Title: {source_title}")
            
            try:
                # Read CSV content
                with open(csv_file, 'r') as f:
                    csv_content = f.read()
                
                # Upload as text source (NotebookLM handles CSV parsing)
                await client.sources.add_text(
                    SCREENS_V2_NOTEBOOK_ID,
                    source_title,
                    csv_content
                )
                
                uploaded += 1
                print(f"   ✓ Uploaded successfully")
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
        
        print(f"\n✅ Uploaded {uploaded}/{len(csv_files)} scan files to NotebookLM")
        print(f"📊 Time series now includes data from {today}")
        print(f"🔗 View: https://notebooklm.google.com/notebook/{SCREENS_V2_NOTEBOOK_ID}")

if __name__ == "__main__":
    asyncio.run(upload_todays_scans())
