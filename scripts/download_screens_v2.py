#!/usr/bin/env python3
"""
Download scan history from NotebookLM "Screens v2" notebook
Backfills missing historical data for time series analysis
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
SCANS_DIR = WORKSPACE / "scans" / "historical"

async def download_screens_v2_sources():
    """Download all sources from Screens v2 notebook"""
    
    print("🔐 Connecting to NotebookLM...")
    async with await NotebookLMClient.from_storage() as client:
        
        # Get notebook
        notebook = await client.notebooks.get(SCREENS_V2_NOTEBOOK_ID)
        print(f"📓 Notebook: {notebook.title}")
        
        # List sources
        sources = await client.sources.list(SCREENS_V2_NOTEBOOK_ID)
        print(f"📄 Found {len(sources)} sources")
        
        if not sources:
            print("⚠️ No sources in notebook")
            return
        
        # Create historical directory
        SCANS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Download each source
        for i, source in enumerate(sources, 1):
            print(f"\n[{i}/{len(sources)}] {source.title}")
            print(f"   Type: {source.type}")
            
            try:
                # Get source content
                content = await client.sources.get_content(SCREENS_V2_NOTEBOOK_ID, source.id)
                
                # Save to file
                filename = f"{source.title}.txt"
                # Clean filename
                filename = filename.replace("/", "-").replace("\\", "-")
                output_path = SCANS_DIR / filename
                
                with open(output_path, 'w') as f:
                    f.write(f"# {source.title}\n")
                    f.write(f"# Downloaded from NotebookLM: {datetime.now()}\n\n")
                    f.write(content)
                
                print(f"   ✓ Saved: {output_path}")
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
        
        print(f"\n✅ Downloaded {len(sources)} sources to {SCANS_DIR}")

if __name__ == "__main__":
    asyncio.run(download_screens_v2_sources())
