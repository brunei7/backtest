# nayrafa_engine.py - Nayrafa AlgoTrade V3 Institutional Scanner (FIXED SYNTAX & VECTORIZED)
import json
import os
import time
import sys
import math
from datetime import datetime
import pandas as pd
import numpy as np
from pybit.unified_trading import HTTP

# ==================== HARDCORE CONFIG ====================
API_KEY = "3KutSBJdpR9U3cGBB2"
API_SECRET = "8bmwecJDavuvqA6XKnt8xU6xUn56zdbdWOrU"
TESTNET_MODE = False

ENTRY_MARGIN = 8.0
LEVERAGE = 10
TP_RR = 2.5
LTF = "5"
HTF = "15"
COOLDOWN_BARS = 10

MAX_ACTIVE_POSITIONS = 3

# ==================== ENTRY CONFIG ====================
MIN_SCORE_FOR_ENTRY = 5
ATR_MULTIPLIER_SL = 2.0
MIN_RR_RATIO = 1.5
REJECT_COOLDOWN = 120

# 100 Koin Populer
AVAILABLE_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT", "NEARUSDT",
    "FTMUSDT", "OPUSDT", "ARBUSDT", "SUIUSDT", "APTUSDT",
    "LTCUSDT", "STXUSDT", "INJUSDT", "TIAUSDT", "FETUSDT",
    "RNDRUSDT", "WLDUSDT", "FILUSDT", "ATOMUSDT", "IMXUSDT",
    "GALAUSDT", "SEIUSDT", "ORDIUSDT", "ONDOUSDT", "JUPUSDT",
    "ENAUSDT", "NOTUSDT", "TONUSDT", "TRXUSDT", "BCHUSDT",
    "SANDUSDT", "MANAUSDT", "THETAUSDT", "AXSUSDT", "AAVEUSDT",
    "DOGEUSDT", "SHIBUSDT", "1000PEPEUSDT", "WIFUSDT", "BONKUSDT",
    "FLOKIUSDT", "BOMEUSDT", "POPCATUSDT", "BRETTUSDT", "MEWUSDT",
    "STRKUSDT", "DYMUSDT", "PYTHUSDT", "MANTAUSDT", "JTOUSDT",
    "CRVUSDT", "SNXUSDT", "GRTUSDT", "CHZUSDT", "ENSUSDT",
    "MNTUSDT", "LDOUSDT", "ARUSDT", "MKRUSDT", "COMPUSDT",
    "ALGOUSDT", "YFIUSDT", "KASUSDT", "RUNEUSDT", "ICPUSDT",
    "TAOUSDT", "BBUSDT", "REZUSDT", "OMNIUSDT", "WUSDT",
    "TNSRUSDT", "ETHFIUSDT", "ALTUSDT", "MEMEUSDT", "BLURUSDT",
    "BIGTIMEUSDT", "ACEUSDT", "NFPUSDT", "AIUSDT", "XAIUSDT",
    "PORTALUSDT", "PIXELUSDT", "IDUSDT", "CYBERUSDT", "ARKMUSDT",
    "PENDLEUSDT", "AGIXUSDT", "OCEANUSDT", "PHBUSDT", "ZETAUSDT"
]

# ==================== FIX SSL ====================
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import ssl
import requests
from requests.adapters import HTTPAdapter

class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_version'] = ssl.PROTOCOL_TLS
        kwargs['cert_reqs'] = ssl.CERT_NONE
        kwargs['assert_hostname'] = False
        return super().init_poolmanager(*args, **kwargs)

# ==================== COLOR SETUP ====================
try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    C_GREEN = Fore.GREEN
    C_RED = Fore.RED
    C_YELLOW = Fore.YELLOW
    C_CYAN = Fore.CYAN
    C_MAGENTA = Fore.MAGENTA
    C_WHITE = Fore.WHITE
    C_BLUE = Fore.BLUE
    C_RESET = Fore.RESET
    C_BOLD = Style.BRIGHT
    C_DIM = Style.DIM
    C_BRIGHT_GREEN = Fore.LIGHTGREEN_EX
    C_BRIGHT_RED = Fore.LIGHTRED_EX
    C_BRIGHT_YELLOW = Fore.LIGHTYELLOW_EX
    C_BRIGHT_CYAN = Fore.LIGHTCYAN_EX
    C_BRIGHT_MAGENTA = Fore.LIGHTMAGENTA_EX
    C_BRIGHT_WHITE = Fore.LIGHTWHITE_EX
except:
    C_GREEN, C_RED, C_YELLOW = '\033[92m', '\033[91m', '\033[93m'
    C_CYAN, C_MAGENTA, C_WHITE = '\033[96m', '\033[95m', '\033[97m'
    C_BLUE, C_RESET, C_BOLD, C_DIM = '\033[94m', '\033[0m', '\033[1m', '\033[2m'
    C_BRIGHT_GREEN, C_BRIGHT_RED = '\033[92;1m', '\033[91;1m'
    C_BRIGHT_YELLOW, C_BRIGHT_CYAN = '\033[93;1m', '\033[96;1m'
    C_BRIGHT_MAGENTA, C_BRIGHT_WHITE = '\033[95;1m', '\033[97;1m'

def get_indicator_icon(is_valid):
    return f"{C_BRIGHT_GREEN}✅{C_RESET}" if is_valid else f"{C_BRIGHT_RED}❌{C_RESET}"

# ==================== BYBIT API ====================
session = HTTP(
    testnet=TESTNET_MODE,
    api_key=API_KEY,
    api_secret=API_SECRET,
)
try:
    session._session.mount('https://', SSLAdapter())
    session._session.verify = False
    session._session.timeout = 15
except:
    pass

# ==================== KURS IDR REAL-TIME ====================
USD_TO_IDR = 16000

def update_usd_to_idr():
    global USD_TO_IDR
    try:
        url = "https://api.frankfurter.app/latest?from=USD&to=IDR"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if 'rates' in data and 'IDR' in data['rates']:
                USD_TO_IDR = data['rates']['IDR']
                return USD_TO_IDR
    except:
        pass
    return USD_TO_IDR

update_usd_to_idr()

def get_total_asset():
    try:
        res = session.get_wallet_balance(accountType="UNIFIED")
        if res and 'result' in res and res['result']['list']:
            return float(res['result']['list'][0]['totalEquity'])
    except:
        pass
    return 0.0

def get_position_pnl(symbol):
    try:
        res = session.get_positions(category="linear", symbol=symbol)
        if not res or 'result' not in res or not res['result']['list']:
            return None
        pos = res['result']['list'][0]
        size = float(pos.get('size', 0))
        if size == 0:
            return None
        return {
            'size': size,
            'entry_price': float(pos.get('avgPrice', 0)),
            'side': pos.get('side', 'Unknown'), 
            'unrealised_pnl': float(pos.get('unrealisedPnl', 0)),
            'unrealised_pnl_percent': float(pos.get('unrealisedPnlPercent', 0)),
            'leverage': float(pos.get('leverage', 0)),
            'tp_price': float(pos.get('takeProfit', 0)) if pos.get('takeProfit') else 0,
            'sl_price': float(pos.get('stopLoss', 0)) if pos.get('stopLoss') else 0,
            'current_price': float(pos.get('markPrice', 0)) if pos.get('markPrice') else 0
        }
    except:
        return None

# ==================== CACHE ====================
CACHE_FILE = 'kline_cache_nayrafa.json'
cache_data = {}
cache_time = {}
price_cache = {}
last_request_time = 0
min_request_interval = 1.0 

def load_cache():
    global cache_data, cache_time
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                cache_data = data.get('data', {})
                cache_time = data.get('time', {})
        except: pass

def save_cache():
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({'data': cache_data, 'time': cache_time}, f)
    except: pass

load_cache()

def wait_for_rate_limit():
    global last_request_time
    now = time.time()
    elapsed = now - last_request_time
    if elapsed < min_request_interval:
        time.sleep(min_request_interval - elapsed)
    last_request_time = time.time()

def get_kline_data(symbol, interval, limit=100):
    cache_key = f"{symbol}_{interval}_{limit}"
    now = time.time()
    if cache_key in cache_data and (now - cache_time.get(cache_key, 0)) < 120:
        return cache_data[cache_key]
    wait_for_rate_limit()
    try:
        response = session.get_kline(category="linear", symbol=symbol, interval=interval, limit=limit)
        data = response['result']['list'][::-1]
        cache_data[cache_key] = data
        cache_time[cache_key] = now
        save_cache()
        return data
    except:
        return cache_data.get(cache_key, [])

def get_current_price(symbol):
    now = time.time()
    if symbol in price_cache and (now - price_cache.get(f'{symbol}_time', 0)) < 5:
        return price_cache[symbol]
    wait_for_rate_limit()
    try:
        res = session.get_tickers(category="linear", symbol=symbol)
        price = float(res['result']['list'][0]['lastPrice'])
        price_cache[symbol] = price
        price_cache[f'{symbol}_time'] = now
        return price
    except:
        return price_cache.get(symbol, 0)

def check_open_position(symbol):
    try:
        res = session.get_positions(category="linear", symbol=symbol)
        size = float(res['result']['list'][0]['size'])
        return size > 0
    except:
        return False

def get_instrument_info(symbol):
    try:
        res = session.get_instruments_info(category="linear", symbol=symbol)
        lot = res['result']['list'][0]['lotSizeFilter']
        return {
            'min_qty': float(lot.get('minOrderQty', 0.001)),
            'max_qty': float(lot.get('maxOrderQty', 1000000)),
            'qty_step': float(lot.get('qtyStep', 0.001))
        }
    except:
        return {'min_qty': 0.001, 'max_qty': 1000000, 'qty_step': 0.001}

# ==================== NAYRAFA ALGOTRADE ENGINE ====================
def format_df(raw_data):
    if not raw_data:
        return pd.DataFrame()
    df = pd.DataFrame(raw_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
    for col in ['timestamp', 'open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col])
    return df

def calculate_supertrend(df, period=10, mult=3.0):
    hl2 = (df['high'] + df['low']) / 2
    atr = df['tr'].rolling(period).mean().bfill().fillna(0.0001)
    
    basic_ub = hl2 + mult * atr
    basic_lb = hl2 - mult * atr

    close_arr = df['close'].values
    ub = np.zeros(len(df))
    lb = np.zeros(len(df))
    st = np.zeros(len(df))
    trend = np.ones(len(df))

    for i in range(1, len(df)):
        ub[i] = basic_ub.iloc[i] if basic_ub.iloc[i] < ub[i-1] or close_arr[i-1] > ub[i-1] else ub[i-1]
        lb[i] = basic_lb.iloc[i] if basic_lb.iloc[i] > lb[i-1] or close_arr[i-1] < lb[i-1] else lb[i-1]

        if st[i-1] == ub[i-1] and close_arr[i] < ub[i]:
            trend[i] = -1
        elif st[i-1] == lb[i-1] and close_arr[i] > lb[i]:
            trend[i] = 1
        elif st[i-1] == ub[i-1] and close_arr[i] > ub[i]:
            trend[i] = 1
        elif st[i-1] == lb[i-1] and close_arr[i] < lb[i]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]

        st[i] = lb[i] if trend[i] == 1 else ub[i]

    return pd.Series(st, index=df.index), pd.Series(trend, index=df.index)

def analyze_nayrafa_engine(raw_ltf):
    if not raw_ltf: return pd.DataFrame()
    df = format_df(raw_ltf)
    if df.empty: return pd.DataFrame()

    # 1. Volatility Base (ATR & TR)
    hl = df['high'] - df['low']
    hc = np.abs(df['high'] - df['close'].shift(1))
    lc = np.abs(df['low'] - df['close'].shift(1))
    df['tr'] = np.maximum(hl, np.maximum(hc, lc))
    df['tr'] = df['tr'].replace(0, 0.000001)
    df['atr'] = df['tr'].rolling(14).mean()
    df['atr_sma'] = df['atr'].rolling(14).mean()
    df['body'] = abs(df['close'] - df['open'])

    # 2. Supertrend Logic
    df['st_val'], df['st_trend'] = calculate_supertrend(df, period=10, mult=3.0)

    # 3. Bollinger Bands Logic
    df['bb_sma'] = df['close'].rolling(100).mean()
    df['bb_std'] = df['close'].rolling(100).std()
    df['bb_upper'] = df['bb_sma'] + (2.0 * df['bb_std'])
    df['bb_lower'] = df['bb_sma'] - (2.0 * df['bb_std'])

    # 4. RSI Logic
    delta = df['close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(7).mean()
    avg_loss = pd.Series(loss).rolling(7).mean()
    rs = avg_gain / np.where(avg_loss == 0, 1, avg_loss)
    df['rsi'] = 100 - (100 / (1 + rs))

    # 5. EMA Logic
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean()

    # 6. Pivot/Structure Logic (Lookback 20)
    df['recent_high'] = df['high'].rolling(20).max().shift(1)
    df['recent_low'] = df['low'].rolling(20).min().shift(1)

    # 7. Engulfing / Candle Pattern
    df['engulfing_bull'] = (df['close'] > df['open']) & (df['close'] > df['close'].shift(1)) & (df['open'] < df['open'].shift(1))
    df['engulfing_bear'] = (df['close'] < df['open']) & (df['close'] < df['close'].shift(1)) & (df['open'] > df['open'].shift(1))

    # 8. Volume Spike
    df['vol_ma'] = df['volume'].rolling(20).mean()
    df['vol_surge'] = df['volume'] > (df['vol_ma'] * 1.2)

    # --- 9 NAYRAFA CONFLUENCE FACTORS ---
    # LONG FACTORS
    df['i1_l'] = df['st_trend'] == 1                              # 1. Supertrend Bullish
    df['i2_l'] = df['close'] > df['bb_sma']                       # 2. Price > BB Middle
    df['i3_l'] = df['atr'] > df['atr_sma']                        # 3. High Volatility (Not Sideways)
    df['i4_l'] = df['rsi'] > 50                                   # 4. RSI Bullish Momentum
    df['i5_l'] = df['close'] > df['ema200']                       # 5. Above Macro EMA 200
    df['i6_l'] = df['close'] > df['recent_high']                  # 6. Breakout recent resistance
    df['i7_l'] = df['engulfing_bull'].rolling(3).max() == 1       # 7. Bullish Pattern
    df['i8_l'] = df['vol_surge']                                  # 8. Volume Spike
    df['i9_l'] = df['low'] <= df['st_val'] * 1.01                 # 9. Retest / Pullback to ST support

    # SHORT FACTORS
    df['i1_s'] = df['st_trend'] == -1
    df['i2_s'] = df['close'] < df['bb_sma']
    df['i3_s'] = df['atr'] > df['atr_sma']
    df['i4_s'] = df['rsi'] < 50
    df['i5_s'] = df['close'] < df['ema200']
    df['i6_s'] = df['close'] < df['recent_low']
    df['i7_s'] = df['engulfing_bear'].rolling(3).max() == 1
    df['i8_s'] = df['vol_surge']
    df['i9_s'] = df['high'] >= df['st_val'] * 0.99

    # Total Scoring
    df['long_score'] = df[['i1_l','i2_l','i3_l','i4_l','i5_l','i6_l','i7_l','i8_l','i9_l']].astype(int).sum(axis=1)
    df['short_score'] = df[['i1_s','i2_s','i3_s','i4_s','i5_s','i6_s','i7_s','i8_s','i9_s']].astype(int).sum(axis=1)

    # Validasi Struktur
    df['longStructureValid'] = df['st_trend'] == 1
    df['shortStructureValid'] = df['st_trend'] == -1
    
    df['longHTFTouch'] = df['low'] <= df['bb_sma'] * 1.002
    df['shortHTFTouch'] = df['high'] >= df['bb_sma'] * 0.998

    return df

def calculate_sltp_nayrafa(df, entry_price, side):
    if df.empty:
        if side == 'Buy': return entry_price * 0.97, entry_price * 1.04
        else: return entry_price * 1.03, entry_price * 0.96
    
    atr = df['atr'].iloc[-1] if 'atr' in df.columns else entry_price * 0.02
    
    if side == 'Buy':
        # SL berbasis Supertrend ATR
        st_val = df['st_val'].iloc[-1]
        sl = st_val - (atr * 0.5) if st_val > 0 else entry_price - (atr * ATR_MULTIPLIER_SL)
        if sl >= entry_price or sl <= 0: sl = entry_price - (atr * ATR_MULTIPLIER_SL)
        risk = entry_price - sl
        tp = entry_price + (risk * TP_RR)
    else:
        st_val = df['st_val'].iloc[-1]
        sl = st_val + (atr * 0.5) if st_val > 0 else entry_price + (atr * ATR_MULTIPLIER_SL)
        if sl <= entry_price or sl <= 0: sl = entry_price + (atr * ATR_MULTIPLIER_SL)
        risk = sl - entry_price
        tp = entry_price - (risk * TP_RR)

    return round(sl, 8), round(tp, 8)

# ==================== STATE & DASHBOARD ====================
STATE_FILE = 'state_multi_nayrafa.json'

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f: return json.load(f)
        except: pass
    return {}

def save_state(states):
    with open(STATE_FILE, 'w') as f: json.dump(states, f, indent=4)

def init_state():
    return {
        "longState": 0, "shortState": 0,
        "lastExitTime": 0, "in_position": False,
        "daily_pnl": 0.0, "total_trades": 0,
        "entry_price": None, "tp_price": None, "sl_price": None,
        "position_side": None, "long_filters": "", "short_filters": "", "last_score": 0,
        "entry_ready": False, "entry_side": None, "entry_price_target": 0,
        "entry_sl": 0, "entry_score": 0, "entry_tp": 0,
        "rejected_time": 0, "best_side": "N/A", "best_filters": ""
    }

def print_dashboard(states, current_sym, idx, total, cycle_time, spinner):
    dashboard = []
    mode_text = f"{C_BRIGHT_GREEN}TESTNET{C_RESET}" if TESTNET_MODE else f"{C_BRIGHT_RED}LIVE{C_RESET}"
    time_str = datetime.now().strftime('%H:%M:%S')
    
    dashboard.append(f"{C_CYAN}╔══════════════════════════════════════════════════════════════════════╗{C_RESET}")
    dashboard.append(f"{C_CYAN}║  {C_BRIGHT_MAGENTA}{C_BOLD}🚀 NAYRAFA ALGOTRADE V3 SCANNER{C_RESET}     {C_BRIGHT_YELLOW}Mode: {mode_text}{C_RESET}  {C_BRIGHT_YELLOW}⌚ {time_str}{C_RESET}  {C_CYAN}║{C_RESET}")
    dashboard.append(f"{C_CYAN}╠══════════════════════════════════════════════════════════════════════╣{C_RESET}")
    dashboard.append(f"║  {C_BRIGHT_GREEN}{spinner}{C_RESET}  {C_DIM}Scan:{C_RESET} {C_BRIGHT_YELLOW}{current_sym:<10}{C_RESET}  {idx:03d}/{total}  {C_DIM}| {cycle_time:.1f}s{C_RESET}  {C_CYAN}║{C_RESET}")
    dashboard.append(f"{C_CYAN}╠══════════════════════════════════════════════════════════════════════╣{C_RESET}")
    
    dashboard.append(f"║  {C_BRIGHT_CYAN}{C_BOLD}📊 9 NAYRAFA FACTOR:{C_RESET} {C_BRIGHT_GREEN}1.SuperTrnd{C_RESET} {C_BRIGHT_YELLOW}2.BB Trend {C_RESET} {C_BRIGHT_CYAN}3.ATR Filter{C_RESET} {C_BRIGHT_MAGENTA}4.RSI Mom   ║{C_RESET}")
    dashboard.append(f"║  {C_BRIGHT_GREEN}5.EMA 200  {C_RESET}{C_BRIGHT_YELLOW}6.BOS/Break{C_RESET} {C_BRIGHT_RED}7.Engulfing{C_RESET} {C_BRIGHT_CYAN}8.Vol Surge{C_RESET} {C_BRIGHT_WHITE}9.Pullback  ║{C_RESET}")
    dashboard.append(f"{C_CYAN}╠══════════════════════════════════════════════════════════════════════╣{C_RESET}")
    
    active = []
    for sym, s in states.items():
        if s.get('in_position'): active.append((sym, s))
    
    dashboard.append(f"║  {C_BRIGHT_MAGENTA}{C_BOLD}🔴 POSISI AKTIF ({len(active)}/{MAX_ACTIVE_POSITIONS}){C_RESET}  {C_CYAN}║{C_RESET}")
    if not active:
        dashboard.append(f"║    {C_DIM}Menunggu...{C_RESET}  {C_CYAN}║{C_RESET}")
    else:
        for sym, s in active[:3]:
            pos_info = get_position_pnl(sym)
            if pos_info:
                usdt_pnl = pos_info['unrealised_pnl']
                side = pos_info['side']
                entry = pos_info['entry_price']
                tp = pos_info.get('tp_price')
                sl = pos_info.get('sl_price')
                current_price = pos_info.get('current_price', 0)
            else:
                side = s.get('position_side', 'Unknown')
                entry = s.get('entry_price', 0)
                tp = s.get('tp_price')
                sl = s.get('sl_price')
                current_price = get_current_price(sym) or 0
                usdt_pnl = 0

            if entry is not None and entry > 0 and current_price > 0:
                if side in ['Buy', 'LONG']: pct = ((current_price - entry) / entry) * 100
                else: pct = ((entry - current_price) / entry) * 100
                if not pos_info: usdt_pnl = (ENTRY_MARGIN * LEVERAGE) * (pct / 100)
            else:
                pct = 0
            
            tp = tp if tp is not None else 0.0
            sl = sl if sl is not None else 0.0
            
            if side and entry > 0:
                idr_pnl = usdt_pnl * USD_TO_IDR
                color = C_BRIGHT_GREEN if usdt_pnl > 0 else C_BRIGHT_RED
                side_color = C_BRIGHT_GREEN if side in ['Buy', 'LONG'] else C_BRIGHT_RED
                dashboard.append(f"║    {side_color}{side:<4}{C_RESET} {C_BRIGHT_CYAN}{sym:<8}{C_RESET} | {color}{usdt_pnl:+.2f}$ ({idr_pnl:+,.0f} IDR) ({pct:+.2f}%){C_RESET}  {C_CYAN}║{C_RESET}")
                dashboard.append(f"║      {C_DIM}Live:{C_RESET} {C_WHITE}{current_price:.8f}{C_RESET}  {C_DIM}Entry:{C_RESET} {entry:.8f}  {C_CYAN}║{C_RESET}")
                dashboard.append(f"║      {C_BRIGHT_GREEN}TP: {tp:.8f}{C_RESET}  {C_BRIGHT_RED}SL: {sl:.8f}{C_RESET}  {C_CYAN}║{C_RESET}")
                if s.get('long_filters') and side in ['Buy', 'LONG']: dashboard.append(f"║      ↳ NYRF: {s.get('long_filters')}  {C_CYAN}║{C_RESET}")
                elif s.get('short_filters') and side in ['Sell', 'SHORT']: dashboard.append(f"║      ↳ NYRF: {s.get('short_filters')}  {C_CYAN}║{C_RESET}")
            else:
                dashboard.append(f"║    {C_YELLOW}⚠️ Data posisi tidak lengkap untuk {sym}{C_RESET}  {C_CYAN}║{C_RESET}")
    
    dashboard.append(f"{C_CYAN}╠──────────────────────────────────────────────────────────────────────╣{C_RESET}")
    dashboard.append(f"║  {C_BRIGHT_CYAN}{C_BOLD}📈 ANTREAN MOMENTUM NAYRAFA ALGO{C_RESET}  {C_CYAN}║{C_RESET}")
    all_scores = []
    for sym, s in states.items():
        score = s.get('last_score', 0)
        if score > 0:
            best_side = s.get('best_side', 'N/A')
            side_label = f"{C_BRIGHT_GREEN}LONG{C_RESET}" if best_side == 'LONG' else f"{C_BRIGHT_RED}SHORT{C_RESET}" if best_side == 'SHORT' else f"{C_DIM}N/A{C_RESET}"
            filters = s.get('long_filters', '') if best_side == 'LONG' else s.get('short_filters', '')
            armed_status = (s.get('longState') == 1 or s.get('shortState') == 1)
            all_scores.append((sym, side_label, score, filters, armed_status))
            
    semua_antrean = sorted(all_scores, key=lambda x: x[2], reverse=True)[:10]
    if semua_antrean:
        for rank, (sym, side_label, score, filters, armed_status) in enumerate(semua_antrean, 1):
            status_text = f"{C_BRIGHT_GREEN}✅ BREAKOUT/RETEST VALID{C_RESET}" if armed_status else f"{C_YELLOW}🔒 MENUNGGU KONFIRMASI{C_RESET}"
            dashboard.append(f"║    {rank}. {C_BRIGHT_CYAN}{sym:<8}{C_RESET} | {side_label:<5} | {C_BRIGHT_YELLOW}SKOR: {score}/9{C_RESET} | {status_text}  {C_CYAN}║{C_RESET}")
            if filters: dashboard.append(f"║      ↳ {filters}  {C_CYAN}║{C_RESET}")
    else:
        dashboard.append(f"║    {C_DIM}Belum ada sinyal Algo yang tervalidasi.{C_RESET}  {C_CYAN}║{C_RESET}")
    
    dashboard.append(f"{C_CYAN}╠══════════════════════════════════════════════════════════════════════╣{C_RESET}")
    
    realized_pnl = sum(s.get('daily_pnl', 0) for s in states.values())
    unrealized_pnl = sum((get_position_pnl(sym) or {}).get('unrealised_pnl', 0) for sym in states.keys())
    total_pnl = realized_pnl + unrealized_pnl
    total_asset_usd = get_total_asset()
    pnl_col = C_BRIGHT_GREEN if total_pnl > 0 else C_BRIGHT_RED if total_pnl < 0 else C_WHITE
    
    dashboard.append(f"║  {C_DIM}Trades:{C_RESET} {sum(s.get('total_trades', 0) for s in states.values())}  |  {C_DIM}Realized:{C_RESET} {pnl_col}{realized_pnl:+.2f}$ {C_RESET}  |  {C_DIM}Unrealized:{C_RESET} {pnl_col}{unrealized_pnl:+.2f}$ {C_RESET}  {C_CYAN}║{C_RESET}")
    dashboard.append(f"║  {C_DIM}Total P&L:{C_RESET} {pnl_col}{total_pnl:+.2f}$ ({total_pnl * USD_TO_IDR:+,.0f} IDR) {C_RESET} |  {C_DIM}Margin:{C_RESET} ${ENTRY_MARGIN:.2f} @ {LEVERAGE}x{C_RESET}  {C_CYAN}║{C_RESET}")
    dashboard.append(f"║  {C_BRIGHT_YELLOW}💰 TOTAL ASET:{C_RESET} {C_BRIGHT_GREEN}{total_asset_usd:,.2f} $ {C_RESET} ({C_BRIGHT_GREEN}{total_asset_usd * USD_TO_IDR:+,.0f} IDR{C_RESET})  {C_CYAN}║{C_RESET}")
    dashboard.append(f"{C_CYAN}╚══════════════════════════════════════════════════════════════════════╝{C_RESET}")
    
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.write("\n".join(dashboard) + "\n")
    sys.stdout.flush()

# ==================== MAIN ====================
def run():
    if not API_KEY:
        print("❌ API Key kosong!")
        return
    
    states = load_state()
    for sym in AVAILABLE_SYMBOLS:
        if sym not in states: states[sym] = init_state()
    
    print(f"{C_BRIGHT_GREEN}{C_BOLD}🚀 NAYRAFA ALGOTRADE V3 ENGINE START{C_RESET}")
    print(f"{C_DIM}Total: {len(AVAILABLE_SYMBOLS)} coins | Batch: 5 coins/cycle | Rate limit: 1.0s{C_RESET}")
    print(f"{C_DIM}Margin: ${ENTRY_MARGIN} | Leverage: {LEVERAGE}x | TP_RR: {TP_RR} | Kurs IDR: {USD_TO_IDR:,.0f}{C_RESET}")
    print(f"{C_DIM}Max aktif: {MAX_ACTIVE_POSITIONS} | Min Skor: {MIN_SCORE_FOR_ENTRY}/9 | SL logic: SuperTrend + ATR{C_RESET}")
    time.sleep(2)
    
    spinner, si, scan_index, batch_size = ['|', '/', '-', '\\'], 0, 0, 5
    
    while True:
        start = time.time()
        start_idx = scan_index % len(AVAILABLE_SYMBOLS)
        batch_symbols = AVAILABLE_SYMBOLS[start_idx:start_idx + batch_size]
        
        for idx, sym in enumerate(batch_symbols, 1):
            s = states[sym]
            if time.time() - s.get('rejected_time', 0) < REJECT_COOLDOWN: continue
            
            in_pos = check_open_position(sym)
            if in_pos and not s.get('in_position'):
                try:
                    pos = session.get_positions(category="linear", symbol=sym)['result']['list'][0]
                    if float(pos['size']) != 0:
                        s.update({'in_position': True, 'position_side': pos.get('side'), 'entry_price': float(pos['avgPrice'])})
                except: pass
            
            if s.get('in_position') and not in_pos:
                entry, side, px = s.get('entry_price', 0), s.get('position_side'), get_current_price(sym) or 0
                if entry > 0 and side and px > 0:
                    pct = ((px - entry) / entry) if side in ['Buy', 'LONG'] else ((entry - px) / entry)
                    s['daily_pnl'] = s.get('daily_pnl', 0) + ((ENTRY_MARGIN * LEVERAGE) * pct)
                    s['total_trades'] = s.get('total_trades', 0) + 1
                s.update({"lastExitTime": time.time(), "longState": 0, "shortState": 0, "in_position": False, "entry_price": None, "tp_price": None, "sl_price": None, "position_side": None})
            
            s['in_position'] = in_pos
            in_cooldown = (time.time() - s.get('lastExitTime', 0)) < (COOLDOWN_BARS * 5 * 60)
            si = (si + 1) % 4
            print_dashboard(states, sym, start_idx + idx, len(AVAILABLE_SYMBOLS), time.time()-start, spinner[si])
            
            if not in_pos and not in_cooldown:
                df = analyze_nayrafa_engine(get_kline_data(sym, LTF, 120))
                
                if df is not None and not df.empty and len(df) >= 2:
                    last = df.iloc[-2]
                    
                    l1 = get_indicator_icon(last.get('i1_l', False))
                    l2 = get_indicator_icon(last.get('i2_l', False))
                    l3 = get_indicator_icon(last.get('i3_l', False))
                    l4 = get_indicator_icon(last.get('i4_l', False))
                    l5 = get_indicator_icon(last.get('i5_l', False))
                    l6 = get_indicator_icon(last.get('i6_l', False))
                    l7 = get_indicator_icon(last.get('i7_l', False))
                    l8 = get_indicator_icon(last.get('i8_l', False))
                    l9 = get_indicator_icon(last.get('i9_l', False))
                    score_l_val = int(last.get('long_score', 0))
                    
                    s['long_filters'] = f"1:{l1} 2:{l2} 3:{l3} 4:{l4} 5:{l5} 6:{l6} 7:{l7} 8:{l8} 9:{l9} {C_BRIGHT_YELLOW}({score_l_val}/9){C_RESET}"
                    
                    s1 = get_indicator_icon(last.get('i1_s', False))
                    s2 = get_indicator_icon(last.get('i2_s', False))
                    s3 = get_indicator_icon(last.get('i3_s', False))
                    s4 = get_indicator_icon(last.get('i4_s', False))
                    s5 = get_indicator_icon(last.get('i5_s', False))
                    s6 = get_indicator_icon(last.get('i6_s', False))
                    s7 = get_indicator_icon(last.get('i7_s', False))
                    s8 = get_indicator_icon(last.get('i8_s', False))
                    s9 = get_indicator_icon(last.get('i9_s', False))
                    score_s_val = int(last.get('short_score', 0))
                    
                    s['short_filters'] = f"1:{s1} 2:{s2} 3:{s3} 4:{s4} 5:{s5} 6:{s6} 7:{s7} 8:{s8} 9:{s9} {C_BRIGHT_YELLOW}({score_s_val}/9){C_RESET}"
                    
                    score_l, score_s = score_l_val, score_s_val
                    
                    if score_l >= score_s: s.update({'best_side': 'LONG', 'best_filters': s['long_filters']})
                    else: s.update({'best_side': 'SHORT', 'best_filters': s['short_filters']})
                    s['last_score'] = max(score_l, score_s)
                    
                    px = get_current_price(sym) or 0
                    if s.get('longState') == 0 and last.get('longStructureValid') and last.get('longHTFTouch'):
                        s['longState'] = 1
                    elif s.get('longState') == 1:
                        if not last.get('longStructureValid'): s['longState'] = 0
                        elif score_l >= MIN_SCORE_FOR_ENTRY and px > 0:
                            sl, tp = calculate_sltp_nayrafa(df, px, 'Buy')
                            if (px - sl) > 0 and (tp - px) / (px - sl) >= MIN_RR_RATIO:
                                s.update({'entry_ready': True, 'entry_side': 'Buy', 'entry_price_target': px, 'entry_sl': sl, 'entry_tp': tp, 'entry_score': score_l})
                            else: s.update({'rejected_time': time.time(), 'entry_ready': False})
                    
                    if s.get('shortState') == 0 and last.get('shortStructureValid') and last.get('shortHTFTouch'):
                        s['shortState'] = 1
                    elif s.get('shortState') == 1:
                        if not last.get('shortStructureValid'): s['shortState'] = 0
                        elif score_s >= MIN_SCORE_FOR_ENTRY and px > 0:
                            sl, tp = calculate_sltp_nayrafa(df, px, 'Sell')
                            if (sl - px) > 0 and (px - tp) / (sl - px) >= MIN_RR_RATIO:
                                s.update({'entry_ready': True, 'entry_side': 'Sell', 'entry_price_target': px, 'entry_sl': sl, 'entry_tp': tp, 'entry_score': score_s})
                            else: s.update({'rejected_time': time.time(), 'entry_ready': False})
            
            states[sym] = s
            time.sleep(0.5)
        
        active_count = sum(1 for s in states.values() if s.get('in_position', False))
        if active_count < MAX_ACTIVE_POSITIONS:
            ready_coins = sorted([{'symbol': sym, 'state': s, **s} for sym, s in states.items() if s.get('entry_ready') and not s.get('in_position')], key=lambda x: x['entry_score'], reverse=True)
            for coin in ready_coins:
                if active_count >= MAX_ACTIVE_POSITIONS: break
                if not check_open_position(coin['symbol']):
                    print(f"\n{C_BRIGHT_GREEN}🎯 PRIORITAS NAYRAFA ENTRY: {coin['symbol']} | SKOR: {coin['entry_score']}/9 | POSISI: {active_count+1}/{MAX_ACTIVE_POSITIONS}{C_RESET}")
                    
                    try:
                        instr_info = get_instrument_info(coin['symbol'])
                        min_qty, max_qty, qty_step = instr_info['min_qty'], instr_info['max_qty'], instr_info['qty_step']
                        raw_qty = (ENTRY_MARGIN * LEVERAGE) / coin['entry_price_target']
                        qty = round(math.floor(raw_qty / qty_step) * qty_step, 8) or min_qty
                        
                        session.place_order(
                            category="linear", symbol=coin['symbol'], side=coin['entry_side'], orderType="Market", qty=str(qty),
                            takeProfit=str(coin['entry_tp']), stopLoss=str(coin['entry_sl']), timeInForce="GTC"
                        )
                        coin['state'].update({"longState" if coin['entry_side'] == 'Buy' else "shortState": 0, "in_position": True, "entry_price": coin['entry_price_target'], "tp_price": coin['entry_tp'], "sl_price": coin['entry_sl'], "position_side": coin['entry_side'], "last_score": 0, "entry_ready": False})
                        active_count += 1
                    except Exception as e:
                        print(f"{C_BRIGHT_RED}❌ Gagal Eksekusi Order Otomatis: {e}{C_RESET}")
        
        scan_index = (scan_index + batch_size) % len(AVAILABLE_SYMBOLS)
        save_state(states)
        time.sleep(5)

if __name__ == "__main__":
    try: run()
    except KeyboardInterrupt: print(f"\n{C_BRIGHT_YELLOW}👋 Berhenti.{C_RESET}")