import json
import os
import sys
import argparse
import yfinance as yf
import pandas as pd
import numpy as np
import httpx
import feedparser
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from jinja2 import Environment, FileSystemLoader, select_autoescape
from tradingview_ta import TA_Handler, Interval

# --- Technical Indicator Implementations ---
def calculate_sma(series, window):
    return series.rolling(window=window).mean()

def calculate_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series, fast=12, slow=26, signal=9):
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd = ema_fast - ema_slow
    signal_line = calculate_ema(macd, signal)
    hist = macd - signal_line
    return macd, signal_line, hist

def calculate_adx(high, low, close, window=14):
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    
    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame(abs(high - close.shift(1)))
    tr3 = pd.DataFrame(abs(low - close.shift(1)))
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='outer').max(axis=1)
    
    atr = tr.rolling(window).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1/window).mean() / atr)
    minus_di = 100 * abs(minus_dm.ewm(alpha=1/window).mean() / atr)
    dx = (abs(plus_di - minus_di) / abs(plus_di + minus_di)) * 100
    adx = dx.rolling(window).mean()
    return adx

# --- Helper Functions ---
def clean_dict(d):
    if isinstance(d, dict):
        return {k: clean_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [clean_dict(v) for v in d]
    elif isinstance(d, float):
        if np.isnan(d) or np.isinf(d): return None
        return round(d, 2)
    elif isinstance(d, pd.Timestamp):
        return d.strftime('%Y-%m-%d')
    else:
        return d

def format_large_number(num):
    if num is None: return "N/A"
    try:
        num = float(num)
        if num >= 1_000_000_000:
            return f"${num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num / 1_000_000:.2f}M"
        else:
            return f"${num:,.0f}"
    except (ValueError, TypeError):
        return str(num)

def calculate_intrinsic_value(info, current_price):
    eps = info.get('trailingEps', 0)
    bvps = info.get('bookValue', 0)
    current_price = float(current_price)
    
    rev_growth = info.get('revenueGrowth', 0)
    if rev_growth is None: rev_growth = 0
    
    analyst_target = info.get('targetMeanPrice')
    if analyst_target is None: analyst_target = 0
    else: analyst_target = float(analyst_target)

    graham = 0
    if eps and bvps and eps > 0 and bvps > 0:
        try: graham = float(np.sqrt(22.5 * eps * bvps))
        except: pass
        
    lynch = 0
    if eps and eps > 0 and rev_growth > 0:
        lynch = eps * (rev_growth * 100)
        
    is_profitable = eps is not None and eps > 0
    has_analyst = analyst_target > 0
    
    final_value = 0
    method_str = "UNKNOWN"
    used_methods = []
    
    if is_profitable:
        candidates = []
        if graham > 0: candidates.append(graham); used_methods.append("Graham")
        if lynch > 0: candidates.append(lynch); used_methods.append("Lynch")
        if has_analyst: candidates.append(analyst_target); used_methods.append("Analyst")
        
        if candidates:
            final_value = sum(candidates) / len(candidates)
            method_str = "BLENDED (" + "+".join(used_methods) + ")"
        else:
            method_str = "INSUFFICIENT DATA"
    else:
        if has_analyst:
            final_value = analyst_target
            method_str = "ANALYST CONSENSUS"
            
    gap = 0
    status = "UNKNOWN"
    
    if final_value > 0:
        gap = ((final_value - current_price) / current_price) * 100
        if gap > 20: status = "UNDERVALUED"
        elif gap < -20: status = "OVERVALUED"
        else: status = "FAIR VALUE"
        
    return {
        "status": status,
        "gap_pct": round(gap, 1),
        "target_price": round(final_value, 2),
        "method": method_str,
        "details": {
            "graham": round(graham, 2),
            "lynch": round(lynch, 2),
            "analyst": round(analyst_target, 2)
        }
    }

def fetch_ticker_data(ticker):
    print(f"Fetching data for {ticker}...")
    stock = yf.Ticker(ticker)
    
    try:
        df = stock.history(period='2y')
        if df.empty:
            raise ValueError(f"No price data found for {ticker}")
    except Exception as e:
        print(f"Error fetching history: {e}")
        return None

    df['EMA_8'] = calculate_ema(df['Close'], 8)
    df['EMA_21'] = calculate_ema(df['Close'], 21)
    df['EMA_34'] = calculate_ema(df['Close'], 34)
    df['EMA_55'] = calculate_ema(df['Close'], 55)
    df['EMA_89'] = calculate_ema(df['Close'], 89)
    
    sma_50_series = calculate_sma(df['Close'], 50)
    sma_200_series = calculate_sma(df['Close'], 200)
    sma_50 = sma_50_series.iloc[-1] if not sma_50_series.empty else np.nan
    sma_200 = sma_200_series.iloc[-1] if not sma_200_series.empty else np.nan
    sma_200_val = sma_200 if not np.isnan(sma_200) else sma_50 if not np.isnan(sma_50) else df['Close'].iloc[-1]
    sma_50_val = sma_50 if not np.isnan(sma_50) else df['Close'].iloc[-1]
    
    macd_line, signal_line, macd_hist = calculate_macd(df['Close'])
    df['MACDh_12_26_9'] = macd_hist
    df['RSI_14'] = calculate_rsi(df['Close'])
    df['ADX_14'] = calculate_adx(df['High'], df['Low'], df['Close'])
    df['log_ret'] = np.log(df['Close'] / df['Close'].shift(1))
    hv = df['log_ret'].rolling(window=30).std() * np.sqrt(252) * 100
    vol_avg = df['Volume'].rolling(window=20).mean()
    rel_vol = df['Volume'] / vol_avg
    
    iv = 0
    try:
        opt_chain = stock.options
        if opt_chain:
            exp = opt_chain[min(2, len(opt_chain)-1)]
            calls = stock.option_chain(exp).calls
            latest_close = df['Close'].iloc[-1]
            atm_iv = calls[(calls['strike'] >= latest_close * 0.95) & (calls['strike'] <= latest_close * 1.05)]
            if not atm_iv.empty:
                iv = atm_iv['impliedVolatility'].mean() * 100
    except: pass
    
    hist_month = df.iloc[-21:]
    high_m, low_m, close_m = hist_month['High'].max(), hist_month['Low'].min(), hist_month['Close'].iloc[-1]
    pp = (high_m + low_m + close_m) / 3
    hist_1y = df.iloc[-252:]
    h52, l52 = hist_1y['High'].max(), hist_1y['Low'].min()
    diff = h52 - l52
    latest = df.iloc[-1]

    fundamentals = {'insiders': [], 'news': [], 'info': {}, 'calendar': {}}
    def fetch_fundamental_component(component):
        try:
            if component == 'insiders': return 'insiders', stock.insider_transactions
            elif component == 'news': return 'news', stock.news
            elif component == 'info': return 'info', stock.info
            elif component == 'calendar': return 'calendar', stock.calendar
        except: return component, None

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_fundamental_component, c) for c in ['insiders', 'news', 'info', 'calendar']]
        for future in futures:
            key, result = future.result()
            if result is not None: fundamentals[key] = result

    insider_data = []
    if isinstance(fundamentals['insiders'], pd.DataFrame) and not fundamentals['insiders'].empty:
        df_insiders = fundamentals['insiders'].reset_index()
        for _, row in df_insiders.head(5).iterrows():
            try:
                date_val = row.get('Start Date') or row.get('Date')
                date_str = date_val.strftime('%Y-%m-%d') if isinstance(date_val, pd.Timestamp) else str(date_val)
                val = row.get('Value')
                value_str = format_large_number(val) if isinstance(val, (int, float)) else str(val)
                insider_data.append({"date": date_str, "insider": row.get('Insider', 'Unknown'), "type": row.get('Transaction', 'Unknown'), "value": value_str})
            except: continue
    
    RSS_FEEDS = {
        "bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
        "wsj": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "cnbc": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147",
        "seekingalpha": "https://seekingalpha.com/market_currents.xml",
        "marketwatch": "https://www.marketwatch.com/rss/topstories",
        "ft": "https://www.ft.com/rss/home"
    }

    rss_items = []
    def fetch_rss(source, url):
        try:
            with httpx.Client(timeout=5.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                feed = feedparser.parse(response.text)
                return source, feed.entries
        except: return source, []

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_rss, src, url) for src, url in RSS_FEEDS.items()]
        for future in futures:
            try:
                src, entries = future.result(timeout=10)
                for entry in entries[:2]: 
                    rss_items.append({'title': entry.get('title', 'No Title'), 'link': entry.get('link', ''), 'source': src.upper(), 'summary': entry.get('summary', entry.get('description', 'No summary'))[:150] + "..."})
            except: pass

    tv_analysis = {}
    try:
        info = fundamentals.get('info', {})
        exchange_map = {'NMS': 'NASDAQ', 'NYQ': 'NYSE', 'NGM': 'NASDAQ', 'ASE': 'AMEX', 'PCX': 'ARCA'}
        raw_exchange = info.get('exchange', 'NMS')
        exchange = exchange_map.get(raw_exchange, 'NASDAQ')
        handler = TA_Handler(symbol=ticker, screener="america", exchange=exchange, interval=Interval.INTERVAL_1_DAY)
        analysis = handler.get_analysis()
        tv_analysis = {"summary": analysis.summary, "oscillators": analysis.oscillators, "moving_averages": analysis.moving_averages, "indicators": analysis.indicators}
    except: tv_analysis = {"summary": {"RECOMMENDATION": "UNAVAILABLE"}}

    ticker_feed = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}"
    try:
        tf = feedparser.parse(ticker_feed)
        for entry in tf.entries[:5]:
             rss_items.insert(0, {'title': entry.get('title', 'No Title'), 'link': entry.get('link', ''), 'source': 'YF-RSS', 'summary': entry.get('summary', entry.get('description', 'No summary'))[:150] + "..."})
    except: pass

    seen_titles = set()
    unique_items = []
    for item in rss_items:
        if item['title'] not in seen_titles:
            unique_items.append(item); seen_titles.add(item['title'])
            
    supply_chain_claims = []
    for item in unique_items[:8]:
        supply_chain_claims.append({"claim": f"<a href='{item['link']}' target='_blank' class='hover:text-neon-blue transition-colors'>{item['title']}</a>", "status": "NEWS", "desc": f"<span class='text-neon-blue'>[{item['source']}]</span> {item['summary']}"})

    info = fundamentals['info']
    sec_ops = f"{info.get('longName', ticker)} // {info.get('sector', 'N/A')} [{info.get('industry', 'N/A')}]. Mkt Cap: {format_large_number(info.get('marketCap'))}. Rev Growth: {info.get('revenueGrowth', 0)*100 if info.get('revenueGrowth') else 0:.1f}%. PM: {info.get('profitMargins', 0)*100 if info.get('profitMargins') else 0:.1f}%."
    sec_risks = f"Beta: {info.get('beta', 'N/A')}. Range(52W): {info.get('fiftyTwoWeekLow', 0)} - {info.get('fiftyTwoWeekHigh', 0)}. Analyst Tgt: {info.get('targetMeanPrice', 'N/A')}."
    geo = {"site": f"{info.get('city', 'Unknown')}, {info.get('country', 'Unknown')}", "coords": info.get('website', 'N/A'), "score": 0.0, "observations": [{"period": "Current", "desc": "Headquarters location."}]}

    chart_data = []
    ema_data = { "8": [], "21": [], "34": [], "55": [], "89": [] }
    try:
        hist_data = df.tail(400).copy().reset_index()
        for _, row in hist_data.iterrows():
            d_val = row['Date']
            d_str = d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else ""
            if d_str:
                chart_data.append({"time": d_str, "open": round(row['Open'], 2), "high": round(row['High'], 2), "low": round(row['Low'], 2), "close": round(row['Close'], 2)})
                for span in ["8", "21", "34", "55", "89"]:
                    val = row.get(f"EMA_{span}")
                    if val is not None and not np.isnan(val): ema_data[span].append({"time": d_str, "value": round(float(val), 2)})
    except: pass

    val_result = calculate_intrinsic_value(info, latest['Close'])
    website = info.get('website', '')
    logo_url = info.get('logo_url', '')
    if not logo_url and website:
        try:
            domain = website.replace('http://', '').replace('https://', '').split('/')[0]
            logo_url = f"https://logo.clearbit.com/{domain}"
        except: logo_url = ""

    data = {
        "ticker": ticker, "logo_url": logo_url, "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "chart_data": chart_data, "ema_data": ema_data,
        "market_snapshot": { "price": round(float(latest['Close']), 2), "market_cap": format_large_number(info.get('marketCap')), "beta": info.get('beta', 'N/A'), "range_52w": f"{info.get('fiftyTwoWeekLow', 0)} - {info.get('fiftyTwoWeekHigh', 0)}", "analyst_target": info.get('targetMeanPrice', 'N/A') },
        "tradingview": tv_analysis,
        "technical_analysis": {
            "trend": { "outlook": "Bullish" if sma_50_val > sma_200_val else "Bearish", "sma_50": round(float(sma_50), 2) if not np.isnan(sma_50) else None, "sma_200": round(float(sma_200), 2) if not np.isnan(sma_200) else None, "crossover": "Golden Cross" if sma_50_val > sma_200_val else "Death Cross" },
            "ema": { "8": round(float(latest['EMA_8']), 2), "21": round(float(latest['EMA_21']), 2), "34": round(float(latest['EMA_34']), 2), "55": round(float(latest['EMA_55']), 2), "89": round(float(latest['EMA_89']), 2) },
            "volume": { "current": f"{int(latest['Volume']):,}", "avg_20d": f"{int(vol_avg.iloc[-1]):,}", "rel_vol": round(float(rel_vol.iloc[-1]), 2), "rel_vol_pct": min(100, int(rel_vol.iloc[-1] * 50)) },
            "pivots": { "R2": round(pp + (high_m - low_m), 2), "R1": round((2 * pp) - low_m, 2), "PP": round(pp, 2), "S1": round((2 * pp) - high_m, 2), "S2": round(pp - (high_m - low_m), 2) },
            "fibonacci": { "100": round(h52, 2), "61.8": round(h52 - 0.382 * diff, 2), "50": round(h52 - 0.5 * diff, 2), "38.2": round(h52 - 0.618 * diff, 2), "0": round(l52, 2) },
            "oscillators": { "rsi_14": round(float(latest['RSI_14']), 2) if not np.isnan(latest['RSI_14']) else None, "adx_14": round(float(latest['ADX_14']), 2) if not np.isnan(latest['ADX_14']) else None, "macd_hist": round(float(latest['MACDh_12_26_9']), 2) if not np.isnan(latest['MACDh_12_26_9']) else None }
        },
        "volatility": { "hv_30d": round(float(hv.iloc[-1]), 2), "iv_current": round(float(iv), 2) },
        "insider_transactions": insider_data, "intel_feed": unique_items[:8], "supply_chain": { "claims": supply_chain_claims, "shipments": [] }, 
        "sec_insights": { "operations": sec_ops, "forward_looking": sec_risks }, "geospatial": geo
    }

    tech_score = 50
    if sma_50 > sma_200: tech_score += 20
    else: tech_score -= 20
    if latest['Close'] > sma_50: tech_score += 10
    else: tech_score -= 10
    if latest['Close'] > sma_200: tech_score += 10
    else: tech_score -= 10
    rsi = data['technical_analysis']['oscillators'].get('rsi_14')
    if rsi:
        if 40 < rsi < 60: tech_score += 5
        elif 30 < rsi <= 40: tech_score += 10
        elif 60 <= rsi < 70: tech_score += 10
        elif rsi >= 70: tech_score -= 5
        elif rsi <= 30: tech_score -= 5
        
    fund_score = 50
    if info.get('profitMargins', 0) > 0.1: fund_score += 10
    if info.get('revenueGrowth', 0) > 0.05: fund_score += 10
    insider_sentiment = 0
    for i in insider_data:
        try:
            if 'Purchase' in i.get('type',''): insider_sentiment += 1
            elif 'Sale' in i.get('type',''): insider_sentiment -= 1
        except: pass
    if insider_sentiment > 0: fund_score += 10
    elif insider_sentiment < 0: fund_score -= 5
    tgt = info.get('targetMeanPrice')
    if tgt and tgt > latest['Close']: fund_score += 10
    
    tech_score = max(0, min(100, tech_score))
    fund_score = max(0, min(100, fund_score))
    data["scores"] = { "technical": tech_score, "fundamental": fund_score, "grade": "A" if (tech_score+fund_score)/2 > 80 else "B" if (tech_score+fund_score)/2 > 60 else "C" if (tech_score+fund_score)/2 > 40 else "D" }
    data["valuation"] = { "status": val_result['status'], "gap_pct": round(val_result['gap_pct'], 2), "target_price": round(val_result['target_price'], 2), "graham_num": val_result['details']['graham'], "lynch_value": val_result['details']['lynch'], "method": val_result['method'] }
    
    def generate_ai_narrative(d):
        t_score, f_score = d['scores']['technical'], d['scores']['fundamental']
        trend, val_status, val_gap = d['technical_analysis']['trend']['outlook'], d['valuation']['status'], d['valuation']['gap_pct']
        narrative = f"<span class='text-neon-blue font-bold'>AI.SYNTHESIS // </span> <br>Asset demonstrates a <span class='{'text-neon-green' if t_score > 60 else 'text-neon-red'}'>{'STRONG' if t_score > 70 else 'WEAK' if t_score < 40 else 'NEUTRAL'}</span> technical posture (Score: {t_score}/100) within a wider {trend} trend. "
        if val_status == "UNDERVALUED": narrative += f"Models suggest the asset is <span class='text-neon-green'>UNDERVALUED</span> by {abs(val_gap)}%, implying a significant margin of safety. "
        elif val_status == "OVERVALUED": narrative += f"However, valuation models indicate the asset is <span class='text-neon-red'>OVERVALUED</span> by ~{val_gap}%; price may be extended beyond fundamentals. "
        else: narrative += f"Asset appears fairly valued relative to growth and book value. "
        narrative += f"<br><br><span class='text-neon-amber font-bold'>VERDICT // </span>{'ACCUMULATE on Dips' if t_score > 60 and val_status != 'OVERVALUED' else 'DISTRIBUTE into Strength' if t_score < 40 else 'WAIT for Validation'}."
        return narrative
    data['ai_analysis'] = generate_ai_narrative(data)
    return clean_dict(data)

def generate_html(data):
    """Fetch template from GitHub and render the final HUD HTML report."""
    TEMPLATE_URL = "https://raw.githubusercontent.com/mphinance/alpha-playbooks/refs/heads/main/ghost-research-v1/templates/hud_template.html"
    print(f"Fetching remote template...")
    try:
        # Fetch remote template
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(TEMPLATE_URL)
            response.raise_for_status()
            template_str = response.text

        # Prepare Jinja2 Environment from string
        from jinja2 import Template
        template = Template(template_str)
        
        # Prepare context
        context = data.copy()
        context['ticker_first'] = data['ticker'][0] if data['ticker'] else '?'
        context['raw_json_data'] = json.dumps(data)
        context['chart_data_json'] = json.dumps(data.get('chart_data', []))
        context['ema_data_json'] = json.dumps(data.get('ema_data', {}))
        
        html = template.render(**context)
        
        out_html = f"{data['ticker']}_Alpha.html"
        with open(out_html, 'w') as f:
            f.write(html)
        return out_html
    except Exception as e:
        print(f"Template Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Ghost Alpha Standalone")
    parser.add_argument('--ticker', type=str, required=True, help='Stock Ticker Symbol')
    args = parser.parse_args()
    data = fetch_ticker_data(args.ticker)
    if data:
        html_path = generate_html(data)
        if html_path: print(f"Alpha Dossier saved to: {html_path}")

if __name__ == "__main__": main()