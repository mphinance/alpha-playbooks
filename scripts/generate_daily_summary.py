#!/usr/bin/env python3
"""
Daily Scan Summary Generator
Reads all scan CSVs and creates a concise markdown summary for Sam's memory recall.
"""
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

SCANS_DIR = Path(__file__).parent.parent / "scans"
SUMMARIES_DIR = Path(__file__).parent.parent / "scan_summaries"
TOP_N_PICKS = 10  # Top picks per strategy

def summarize_strategy(csv_path: Path) -> dict:
    """Generate summary stats for a single strategy CSV"""
    try:
        df = pd.read_csv(csv_path)
        
        # Extract strategy name from filename
        strategy_name = csv_path.stem.replace("Screens_v2 - ", "")
        
        # Basic stats
        total_count = len(df)
        
        # Top picks (limit to TOP_N_PICKS)
        top_picks = df.head(TOP_N_PICKS)
        
        # Sector breakdown (if column exists)
        sector_dist = {}
        if 'sector' in df.columns or 'Sector' in df.columns:
            sector_col = 'sector' if 'sector' in df.columns else 'Sector'
            sector_dist = df[sector_col].value_counts().head(5).to_dict()
        
        # Average IV (if exists)
        avg_iv = None
        for col in ['IV', 'iv', 'ImpliedVolatility']:
            if col in df.columns:
                avg_iv = df[col].mean()
                break
        
        return {
            "strategy": strategy_name,
            "total": total_count,
            "top_picks": top_picks,
            "sectors": sector_dist,
            "avg_iv": avg_iv,
            "csv_path": csv_path.name
        }
    except Exception as e:
        return {
            "strategy": csv_path.stem,
            "error": str(e)
        }

def generate_markdown_summary(summaries: list, date: str) -> str:
    """Generate markdown summary from strategy summaries"""
    md = f"# Scan Summary: {date}\n\n"
    md += f"*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    # Overview stats
    total_tickers = sum(s.get('total', 0) for s in summaries if 'error' not in s)
    md += f"## 📊 Overview\n\n"
    md += f"- **Total strategies scanned:** {len(summaries)}\n"
    md += f"- **Total tickers across all scans:** {total_tickers}\n\n"
    
    md += "---\n\n"
    
    # Per-strategy summaries
    for summary in summaries:
        strategy = summary['strategy']
        
        if 'error' in summary:
            md += f"## ⚠️ {strategy}\n\n"
            md += f"*Error: {summary['error']}*\n\n"
            continue
        
        md += f"## 🎯 {strategy}\n\n"
        md += f"**Total tickers:** {summary['total']}\n\n"
        
        # Average IV if available
        if summary.get('avg_iv'):
            md += f"**Avg IV:** {summary['avg_iv']:.1f}%\n\n"
        
        # Sector breakdown
        if summary.get('sectors'):
            md += "**Top sectors:**\n"
            for sector, count in summary['sectors'].items():
                md += f"- {sector}: {count}\n"
            md += "\n"
        
        # Top picks table
        if 'top_picks' in summary and not summary['top_picks'].empty:
            md += f"**Top {min(TOP_N_PICKS, len(summary['top_picks']))} picks:**\n\n"
            
            # Select key columns (adapt based on what exists)
            top_df = summary['top_picks']
            display_cols = []
            
            for col in ['Symbol', 'symbol', 'Ticker', 'ticker']:
                if col in top_df.columns:
                    display_cols.append(col)
                    break
            
            for col in ['close', 'Close', 'price', 'Price']:
                if col in top_df.columns:
                    display_cols.append(col)
                    break
            
            for col in ['volume', 'Volume']:
                if col in top_df.columns:
                    display_cols.append(col)
                    break
            
            for col in ['sector', 'Sector']:
                if col in top_df.columns:
                    display_cols.append(col)
                    break
            
            if display_cols:
                # Manual markdown table (no tabulate dependency)
                md += "| " + " | ".join(display_cols) + " |\n"
                md += "|" + "|".join(["---"] * len(display_cols)) + "|\n"
                for _, row in top_df[display_cols].iterrows():
                    md += "| " + " | ".join(str(v) for v in row) + " |\n"
                md += "\n"
        
        md += f"*Full data: [`{summary['csv_path']}`]({SCANS_DIR / summary['csv_path']})*\n\n"
        md += "---\n\n"
    
    # Memory hints
    md += "## 💡 Memory Hints\n\n"
    md += "Key patterns to remember:\n"
    
    # Find highest IV strategy
    iv_strategies = [(s['strategy'], s.get('avg_iv', 0)) for s in summaries if s.get('avg_iv')]
    if iv_strategies:
        top_iv = max(iv_strategies, key=lambda x: x[1])
        md += f"- **Highest volatility:** {top_iv[0]} ({top_iv[1]:.1f}% avg IV)\n"
    
    # Find largest scan
    count_strategies = [(s['strategy'], s.get('total', 0)) for s in summaries]
    if count_strategies:
        largest = max(count_strategies, key=lambda x: x[1])
        md += f"- **Largest scan:** {largest[0]} ({largest[1]} tickers)\n"
    
    return md

def main():
    """Main summary generation"""
    # Ensure output directory exists
    SUMMARIES_DIR.mkdir(exist_ok=True)
    
    # Today's date
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Find all scan CSVs
    csv_files = sorted(SCANS_DIR.glob("Screens_v2 - *.csv"))
    
    if not csv_files:
        print(f"⚠️ No scan CSVs found in {SCANS_DIR}")
        return
    
    print(f"📊 Processing {len(csv_files)} scan files...")
    
    # Generate summaries for each strategy
    summaries = []
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")
        summary = summarize_strategy(csv_file)
        summaries.append(summary)
    
    # Generate markdown
    markdown = generate_markdown_summary(summaries, today)
    
    # Write to file
    output_file = SUMMARIES_DIR / f"{today}.md"
    output_file.write_text(markdown)
    
    # Create/update "latest" symlink
    latest_link = SUMMARIES_DIR / "latest.md"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(f"{today}.md")
    
    print(f"✅ Summary written to: {output_file}")
    print(f"📌 Latest symlink: {latest_link}")
    print(f"\n📏 Summary size: {output_file.stat().st_size:,} bytes")
    print(f"💾 Total CSV size: {sum(f.stat().st_size for f in csv_files):,} bytes")
    print(f"📊 Compression ratio: {output_file.stat().st_size / sum(f.stat().st_size for f in csv_files) * 100:.1f}%")

if __name__ == "__main__":
    main()
