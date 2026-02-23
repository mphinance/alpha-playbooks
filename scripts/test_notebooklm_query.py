#!/usr/bin/env python3
"""
Test query to NotebookLM "Screens v2" notebook
Demonstrates time series analysis with existing historical data
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add notebooklm-py to path
sys.path.append(str(Path.home() / "anti/notebooklm-py/src"))

from notebooklm.client import NotebookLMClient

SCREENS_V2_NOTEBOOK_ID = "2c9be559-2b90-4a91-8ad5-d2e4f0b655bb"

# Sample analysis prompt
ANALYSIS_PROMPT = """# Trading Pattern Analysis - Live Test

I'm testing the time series analysis workflow. Please analyze the historical scan data in this notebook to identify:

## 🔍 Key Questions

1. **Time Series Patterns**
   - Which tickers have appeared consistently across multiple scans over the past 2 weeks?
   - Are there stocks that "graduated" from one strategy to another (e.g., Gravity Squeeze → MEME Screen)?
   - Which patterns suggest sustained momentum vs. one-day spikes?

2. **Top Trade Setups**
   Based on the historical patterns, provide 3-5 highest conviction setups with:
   - Ticker symbol
   - Which strategies flagged it (and when)
   - Entry price range
   - Target price
   - Stop loss
   - Setup rationale

3. **Strategy Effectiveness**
   - Which scan strategies are finding the most winners?
   - Are there any strategies showing declining quality?

4. **Pattern Warnings**
   - Any tickers showing up repeatedly that match failed setup patterns?
   - Red flags in the recent data?

## 📋 Output Format

Please provide:
- Executive summary (2-3 sentences)
- Top 3-5 trade setups (with specific levels)
- Strategy rankings
- Risk warnings

**Context:** This is a test query to demonstrate how the time series analysis works. Use all available historical data in the notebook.
"""

async def test_notebooklm_query():
    """Test querying NotebookLM with historical data"""
    
    print("=" * 70)
    print("🧪 Testing NotebookLM Time Series Analysis")
    print("=" * 70)
    print()
    
    print("🔐 Connecting to NotebookLM...")
    async with await NotebookLMClient.from_storage() as client:
        
        # Get notebook info
        notebook = await client.notebooks.get(SCREENS_V2_NOTEBOOK_ID)
        print(f"📓 Notebook: {notebook.title}")
        
        # Check sources
        sources = await client.sources.list(SCREENS_V2_NOTEBOOK_ID)
        print(f"📄 Sources: {len(sources)}")
        
        if len(sources) > 0:
            print(f"\n📊 Sample sources:")
            for source in sources[:5]:
                print(f"   - {source.title}")
            if len(sources) > 5:
                print(f"   ... and {len(sources) - 5} more")
        
        # Generate analysis using the prompt
        print(f"\n🔮 Generating time series analysis...")
        print(f"   (This may take 2-3 minutes)")
        
        source_ids = [s.id for s in sources]
        
        try:
            # Generate study guide as a proxy for analysis
            await client.artifacts.generate_study_guide(
                SCREENS_V2_NOTEBOOK_ID,
                source_ids,
                instructions=ANALYSIS_PROMPT
            )
            
            # Wait for completion
            print(f"\n⏳ Waiting for analysis...")
            await asyncio.sleep(60)  # Give it time to process
            
            # Check for study guides
            guides = await client.artifacts.list_study_guides(SCREENS_V2_NOTEBOOK_ID)
            
            if guides:
                latest = guides[0]
                print(f"\n✅ Analysis generated!")
                
                # Download the analysis
                output_path = Path("/home/sam/.openclaw/workspace/notebooklm/test_analysis.md")
                await client.artifacts.download_study_guide(
                    SCREENS_V2_NOTEBOOK_ID,
                    str(output_path)
                )
                
                print(f"📄 Saved to: {output_path}")
                
                # Show preview
                with open(output_path, 'r') as f:
                    content = f.read()
                    print(f"\n{'='*70}")
                    print("📊 ANALYSIS PREVIEW")
                    print(f"{'='*70}\n")
                    print(content[:1000])
                    if len(content) > 1000:
                        print(f"\n... [+{len(content)-1000} more characters]")
                    print(f"\n{'='*70}")
                
                return output_path
            else:
                print(f"\n⏱️ Analysis still processing...")
                print(f"   Check: https://notebooklm.google.com/notebook/{SCREENS_V2_NOTEBOOK_ID}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print(f"\n💡 Try querying manually:")
            print(f"   1. Open: https://notebooklm.google.com/notebook/{SCREENS_V2_NOTEBOOK_ID}")
            print(f"   2. Use the prompt from: notebooklm/prompts/2026-02-09.md")
            return None

if __name__ == "__main__":
    asyncio.run(test_notebooklm_query())
