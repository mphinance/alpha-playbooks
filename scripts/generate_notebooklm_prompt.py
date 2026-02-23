#!/usr/bin/env python3
"""
Sam's Daily NotebookLM Prompt Generator
Analyzes scans + news → crafts intelligent prompt → Sam uses NotebookLM skill
"""
import sys
from pathlib import Path
from datetime import datetime
import re

WORKSPACE = Path(__file__).parent.parent
SUMMARIES_DIR = WORKSPACE / "scan_summaries"
PROMPTS_DIR = WORKSPACE / "notebooklm" / "prompts"

def extract_tickers_from_summary(summary_path: Path) -> dict:
    """Extract tickers and their strategies from summary"""
    with open(summary_path, 'r') as f:
        content = f.read()
    
    ticker_strategies = {}
    
    # Extract from each strategy section
    strategies = {
        "Gravity Squeeze": "## 🎯 Gravity Squeeze",
        "MEME Screen": "## 🎯 MEME Screen", 
        "Gamma Scan": "## 🎯 Gamma Scan",
        "Volatility Squeeze": "## 🎯 Volatility Squeeze",
        "Momentum with Pullback": "## 🎯 Momentum with Pullback",
        "Small Cap Multibaggers": "## 🎯 Small Cap Multibaggers"
    }
    
    for strategy_name, header in strategies.items():
        if header not in content:
            continue
            
        # Get section text
        parts = content.split(header)
        if len(parts) < 2:
            continue
        section = parts[1].split("---")[0]
        
        # Find tickers (1-5 uppercase letters)
        ticker_pattern = r'\b([A-Z]{1,5})\b'
        matches = re.findall(ticker_pattern, section)
        
        # Filter noise
        exclude = {'TOP', 'TOTAL', 'SCAN', 'PICKS', 'AVG', 'ERROR', 'CSV'}
        for ticker in matches:
            if ticker not in exclude and len(ticker) <= 5:
                if ticker not in ticker_strategies:
                    ticker_strategies[ticker] = []
                if strategy_name not in ticker_strategies[ticker]:
                    ticker_strategies[ticker].append(strategy_name)
    
    return ticker_strategies

def craft_notebooklm_prompt(ticker_strategies: dict, date: str) -> str:
    """Sam crafts the daily analysis prompt"""
    
    # Multi-strategy signals (highest conviction)
    multi = {t: s for t, s in ticker_strategies.items() if len(s) > 1}
    
    prompt = f"""# Trading Pattern Analysis - {date}

## 📊 Today's Scan Results

### Multi-Strategy Signals (Top Priority)
"""
    
    if multi:
        for ticker, strategies in sorted(multi.items(), key=lambda x: len(x[1]), reverse=True)[:8]:
            prompt += f"- **${ticker}**: {', '.join(strategies)} ({len(strategies)} strategies)\n"
    else:
        prompt += "*No multi-strategy signals today*\n"
    
    # Top tickers by strategy
    prompt += f"""

### Top Picks by Strategy
"""
    
    # Group by strategy
    by_strategy = {}
    for ticker, strategies in ticker_strategies.items():
        for strategy in strategies:
            if strategy not in by_strategy:
                by_strategy[strategy] = []
            by_strategy[strategy].append(ticker)
    
    for strategy, tickers in sorted(by_strategy.items()):
        prompt += f"\n**{strategy}**: {', '.join(tickers[:10])}"
    
    prompt += f"""

---

## 🔍 Time Series Analysis Questions

I need you to analyze the patterns across the past 2 weeks to identify high-probability trade setups.

### 1. Pattern Recognition
- Which tickers from today's list have appeared consistently over multiple days?
- Are there stocks that "graduated" from one strategy to another?
  - Example: Gravity Squeeze → MEME Screen (momentum building)
  - Example: Volatility Squeeze → Gamma Scan (options activity increasing)
- Which patterns suggest sustained momentum vs. one-day spikes?

### 2. Cross-Strategy Convergence
**For the multi-strategy tickers above:**
- What does it mean when a stock appears in both {list(multi.keys())[:3] if multi else ['multiple strategies']}?
- Are these showing institutional accumulation or retail FOMO?
- Which combinations have historically led to successful trades?

### 3. Trade Setups
Based on the 2-week time series, provide:
- **Top 3-5 highest conviction setups** with:
  - Entry price range
  - Target price (based on historical resistance)
  - Stop loss level
  - Timeframe (swing vs. day trade)
  - Setup rationale (why this ticker, why now)

### 4. Strategy Effectiveness Analysis
- Which strategies are "hot" this week (finding winners)?
- Which strategies are cooling off (fewer quality picks)?
- Should I adjust my scan parameters based on current market conditions?

### 5. Risk Management
- Are there any tickers showing up repeatedly that later crashed?
- What patterns preceded failed setups in the historical data?
- Red flags to watch for in today's picks?

---

## 📋 Output Format

Please provide:

1. **Executive Summary** (3-4 sentences)
   - Overall market conditions from scan perspective
   - Dominant pattern this week
   - Risk level assessment

2. **High-Conviction Setups** (Top 3-5)
   ```
   Ticker: $SYMBOL
   Strategy: [Which scans flagged it]
   Time Series: [How it's been moving across strategies]
   Entry: $X.XX - $X.XX
   Target: $X.XX (X% gain)
   Stop: $X.XX (X% risk)
   Timeframe: [Days/weeks]
   Rationale: [Why this setup has edge]
   ```

3. **Pattern Warnings**
   - Tickers that match historical failure patterns
   - Red flags in today's data

4. **Strategy Rankings**
   - Which strategies are performing best this week
   - Recommended focus areas

---

**Context:** This prompt is generated daily by Sam (my trading agent) who runs 9 scan strategies across the market. The "Screens v2" notebook contains 2 weeks of historical scan data showing how stocks move through different strategies over time. Sam needs actionable trade setups with specific entries/exits based on pattern recognition, not generic analysis.
"""
    
    return prompt

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    
    print("=" * 70)
    print("📝 Sam's NotebookLM Prompt Generator")
    print("=" * 70)
    print()
    
    # Check for today's summary
    summary_path = SUMMARIES_DIR / f"{today}.md"
    if not summary_path.exists():
        print(f"❌ No scan summary found for {today}")
        print(f"Run: python3 scripts/generate_daily_summary.py")
        sys.exit(1)
    
    print(f"📄 Reading: {summary_path.name}")
    
    # Extract tickers
    ticker_strategies = extract_tickers_from_summary(summary_path)
    total = len(ticker_strategies)
    multi = len({t: s for t, s in ticker_strategies.items() if len(s) > 1})
    
    print(f"📊 Found: {total} tickers ({multi} with multi-strategy signals)")
    
    # Craft prompt
    prompt = craft_notebooklm_prompt(ticker_strategies, today)
    
    # Save prompt
    PROMPTS_DIR.mkdir(exist_ok=True, parents=True)
    prompt_file = PROMPTS_DIR / f"{today}.md"
    with open(prompt_file, 'w') as f:
        f.write(prompt)
    
    print(f"✅ Prompt saved: {prompt_file}")
    print()
    print("-" * 70)
    print("📋 Next Steps:")
    print("-" * 70)
    print()
    print("1. Review the prompt (optional):")
    print(f"   cat {prompt_file}")
    print()
    print("2. Sam uses NotebookLM skill to query 'Screens v2' notebook:")
    print(f"   Query notebook 2c9be559-2b90-4a91-8ad5-d2e4f0b655bb with prompt from {prompt_file.name}")
    print()
    print("3. Or copy/paste prompt to NotebookLM web UI")
    print()

if __name__ == "__main__":
    main()
