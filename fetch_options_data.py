import json
import os
import argparse
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from tradingview_ta import TA_Handler, Interval

from utils import *

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
    total_call_vol = 0
    total_put_vol = 0
    total_call_oi = 0
    total_put_oi = 0

    try:
        opt_chain_dates = stock.options
        if opt_chain_dates:
            def fetch_chain(exp):
                try:
                    chain = stock.option_chain(exp)
                    return chain.calls, chain.puts
                except:
                    return pd.DataFrame(), pd.DataFrame()

            with ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(fetch_chain, opt_chain_dates[:5]))
            
            for calls, puts in results:
                if not calls.empty:
                    total_call_vol += calls['volume'].fillna(0).sum()
                    total_call_oi += calls['openInterest'].fillna(0).sum()
                if not puts.empty:
                    total_put_vol += puts['volume'].fillna(0).sum()
                    total_put_oi += puts['openInterest'].fillna(0).sum()
                
            if results and not results[0][0].empty:
                nearest_calls = results[0][0]
                latest_close = df['Close'].iloc[-1]
                atm_iv = nearest_calls[(nearest_calls['strike'] >= latest_close * 0.95) & (nearest_calls['strike'] <= latest_close * 1.05)]
                if not atm_iv.empty:
                    iv = atm_iv['impliedVolatility'].mean() * 100
    except Exception as e:
        print(f"Error fetching options: {e}")
    
    hist_month = df.iloc[-21:]
    high_m, low_m, close_m = hist_month['High'].max(), hist_month['Low'].min(), hist_month['Close'].iloc[-1]
    pp = (high_m + low_m + close_m) / 3
    
    hist_1y = df.iloc[-252:]
    h52, l52 = hist_1y['High'].max(), hist_1y['Low'].min()
    diff = h52 - l52
    
    latest = df.iloc[-1]

    fundamentals = {
        'insiders': [],
        'news': [],
        'info': {},
        'calendar': {}
    }

    def fetch_fundamental_component(component):
        try:
            if component == 'insiders':
                return 'insiders', stock.insider_transactions
            elif component == 'news':
                return 'news', stock.news
            elif component == 'info':
                return 'info', stock.info
            elif component == 'calendar':
                return 'calendar', stock.calendar
        except Exception as e:
            return component, None

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_fundamental_component, c) for c in ['insiders', 'news', 'info', 'calendar']]
        for future in futures:
            key, result = future.result()
            if result is not None:
                fundamentals[key] = result

    insider_data = []
    if isinstance(fundamentals['insiders'], pd.DataFrame) and not fundamentals['insiders'].empty:
        df_insiders = fundamentals['insiders'].reset_index()
        for _, row in df_insiders.head(5).iterrows():
            try:
                date_val = row.get('Start Date') or row.get('Date')
                date_str = date_val.strftime('%Y-%m-%d') if isinstance(date_val, pd.Timestamp) else str(date_val)
                val = row.get('Value')
                value_str = format_large_number(val) if isinstance(val, (int, float)) else str(val)

                insider_data.append({
                    "date": date_str,
                    "insider": row.get('Insider', 'Unknown'),
                    "type": row.get('Transaction', 'Unknown'),
                    "value": value_str
                })
            except Exception:
                continue
    
    tv_analysis = {}
    try:
        info = fundamentals.get('info', {})
        exchange_map = {
            'NMS': 'NASDAQ',
            'NYQ': 'NYSE',
            'NGM': 'NASDAQ',
            'ASE': 'AMEX',
            'PCX': 'ARCA'
        }
        raw_exchange = info.get('exchange', 'NMS')
        exchange = exchange_map.get(raw_exchange, 'NASDAQ')
        screener = "america"
        
        handler = TA_Handler(
            symbol=ticker,
            screener=screener,
            exchange=exchange,
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        
        tv_analysis = {
            "summary": analysis.summary,
            "oscillators": analysis.oscillators,
            "moving_averages": analysis.moving_averages,
            "indicators": analysis.indicators 
        }
    except Exception as e:
        tv_analysis = {"summary": {"RECOMMENDATION": "UNAVAILABLE"}}

    supply_chain_claims = []

    info = fundamentals['info']
    sec_ops = (
        f"{info.get('longName', ticker)} // {info.get('sector', 'N/A')} [{info.get('industry', 'N/A')}]. "
        f"Mkt Cap: {format_large_number(info.get('marketCap'))}. "
        f"Rev Growth: {info.get('revenueGrowth', 0)*100 if info.get('revenueGrowth') else 0:.1f}%. "
        f"PM: {info.get('profitMargins', 0)*100 if info.get('profitMargins') else 0:.1f}%."
    )
    
    sec_risks = (
        f"Beta: {info.get('beta', 'N/A')}. "
        f"Range(52W): {info.get('fiftyTwoWeekLow', 0)} - {info.get('fiftyTwoWeekHigh', 0)}. "
        f"Analyst Tgt: {info.get('targetMeanPrice', 'N/A')}."
    )

    geo = {
        "site": f"{info.get('city', 'Unknown')}, {info.get('country', 'Unknown')}",
        "coords": info.get('website', 'N/A'),  
        "score": 0.0,
        "observations": [{"period": "Current", "desc": "Headquarters location."}]
    }

    chart_data = []
    ema_data = { "8": [], "21": [], "34": [], "55": [], "89": [] }
    
    try:
        hist_data = df.tail(400).copy().reset_index()
        for _, row in hist_data.iterrows():
            d_val = row['Date']
            d_str = d_val.strftime('%Y-%m-%d') if pd.notnull(d_val) else ""
            
            if d_str:
                chart_data.append({
                    "time": d_str,
                    "open": round(row['Open'], 2),
                    "high": round(row['High'], 2),
                    "low": round(row['Low'], 2),
                    "close": round(row['Close'], 2)
                })
                
                for span in ["8", "21", "34", "55", "89"]:
                    val = row.get(f"EMA_{span}")
                    if val is not None and not np.isnan(val):
                        ema_data[span].append({
                            "time": d_str,
                            "value": round(float(val), 2)
                        })
    except Exception as e:
        print(f"Error preparing chart data: {e}")

    val_result = calculate_intrinsic_value(info, latest['Close'])
    
    valuation_status = val_result['status']
    avg_value = val_result['target_price']
    valuation_gap = val_result['gap_pct']
    method_used = val_result['method']

    prev_close = df['Close'].iloc[-2] if len(df) > 1 else latest['Close']
    price_change = latest['Close'] - prev_close
    price_change_pct = (price_change / prev_close) * 100
    
    iv_val = iv
    iv_rank = 25.0
    iv_percentile = 30.0
    
    def get_trend_strength(p, ema8, ema21, ema34):
        if p > ema8 > ema21 > ema34: return "Strong"
        if p > ema21: return "Weak"
        if p < ema34: return "Bear"
        return "Soft"

    trend_short = get_trend_strength(latest['Close'], latest['EMA_8'], latest['EMA_21'], latest['EMA_34'])
    trend_med = "Strong" if latest['Close'] > sma_50_val else "Soft"
    trend_long = "Strong" if latest['Close'] > sma_200_val else "Bear"
    
    expected_moves = []
    days_out = [7, 14, 30, 60]
    for d in days_out:
        move = latest['Close'] * (iv_val / 100) * np.sqrt(d / 365)
        exp_date = (datetime.now() + pd.Timedelta(days=d)).strftime('%m/%d/%y')
        expected_moves.append({
            "expiration": exp_date,
            "expectedMove": round(move, 2),
            "expectedRange": f"{round(latest['Close'] - move, 2)} - {round(latest['Close'] + move, 2)}",
            "iv": round(iv_val, 1)
        })

    pc_ratio_vol = total_put_vol / total_call_vol if total_call_vol > 0 else 0
    pc_ratio_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
    
    dashboard_data = {
        "ticker": ticker,
        "companyName": info.get('longName', ticker),
        "currentPrice": round(float(latest['Close']), 2),
        "priceChange": round(float(price_change), 2),
        "priceChangePct": round(float(price_change_pct), 2),
        "timestamp": datetime.now().strftime("%m/%d/%y %H:%M %Z"),
        "postMarketStr": f"Post-Market: ${round(float(latest['Close']), 2)} (0.00)",
        "impliedVolatility": round(float(iv_val), 2),
        "historicVolatility": round(float(hv.iloc[-1]), 2),
        "ivRank": iv_rank,
        "ivPercentile": iv_percentile,
        "iv5dAvg": round(float(iv_val), 2),
        "iv1mAvg": round(float(iv_val), 2),
        "iv3mLow": 0, "iv3mLowDate": "N/A",
        "iv3mHigh": 0, "iv3mHighDate": "N/A",
        "iv52wLow": 0, "iv52wLowDate": "N/A",
        "iv52wHigh": 0, "iv52wHighDate": "N/A",
        "trendOverall": "Bullish" if latest['Close'] > sma_50_val else "Bearish",
        "trendShort": trend_short,
        "trendMed": trend_med,
        "trendLong": trend_long,
        "movAvg20d": round(float(df['Close'].rolling(20).mean().iloc[-1]), 2),
        "movAvg50d": round(float(sma_50_val), 2),
        "movAvg100d": round(float(df['Close'].rolling(100).mean().iloc[-1]), 2),
        "movAvgChange20d": 0.0, "movAvgChange50d": 0.0, "movAvgChange100d": 0.0,
        "atr20d": 5.0, 
        "rsi20d": round(float(calculate_rsi(df['Close'], 20).iloc[-1]), 2),
        "trendSeekerSignal": "WAIT" if trend_short == "Soft" else "BUY" if "Strong" in trend_short else "SELL",
        "low52w": round(float(l52), 2), "low52wDate": "1Y Low",
        "high52w": round(float(h52), 2), "high52wDate": "1Y High",
        "expectedMoves": expected_moves,
        "volumeStats": {
            "callVolume": int(total_call_vol), "putVolume": int(total_put_vol), "totalVolume": int(total_call_vol + total_put_vol), "pcRatioVol": round(pc_ratio_vol, 2),
            "callOpenInt": int(total_call_oi), "putOpenInt": int(total_put_oi), "totalOpenInt": int(total_call_oi + total_put_oi), "pcRatioOi": round(pc_ratio_oi, 2),
            "volChg5d": 0, "volChg1m": 0, "oiChg5d": 0, "oiChg1m": 0
        },
        "pcCharts": {
            "dates": [d.strftime('%m/%d') for d in df.index[-10:]],
            "stockPrices": [round(p, 2) for p in df['Close'].tail(10)],
            "volRatios": [round(pc_ratio_vol, 2)] * 10,
            "oiRatios": [round(pc_ratio_oi, 2)] * 10
        }
    }

    website = info.get('website', '')
    logo_url = info.get('logo_url', '')
    
    if not logo_url and website:
        try:
            domain = website.replace('http://', '').replace('https://', '').split('/')[0]
            logo_url = f"https://logo.clearbit.com/{domain}"
        except:
            logo_url = ""

    data = dashboard_data.copy()
    data.update({
        "logo_url": logo_url,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "chart_data": chart_data,
        "ema_data": ema_data,
        "market_snapshot": { 
            "price": round(float(latest['Close']), 2),
            "market_cap": format_large_number(info.get('marketCap')),
            "beta": info.get('beta', 'N/A'),
            "range_52w": f"{info.get('fiftyTwoWeekLow', 0)} - {info.get('fiftyTwoWeekHigh', 0)}",
            "analyst_target": info.get('targetMeanPrice', 'N/A')
        },
        "tradingview": tv_analysis,
        "technical_analysis": {
            "trend": {
                "outlook": "Bullish" if sma_50_val > sma_200_val else "Bearish",
                "sma_50": round(float(sma_50), 2) if not np.isnan(sma_50) else None,
                "sma_200": round(float(sma_200), 2) if not np.isnan(sma_200) else None,
                "crossover": "Golden Cross" if sma_50_val > sma_200_val else "Death Cross"
            },
            "ema": {
                "8": round(float(latest['EMA_8']), 2),
                "21": round(float(latest['EMA_21']), 2),
                "34": round(float(latest['EMA_34']), 2),
                "55": round(float(latest['EMA_55']), 2),
                "89": round(float(latest['EMA_89']), 2)
            },
            "volume": {
                "current": f"{int(latest['Volume']):,}",
                "avg_20d": f"{int(vol_avg.iloc[-1]):,}",
                "rel_vol": round(float(rel_vol.iloc[-1]), 2),
                "rel_vol_pct": min(100, int(rel_vol.iloc[-1] * 50)) 
            },
            "pivots": {
                "R2": round(pp + (high_m - low_m), 2),
                "R1": round((2 * pp) - low_m, 2),
                "PP": round(pp, 2),
                "S1": round((2 * pp) - high_m, 2),
                "S2": round(pp - (high_m - low_m), 2)
            },
            "fibonacci": {
                "100": round(h52, 2), "61.8": round(h52 - 0.382 * diff, 2),
                "50": round(h52 - 0.5 * diff, 2), "38.2": round(h52 - 0.618 * diff, 2), "0": round(l52, 2)
            },
            "oscillators": {
                "rsi_14": round(float(latest['RSI_14']), 2) if not np.isnan(latest['RSI_14']) else None,
                "adx_14": round(float(latest['ADX_14']), 2) if not np.isnan(latest['ADX_14']) else None,
                "macd_hist": round(float(latest['MACDh_12_26_9']), 2) if not np.isnan(latest['MACDh_12_26_9']) else None
            }
        },
        "volatility": { "hv_30d": round(float(hv.iloc[-1]), 2), "iv_current": round(float(iv), 2) },
        "insider_transactions": insider_data,
        "intel_feed": [],
        "supply_chain": { "claims": supply_chain_claims, "shipments": [] }, 
        "sec_insights": {
            "operations": sec_ops,
            "forward_looking": sec_risks
        },
        "geospatial": geo
    })

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
        v = i.get('value', '0').replace('$','').replace('M','000000').replace('K','000').replace(',','')
        try:
            val = float(v)
            if 'Purchase' in i.get('type',''): insider_sentiment += 1
            elif 'Sale' in i.get('type',''): insider_sentiment -= 1
        except: pass
        
    if insider_sentiment > 0: fund_score += 10
    elif insider_sentiment < 0: fund_score -= 5
    
    tgt = info.get('targetMeanPrice')
    if tgt and tgt > latest['Close']: fund_score += 10
    
    tech_score = max(0, min(100, tech_score))
    fund_score = max(0, min(100, fund_score))
    
    data["scores"] = {
        "technical": tech_score,
        "fundamental": fund_score,
        "grade": "A" if (tech_score+fund_score)/2 > 80 else "B" if (tech_score+fund_score)/2 > 60 else "C" if (tech_score+fund_score)/2 > 40 else "D"
    }
    
    data["valuation"] = {
        "status": valuation_status,
        "gap_pct": round(valuation_gap, 2),
        "target_price": round(avg_value, 2),
        "graham_num": val_result['details']['graham'],
        "lynch_value": val_result['details']['lynch'],
        "method": method_used
    }
    
    def generate_ai_narrative(d):
        t_score = d['scores']['technical']
        f_score = d['scores']['fundamental']
        trend = d['technical_analysis']['trend']['outlook']
        val_status = d['valuation']['status']
        val_gap = d['valuation']['gap_pct']
        
        narrative = f"<span class='text-neon-blue font-bold'>AI.SYNTHESIS // </span> <br>"
        narrative += f"Asset demonstrates a <span class='{'text-neon-green' if t_score > 60 else 'text-neon-red'}'>{'STRONG' if t_score > 70 else 'WEAK' if t_score < 40 else 'NEUTRAL'}</span> technical posture (Score: {t_score}/100) within a wider {trend} trend. "
        
        if val_status == "UNDERVALUED":
            narrative += f"Models suggest the asset is <span class='text-neon-green'>UNDERVALUED</span> by {abs(val_gap)}%, implying a significant margin of safety. "
        elif val_status == "OVERVALUED":
            narrative += f"However, valuation models indicate the asset is <span class='text-neon-red'>OVERVALUED</span> by ~{val_gap}%; price may be extended beyond fundamentals. "
        else:
            narrative += f"Asset appears fairly valued relative to growth and book value. "
            
        narrative += "<br><br><span class='text-gray-400 font-bold'>RISK.PROFILE // </span>"
        if d['volatility']['iv_current'] > d['volatility']['hv_30d']:
             narrative += "Implied volatility exceeds historical norms, expecting turbulence. "
        else:
             narrative += "Volatility compression detected; potential for range expansion. "
             
        narrative += f"<br><br><span class='text-neon-amber font-bold'>VERDICT // </span>{'ACCUMULATE on Dips' if t_score > 60 and val_status != 'OVERVALUED' else 'DISTRIBUTE into Strength' if t_score < 40 else 'WAIT for Validation'}."
        
        return narrative

    data['ai_analysis'] = generate_ai_narrative(data)
    data['ghost_analysis'] = data['ai_analysis']

    return clean_dict(data)

def save_json(data, ticker):
    ticker_dir = f"reports/{ticker}"
    os.makedirs(ticker_dir, exist_ok=True)
    out_json = f"{ticker_dir}/{datetime.now().strftime('%Y-%m-%d')}.json"
    latest_json = f"{ticker_dir}/latest.json"
    
    min_data = data.copy()
    min_data.pop('chart_data', None)
    min_data.pop('ema_data', None)
    
    with open(out_json, 'w') as f:
        json.dump(min_data, f, indent=2)
    with open(latest_json, 'w') as f:
        json.dump(min_data, f, indent=2)
        
    return out_json

def save_series_json(ticker, chart_data, ema_data):
    ticker_dir = f"reports/{ticker}"
    os.makedirs(ticker_dir, exist_ok=True)
    out_json = f"{ticker_dir}/{datetime.now().strftime('%Y-%m-%d')}_series.json"
    latest_series = f"{ticker_dir}/latest_series.json"
    series_data = {
        "ticker": ticker,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "chart_data": chart_data,
        "ema_data": ema_data
    }
    with open(out_json, 'w') as f:
        json.dump(series_data, f, indent=2)
    with open(latest_series, 'w') as f:
        json.dump(series_data, f, indent=2)
        
    print(f"Series Data saved to: {out_json}")
    return out_json

def main():
    parser = argparse.ArgumentParser(description="Fetch Options Playbook Data")
    parser.add_argument('--ticker', type=str, required=True, help='Stock Ticker Symbol')
    args = parser.parse_args()

    data = fetch_ticker_data(args.ticker)
    if data:
        json_path = save_json(data, args.ticker)
        print(f"JSON Data saved to: {json_path}")
        save_series_json(args.ticker, data.get('chart_data', []), data.get('ema_data', {}))

if __name__ == "__main__":
    main()
