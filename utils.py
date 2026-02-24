import pandas as pd
import numpy as np

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

def clean_dict(d):
    """Recursively remove NaNs and non-serializable objects from a dictionary."""
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
    """Formatting helper for large numbers."""
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
    """
    Calculates intrinsic value using a Multi-Model Consensus approach.
    Prioritizes Analyst Targets for growth/unprofitable stocks.
    Blends Graham, Lynch, and Analyst for value/profitable stocks.
    """
    eps = info.get('trailingEps', 0)
    bvps = info.get('bookValue', 0)
    current_price = float(current_price)
    
    # Safely get growth and targets
    rev_growth = info.get('revenueGrowth', 0)
    if rev_growth is None: rev_growth = 0
    
    analyst_target = info.get('targetMeanPrice')
    if analyst_target is None: analyst_target = 0
    else: analyst_target = float(analyst_target)

    # 1. Graham Number (Value)
    graham = 0
    if eps and bvps and eps > 0 and bvps > 0:
        try: graham = float(np.sqrt(22.5 * eps * bvps))
        except: pass
        
    # 2. Peter Lynch Fair Value (Growth at Reasonable Price)
    lynch = 0
    if eps and eps > 0 and rev_growth > 0:
        # Lynch Fair Value = PEG * Earnings * Growth. Assuming PEG=1 is fair.
        # Adjusted: Fair Value = Earnings * (Growth Rate * 100)
        lynch = eps * (rev_growth * 100)
        
    # Selection Logic
    is_profitable = eps is not None and eps > 0
    has_analyst = analyst_target > 0
    
    final_value = 0
    method_str = "UNKNOWN"
    used_methods = []
    
    if is_profitable:
        # Profitable: Average of valid metrics
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
        # Unprofitable / Growth
        if has_analyst:
            final_value = analyst_target
            method_str = "ANALYST CONSENSUS"
        elif rev_growth > 0.20:
            pass
            
    # Gap Calculation
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
