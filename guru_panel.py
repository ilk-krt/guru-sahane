import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime, timedelta
import calendar

# ==========================================
# 0. AYARLAR & AGRESİF DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER APEX V131.0", page_icon="🏛️")

st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    p, h1, h2, h3, h4, h5, h6, span, label, div { color: #e0e0e0 !important; }
    div[data-baseweb="select"] > div { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #444 !important; }
    div[data-baseweb="popover"] > div { background-color: #1a1a1a !important; }
    ul[role="listbox"] { background-color: #1a1a1a !important; }
    ul[role="listbox"] li { color: #ffffff !important; background-color: #1a1a1a !important; }
    ul[role="listbox"] li:hover { background-color: #333333 !important; color: #00ff88 !important; }
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; color: #ffffff !important; }
    [data-testid="stExpander"] { background-color: #111111 !important; border: 1px solid #333 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary p { color: #00ff88 !important; font-weight: bold !important; font-size: 1.1rem !important; }
    div.stButton > button { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #444 !important; border-radius: 8px !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    .battery-container { width: 100%; background-color: #222; border-radius: 10px; margin: 5px 0 15px 0; border: 1px solid #444; position: relative; height: 25px; overflow: hidden; }
    .battery-fill { height: 100%; border-radius: 8px; transition: width 0.5s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-weight: bold; color: #000 !important; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

if 'active_trigger' not in st.session_state: st.session_state.active_trigger = "OPEX PINNING"

# ==========================================
# 1. NİŞ TEMATİK VERİ HARİTASI (GENİŞLETİLMİŞ)
# ==========================================
MAIN_SECTORS = {
    "XLK": "Ana Sektör: Teknoloji", "XLI": "Ana Sektör: Sanayi", "XLE": "Ana Sektör: Enerji",
    "XLV": "Ana Sektör: Sağlık", "XLF": "Ana Sektör: Finans", "XLY": "Ana Sektör: Tüketim",
    "XLB": "Ana Sektör: Materyal", "XLC": "Ana Sektör: İletişim", "XLRE": "Ana Sektör: Gayrimenkul",
    "XLU": "Ana Sektör: Kamu"
}

GLOBAL_MAP = {
    "Teknoloji (XLK)": ["SMH", "SOXX", "CIBR", "IGV", "BOTZ", "ARKF"],
    "Enerji & Altyapı": ["XOP", "OIH", "URA", "ICLN", "PAVE", "JOUL", "GASZ", "WATS"],
    "Robotik & Uzay": ["CBOT", "XAR", "ARKQ", "UFO"],
    "Biyoteknoloji & Sağlık": ["XBI", "IHI", "ARKG"],
    "Lojistik & Taşıma": ["HULL", "IYT", "JETS"],
    "Kozmetik & Tüketim": ["GLAM", "XRT", "XHB"],
    "Emtia & Materyal": ["XME", "GDX", "LIT", "REMX", "COPX"],
    "Finans & Kripto": ["KRE", "IBIT", "WGMI"],
    "Veri Merkezi & GYO": ["SRVR", "REZ", "VNQ"],
    "Litografi & Yarı İletken": ["EUV"]
}

ETF_INFO = {
    "CBOT": {"area": "Endüstriyel & Humanoid Robotlar", "stocks": ["ISRG", "PATH", "SYM", "ROCK"]},
    "WATS": {"area": "Batarya & Enerji Depolama", "stocks": ["ENPH", "PLUG", "STEM", "FLNC"]},
    "GLAM": {"area": "Kozmetik & Cilt Bakımı", "stocks": ["ELF", "EL", "COTY", "ULTA"]},
    "JOUL": {"area": "Elektrik Altyapısı & Şebeke", "stocks": ["PWR", "ETN", "QUAN", "HUBB"]},
    "GASZ": {"area": "Doğalgaz & LNG Zinciri", "stocks": ["LNG", "TRGP", "WMB", "OKE"]},
    "HULL": {"area": "Deniz & Konteyner Taşımacılığı", "stocks": ["ZIM", "TRMD", "STNG", "SBLK"]},
    "EUV": {"area": "Litografi Ekosistemi", "stocks": ["ASML", "AMAT", "LRCX", "KLAC"]},
    "COPX": {"area": "Bakır Madenciliği", "stocks": ["FCX", "SCCO", "TECK", "ERO"]},
    "LIT": {"area": "Lityum Döngüsü", "stocks": ["ALB", "SQM", "TSLA", "LTHM"]},
    "UFO": {"area": "Uzay Ekonomisi", "stocks": ["RKLB", "LUNR", "ASTS", "SPIR"]},
    "SRVR": {"area": "Veri Merkezleri & Kripto Madencilik", "stocks": ["EQIX", "AMT", "DLR", "IREN", "WULF", "SLNH", "CIFR", "DGXX"]},
    "WGMI": {"area": "Kripto Madencilik", "stocks": ["MARA", "RIOT", "CLSK"]},
    "SMH": {"area": "Yarı İletken Devleri", "stocks": ["NVDA", "TSM", "AVGO", "AMD", "ARM"]},
    "SOXX": {"area": "Çip Ekosistemi", "stocks": ["TXN", "AMAT", "QCOM", "ADI", "MCHP", "CRDO", "AXTI"]},
    "BOTZ": {"area": "Endüstriyel AI & Bulut", "stocks": ["ISRG", "SMCI", "AI", "IONQ", "NBIS"]},
    "CIBR": {"area": "Siber Güvenlik", "stocks": ["PANW", "CRWD", "FTNT", "NET", "ZS", "S", "EXTR", "DT", "OUST", "ONDS"]},
    "IGV": {"area": "Kurumsal Yazılım", "stocks": ["ADBE", "CRM", "MSFT", "NOW", "SNOW"]},
    "ARKF": {"area": "FinTech", "stocks": ["COIN", "SQ", "MELI", "PYPL", "MA", "PGY"]},
    "XAR": {"area": "Uzay Teknolojileri", "stocks": ["RKLB", "SPCE", "SIDU", "SPIR", "BKSY", "SATL"]},
    "PAVE": {"area": "Altyapı", "stocks": ["ETN", "URI", "DE", "CAT", "CARR"]},
    "XOP": {"area": "Petrol & Doğalgaz", "stocks": ["XOM", "CVX", "COP", "OXY", "DVN"]},
    "URA": {"area": "Nükleer Enerji", "stocks": ["CCJ", "SMR", "CEG", "VST", "NNE", "TLN"]},
    "ICLN": {"area": "Temiz Enerji", "stocks": ["FSLR", "ENPH", "PLUG", "ASTI"]},
    "XBI": {"area": "Biyoteknoloji", "stocks": ["MRNA", "VRTX", "AMGN", "GILD", "PFE", "GMAB"]},
    "IHI": {"area": "Tıbbi Cihazlar", "stocks": ["ABT", "MDT", "CLPT", "IINN", "QCLS", "HIMS", "TDOC", "OSCR"]},
    "KRE": {"area": "Bölgesel Bankalar", "stocks": ["NYCB", "WAL", "ZION", "CMA"]},
    "XRT": {"area": "Perakende", "stocks": ["AMZN", "COST", "WMT", "TGT", "GRAB", "SFM", "HITI", "TRUG", "SBET"]},
    "XME": {"area": "Madencilik & Çelik", "stocks": ["FCX", "NUE", "STLD", "AA", "CRML", "ATLX", "BMNR"]},
    "GDX": {"area": "Altın Madencileri", "stocks": ["NEM", "GOLD", "AEM"]},
    "OIH": {"area": "Sondaj Ekipmanları", "stocks": ["SLB", "HAL", "BKR", "VLO"]},
    "IYT": {"area": "Lojistik", "stocks": ["UNP", "UPS", "UBER", "FDX"]},
    "ARKG": {"area": "Genom", "stocks": ["CRSP", "NTLA"]},
    "JETS": {"area": "Havacılık", "stocks": ["DAL", "UAL"]},
    "XHB": {"area": "Ev Yapımı", "stocks": ["LEN", "DHI"]},
    "REMX": {"area": "Nadir Elementler", "stocks": ["MP"]},
    "IBIT": {"area": "Bitcoin ETF", "stocks": ["MSTR", "COIN"]},
    "REZ": {"area": "Konut GYO", "stocks": ["AVB", "EQR"]},
    "VNQ": {"area": "Genel GYO", "stocks": ["PLD", "AMT", "O"]}
}

SYSTEM_TRIGGERS = {
    "GAMMA SQUEEZE": {"color": "#00ff88", "battery": {"Stocks": 90, "Bonds": 30, "Crypto": 85, "Commodities": 60, "RealEstate": 70}},
    "OPEX PINNING": {"color": "#f1c40f", "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 45, "Commodities": 55, "RealEstate": 50}},
    "GEOPOLITICAL SHOCK": {"color": "#ff3333", "battery": {"Stocks": 30, "Bonds": 80, "Crypto": 25, "Commodities": 95, "RealEstate": 45}}
}

# ==========================================
# 2. KURUMSAL HABER & OPEX MOTORU (TAM İSTENEN TERİMLERLE)
# ==========================================
def get_third_friday(year, month):
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_cal = c.monthdatescalendar(year, month)
    fridays = [day for week in month_cal for day in week if day.weekday() == calendar.FRIDAY and day.month == month]
    return fridays[2]

def generate_institutional_news(trigger):
    today = datetime.now().date()
    year, month = today.year, today.month
    third_friday = get_third_friday(year, month)
    if (today - third_friday).days > 3:
        month = month + 1 if month < 12 else 1
        year = year + 1 if month == 1 else year
        third_friday = get_third_friday(year, month)
    
    days_to_opex = (third_friday - today).days
    alerts = []
    
    # Gerçekçi Mekanik Haberler (Strike Pinning, Gamma Unwind, Basket Hedging)
    if 0 <= days_to_opex <= 10:
        alerts.append(f"🚨 **OPEX DYNAMICS (Vadeye {days_to_opex} Gün):** Options expiration (OpEx) is approaching. Market makers are in long gamma. Expect artificial calm and heavy **Strike Pinning**. Breakouts are highly prone to algoritmik whipsaws.")
    elif -3 <= days_to_opex < 0:
        alerts.append("💥 **GAMMA UNWIND & REBALANCE:** OpEx is over. Dealer hedges are rolling off. Brace for violent **Dealer Gamma Unwinds** and massive **Systematic Flow Rebalances**. Fundamental realities don't matter today.")
    else:
        alerts.append(f"📊 **CLEAN FLOW:** No immediate OpEx gravity. Price action is driven by pure Dark Pool supply/demand and thematic **Basket Hedging** execution.")

    # Tetikleyiciye Özel Kurumsal Akışlar
    if trigger == "GEOPOLITICAL SHOCK":
        alerts.extend(["🌍 **SUPPLY SHOCK:** Geopolitical tension spiking. Systematic funds are executing heavy basket hedging into $HULL (Deniz Lojistiği) and $GASZ (Fosil Enerji).", "🛢️ **CONTRARIAN FLOW:** Growth thesis ignored. Capital is fleeing to hard assets."])
    elif trigger == "GAMMA SQUEEZE":
        alerts.extend(["📈 **FAIR VALUE UPGRADES:** Sell-side analysts just initiated mass re-ratings on AI Infrastructure. Institutional order flow is hunting liquidity in $JOUL and $EUV.", "🤖 **THEME ROTATION:** Relentless bid under $CBOT (Robotik). Smart money is putting size here."])
    else:
        alerts.extend(["⚖️ **EQUITY NEUTRAL:** Market is digesting recent moves. Quantitative funds are deploying statistical arbitrage across pairs. Pure 'Wait and See' mode."])
    
    return alerts

def draw_battery(label, current, color):
    st.markdown(f"""
        <div style="margin-bottom: 2px; font-size: 0.85rem; color: #ccc;">{label}</div>
        <div class="battery-container" style="height: 20px;">
            <div class="battery-fill" style="width: {current}%; background-color: {color}; font-size: 0.8rem;">%{int(current)}</div>
        </div>
    """, unsafe_allow_html=True)

def draw_smart_money_flow(trigger_data):
    dot = graphviz.Digraph()
    dot.attr(bgcolor='#050505', rankdir='LR', ranksep='1.5', nodesep='0.8')
    dot.attr('node', fontsize='16', fontname='Arial', margin='0.2,0.1')
    dot.attr('edge', fontsize='14')
    with dot.subgraph(name='cluster_0') as c:
        c.attr(style='dashed', color='#555', label='Kaydi Varlıklar', fontcolor='#e0e0e0', fontsize='18')
        c.node("FIAT", "Fiat\nCurrency", shape='ellipse', style='filled', fillcolor='#4a148c', fontcolor='white')
        c.node("USD", "USD\n(Merkez)", shape='circle', style='filled', fillcolor='#0277bd', fontcolor='white')
        c.node("STOCK", "Borsalar", shape='box', style='filled', fillcolor='#f57f17', fontcolor='white')
        c.node("BOND", "Tahviller", shape='box', style='filled', fillcolor='#2e7d32', fontcolor='white')
        c.node("CRYPTO", "Kripto", shape='box', style='filled', fillcolor='#d81b60', fontcolor='white')
    with dot.subgraph(name='cluster_1') as c:
        c.attr(style='dashed', color='#555', label='Maddi Varlıklar', fontcolor='#e0e0e0', fontsize='18')
        c.node("COMM", "Emtia &\nEnerji", shape='circle', style='filled', fillcolor='#00695c', fontcolor='white')
        c.node("REAL", "Gayrimenkul", shape='box', style='filled', fillcolor='#827717', fontcolor='white')
    bat = trigger_data['battery']
    def get_pen(val): return str(max(2.0, val / 10))
    def get_col(val): return "#00ff88" if val >= 60 else "#ff3333" if val <= 40 else "#888"
    dot.edge("FIAT", "USD", color="#aaa", penwidth="3")
    dot.edge("USD", "STOCK", color=get_col(bat['Stocks']), penwidth=get_pen(bat['Stocks']))
    dot.edge("USD", "BOND", color=get_col(bat['Bonds']), penwidth=get_pen(bat['Bonds']))
    dot.edge("USD", "CRYPTO", color=get_col(bat['Crypto']), penwidth=get_pen(bat['Crypto']))
    dot.edge("USD", "COMM", color=get_col(bat['Commodities']), penwidth=get_pen(bat['Commodities']))
    dot.edge("COMM", "REAL", color=get_col(bat['RealEstate']), penwidth=get_pen(bat['RealEstate']), style="dashed")
    st.graphviz_chart(dot, use_container_width=True)

# ==========================================
# 3. YFINANCE V127.12 MATEMATİK & OMNI FUSION
# ==========================================
def get_rma(s, period): return s.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

def get_rsi(s, period):
    delta = s.diff()
    ma_up = get_rma(delta.clip(lower=0), period)
    ma_down = get_rma(-1 * delta.clip(upper=0), period)
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

def get_wma(s, period):
    weights = np.arange(1, period + 1)
    return s.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

@st.cache_data(ttl=3600)
def fetch_matrix_data():
    all_etfs = list(set([etf for etfs in GLOBAL_MAP.values() for etf in etfs]))
    end_date = datetime.now()
    raw_data = yf.download(all_etfs, start=end_date - timedelta(days=90), end=end_date, interval="1d", group_by='ticker', progress=False)
    matrix_results = []
    for t in all_etfs:
        try:
            df = raw_data[t].dropna() if len(all_etfs) > 1 else raw_data.dropna()
            if len(df) < 25: continue
            close = df['Close']
            r14 = get_rsi(close, 14).iloc[-1]
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            current_bbw = (((sma20 + 2*std20) - (sma20 - 2*std20)) / sma20 * 100).iloc[-1]
            cat = next((k for k, v in GLOBAL_MAP.items() if t in v), "Diğer")
            if r14 > 70: state, color = "Aşırı Alım (Dağıtım)", "#ff3333"
            elif r14 < 35: state, color = "Vakum (Contrarian Fırsat)", "#00ff88"
            else: state, color = "Sıkışma (VCP)", "#f1c40f"
            matrix_results.append({"Sektör": cat, "ETF": t, "RSI": r14, "BBW": current_bbw, "Durum": state, "Renk": color})
        except: continue
    return pd.DataFrame(matrix_results)

@st.cache_data(ttl=900)
def calculate_signals(ticker_list, interval="1d"):
    if not ticker_list: return pd.DataFrame()
    end_date = datetime.now()
    try:
        if interval == "1d":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=90), end=end_date, interval="1d", group_by='ticker', progress=False)
        elif interval == "4h":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=50), end=end_date, interval="1h", group_by='ticker', progress=False)
        elif interval == "1wk":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=200), end=end_date, interval="1wk", group_by='ticker', progress=False)
    except: return pd.DataFrame()

    results = []
    for t in ticker_list:
        try:
            df = raw_data[t].copy().dropna() if len(ticker_list) > 1 else raw_data.copy().dropna()
            if len(df) < 30: continue

            if interval == "4h":
                df.index = pd.to_datetime(df.index)
                df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

            close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
            pct_1d = (close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0
            pct_1w = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else 0

            r14 = get_rsi(close, 14)
            v150_v_avg = vol.rolling(20).mean()
            ema1_s3 = close.ewm(span=5, adjust=False).mean()
            tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
            atr14 = get_rma(tr, 14)

            # V650 Quantum Engine
            c_range_q = (high - low).clip(lower=0.001)
            delta_q = ((close - low) - (high - close)) / c_range_q
            delta_vol_q = (delta_q * vol).rolling(20).mean() / vol.rolling(20).mean().clip(lower=0.001)
            rvol_q = (vol / vol.rolling(20).mean().clip(lower=1)).clip(upper=2.5)

            base_pwr_q = ((r14 - 50) + (delta_vol_q * 50)) * rvol_q * 1.5
            logic_pwr_q = np.log(1 + np.exp(base_pwr_q / 5)) * 5
            logic_pwr_q = np.where((low > high.shift(2)) & (close > open_p), logic_pwr_q + 35, logic_pwr_q)

            log_w_q = np.log10(1 + np.clip(logic_pwr_q, 0, None))
            pct_w_q = np.clip((log_w_q * 65)**0.8 * 1.8, 0, 100)
            w_pwr_q = get_wma(pd.Series(pct_w_q, index=close.index), 2)

            # Whale Re-Entry
            pct_pro_q = w_pwr_q.ewm(span=3, adjust=False).mean()
            yellow_rest = (w_pwr_q.shift(1) < pct_pro_q.shift(1)) & (w_pwr_q.shift(2) < pct_pro_q.shift(2))
            cross_now = (w_pwr_q > pct_pro_q) & (w_pwr_q.shift(1) <= pct_pro_q.shift(1))
            whale_re_entry = cross_now & yellow_rest

            # APU Energy Level
            typ = (high + low + close) / 3
            mf = typ * vol
            pos_mf = mf.where(typ > typ.shift(), 0).rolling(14).sum()
            neg_mf = mf.where(typ < typ.shift(), 0).rolling(14).sum().replace(0, 0.001)
            mfi_14 = 100 - (100 / (1 + (pos_mf / neg_mf)))
            energy_lvl = (r14 + mfi_14) / 2.0
            is_hyper_power = (w_pwr_q >= 70) & (energy_lvl >= 70)

            # Volatility Hole (Keltner Squeeze)
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            b_up = sma20 + 2 * std20
            b_low = sma20 - 2 * std20

            tr_sma20 = tr.rolling(20).mean()
            k_mid = sma20
            k_up = k_mid + 1.5 * tr_sma20
            k_low = k_mid - 1.5 * tr_sma20

            is_sqz = (b_low > k_low) & (b_up < k_up)
            kc_range_half = (k_up - k_mid) / 3.0
            vol_hole = is_sqz & (close <= (k_mid - kc_range_half))

            # Traps (Yazısız)
            bear_trap = (low < ema1_s3) & (close > ema1_s3) & (vol > v150_v_avg * 1.8)
            bull_trap = (high > ema1_s3) & (close < ema1_s3) & (vol > v150_v_avg * 1.8)

            # EXP Ignition
            h_fast = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
            h_slow = get_wma(h_fast, 9)
            snip_bb_dev = 2.0 * std20
            snip_kc_dev = 1.5 * atr14.rolling(20).mean()
            in_squeeze = snip_bb_dev < snip_kc_dev
            exp_buy = (~in_squeeze) & in_squeeze.shift(1) & (h_fast > h_slow) & (h_fast > 0)
            exp_sel = (~in_squeeze) & in_squeeze.shift(1) & (h_fast < h_slow) & (h_fast < 0)

            # Fusion Scores
            _kin_b = ((vol > v150_v_avg * 1.2) & (close > open_p)).astype(int)
            _tre_b = (close > close.ewm(span=34).mean()).astype(int)
            _kur_b = ((r14 > 50) & (r14.shift(1) <= 50)).astype(int)
            _wyc_b = ((low < low.shift(1)) & (close > open_p) & (close > high.shift(1))).astype(int)

            _kin_s = ((vol > v150_v_avg * 1.2) & (close < open_p)).astype(int)
            _tre_s = (close < close.ewm(span=34).mean()).astype(int)
            _kur_s = ((r14 < 50) & (r14.shift(1) >= 50)).astype(int)
            _wyc_s = ((high > high.shift(1)) & (close < open_p) & (close < low.shift(1))).astype(int)

            total_score_b = _kin_b + _tre_b + _kur_b + _wyc_b
            total_score_s = _kin_s + _tre_s + _kur_s + _wyc_s
            any_buy = total_score_b >= 2
            any_sel = total_score_s >= 2

            sig = "⚪ WAIT"
            
            # --- HAFTALIK MOMENTUM-GAP ŞARTLARI ---
            if interval == "1wk":
                # 1. Prior Momentum (Önceki haftalarda yükselen dipler/tepeler)
                prior_momentum = (low.shift(1) >= low.shift(2)) & (high.shift(1) >= high.shift(2)) & (close.shift(1) > sma20.shift(1))
                # 2. Valid Gap (Pazartesi açılışı geçen haftanın en yükseğinin üzerinde)
                bull_gap = (open_p > high.shift(1)) & (close > open_p)
                
                if prior_momentum.iloc[-1] and bull_gap.iloc[-1]: sig = "🚀 MOMENTUM GAP (UP)"
                elif (w_pwr_q.iloc[-1] > 80): sig = "🐋 WHALE ACCUMULATION"
                elif (r14.iloc[-1] < 35): sig = "🕳️ DEEP VALUE (DCA)"
            else:
                # --- GÜNLÜK HİYERARŞİ ---
                if (any_buy.iloc[-1] & is_hyper_power.iloc[-1]): sig = "☄️ HYPER BUY"
                elif (any_sel.iloc[-1] & is_hyper_power.iloc[-1]): sig = "☄️ HYPER SELL"
                elif whale_re_entry.iloc[-1]: sig = "🔄 WHALE RE-ENTRY"
                elif vol_hole.iloc[-1]: sig = "🕳️ VOLA HOLE"
                elif bull_trap.iloc[-1]: sig = "⛔"
                elif bear_trap.iloc[-1]: sig = "✅"
                elif exp_buy.iloc[-1]: sig = "💥 EXP BUY"
                elif exp_sel.iloc[-1]: sig = "💥 EXP SELL"
                elif w_pwr_q.iloc[-1] >= 85: sig = "🐋 WHALE IN"
                elif any_buy.iloc[-1]: sig = "✅ BUY"
                elif any_sel.iloc[-1]: sig = "🔴 SELL"

            results.append({
                "Ticker": t, "Sinyal": sig, "Fiyat": f"${close.iloc[-1]:.2f}",
                "Whale Power": float(f"{w_pwr_q.iloc[-1]:.1f}"), "Fusion": int(total_score_b.iloc[-1]),
                "1 Gün (%)": round(pct_1d, 2), "1 Hafta (%)": round(pct_1w, 2)
            })
        except Exception: continue
    
    if results: return pd.DataFrame(results).sort_values(by="Fusion", ascending=False)
    return pd.DataFrame()

@st.cache_data(ttl=86400)
def fetch_fundamental_data(ticker_list):
    funds = []
    today = datetime.now().date()
    for t in ticker_list:
        try:
            tk = yf.Ticker(t)
            target = tk.info.get('targetMeanPrice', None)
            fv = f"${target:.2f}" if target else "N/A"
            cal = tk.calendar
            earn_date = "N/A"
            days_to_earn = 999
            if cal and 'Earnings Date' in cal and len(cal['Earnings Date']) > 0:
                e_date = cal['Earnings Date'][0].date()
                earn_date = e_date.strftime('%Y-%m-%d')
                days_to_earn = (e_date - today).days
            funds.append({"Ticker": t, "Fair Value": fv, "Bilanço": earn_date, "DaysToEarn": days_to_earn})
        except: funds.append({"Ticker": t, "Fair Value": "N/A", "Bilanço": "N/A", "DaysToEarn": 999})
    return pd.DataFrame(funds)

def style_signals(val):
    if isinstance(val, str):
        if 'GAP' in val: return 'background-color: #00e676; color: black; font-weight: bold;'
        if 'DEEP' in val: return 'background-color: #00b0ff; color: black; font-weight: bold;'
        if 'HYPER BUY' in val: return 'background-color: #827717; color: white; font-weight: bold;'
        if 'HYPER SELL' in val: return 'background-color: #4a0000; color: white; font-weight: bold;'
        if 'WHALE RE-ENTRY' in val: return 'background-color: #006064; color: white; font-weight: bold;'
        if 'WHALE IN' in val: return 'background-color: #01579b; color: white;'
        if 'VOLA HOLE' in val: return 'background-color: #4a148c; color: white;'
        if 'EXP BUY' in val: return 'background-color: #1b5e20; color: white; font-weight: bold;'
        if 'EXP SELL' in val: return 'background-color: #bf360c; color: white; font-weight: bold;'
        if 'BUY' in val: return 'background-color: #004d40; color: white; font-weight: bold;'
        if 'SELL' in val: return 'background-color: #3e2723; color: white; font-weight: bold;'
        if val == '⛔': return 'background-color: #b71c1c; color: white; font-size: 1.2rem; text-align: center;'
        if val == '✅': return 'background-color: #004d40; color: white; font-size: 1.2rem; text-align: center;'
    return 'background-color: #111111; color: white;'

def style_percentages(val):
    if isinstance(val, (float, int)): return f"color: {'#00ff88' if val > 0 else '#ff3333'}; font-weight: bold;"
    return ''

# ==========================================
# 5. KOKPİT ARAYÜZÜ 
# ==========================================
st.title("🏛️ AETHER APEX: THEMATIC & MOMENTUM ARCHITECT")

# --- ACİL UYARI RADARI (EARNINGS & FAIR VALUE) ---
raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]
portfolio_tickers = sorted(list(set(raw_tickers)))

with st.spinner("Piyasa Radar Kontrolü (Bilanço & Değer)..."):
    df_alerts = fetch_fundamental_data(portfolio_tickers)
    urgent_earn = df_alerts[(df_alerts['DaysToEarn'] >= 0) & (df_alerts['DaysToEarn'] <= 7)]
    if not urgent_earn.empty:
        st.warning(f"🔔 **YAKLAŞAN BİLANÇO DİKKAT:** {', '.join(urgent_earn['Ticker'].tolist())} hisselerinin bilançosuna 7 günden az kaldı! Volatilite artabilir.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌐 MAKRO & OPEX", 
    "🔋 OMNI-MATRIX (Piller)", 
    "🦈 HAFTALIK MOMENTUM-GAP",
    "🚨 4H & OMNI RADAR",
    "📋 MÜKEMMEL PORTFÖY"
])

# ---------------------------------------------------------
# TAB 1: MAKRO & OPEX KOKPİT
# ---------------------------------------------------------
with tab1:
    st.subheader("⚙️ Institutional Desk: Gizli Piyasa Mekanikleri")
    t_cols = st.columns(3)
    for i, trig in enumerate(SYSTEM_TRIGGERS.keys()):
        with t_cols[i]:
            if st.button(f"Senaryo: {trig}", use_container_width=True):
                st.session_state.active_trigger = trig

    alerts = generate_institutional_news(st.session_state.active_trigger)
    for alert in alerts:
        st.markdown(f"<div style='border-left: 3px solid {SYSTEM_TRIGGERS[st.session_state.active_trigger]['color']}; padding-left: 10px; margin-bottom: 10px; font-size:1rem; background-color:#1a1a1a; padding:10px; border-radius:5px;'>{alert}</div>", unsafe_allow_html=True)
    
    st.divider()
    draw_smart_money_flow(SYSTEM_TRIGGERS[st.session_state.active_trigger])

# ---------------------------------------------------------
# TAB 2: OMNI-MATRIX (TÜM PİLLER & SCATTER)
# ---------------------------------------------------------
with tab2:
    st.subheader("🔋 Tüm Sektörler Pil Enerjisi & Contrarian Matris")
    st.markdown("Trade the theme you have, not the theme you want. Hangi temanın pili şarj oluyor? Hangi tema Volatilite Vakumuna (Hole) düştü? Bir bakışta gör.")
    
    with st.spinner("Tüm Matrix ve Pil verileri hesaplanıyor..."):
        df_m = fetch_matrix_data()
        if not df_m.empty:
            theme_avg = df_m.groupby('Sektör')['RSI'].mean().reset_index()
            cols = st.columns(4)
            for i, row in theme_avg.iterrows():
                with cols[i % 4]:
                    col = "#00ff88" if row['RSI'] > 60 else "#ff3333" if row['RSI'] < 40 else "#f1c40f"
                    draw_battery(row['Sektör'], row['RSI'], col)
            
            st.divider()
            
            fig = go.Figure()
            for state in ["Aşırı Alım (Dağıtım)", "Sıkışma (VCP)", "Vakum (Contrarian Fırsat)"]:
                df_s = df_m[df_m["Durum"] == state]
                fig.add_trace(go.Scatter(
                    x=df_s["BBW"], y=df_s["RSI"], mode='markers+text',
                    marker=dict(size=14, color=df_s["Renk"], line=dict(width=1, color='white'), opacity=0.9),
                    text=df_s["ETF"], textposition="top center", name=state,
                    hovertemplate="<b>%{text}</b><br>Tema: " + df_s["Sektör"] + "<br>Enerji (Flow): %{y:.1f}<br>Sıkışma: %{x:.1f}%<extra></extra>"
                ))
            fig.add_hline(y=70, line_dash="dash", line_color="#ff3333", annotation_text="Tehlike (Aşırı Isınma)")
            fig.add_hline(y=35, line_dash="dash", line_color="#00ff88", annotation_text="Relentless DCA (Dip Toplama)")
            fig.update_layout(title="Gerçek Zamanlı Tematik Enerji Matrisi", xaxis_title="Bollinger Bant Genişliği (Sola yaklaştıkça patlamaya hazır VCP)", yaxis_title="RSI (Hacimsel Enerji Yükü)", height=550, paper_bgcolor="#050505", plot_bgcolor="#111", font=dict(color="#e0e0e0"))
            st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: HAFTALIK MOMENTUM-GAP
# ---------------------------------------------------------
with tab3:
    st.subheader("🦈 Haftalık Momentum-Gap Avcısı (VCP & Lunge)")
    st.markdown("""
        **Kurallar:** 1. **Prior Momentum:** Geçmiş iki haftada yavaş yavaş yükselen dipler ve tepeler oluşturması (Swimming like sharks).
        2. **Valid Gap:** Pazartesi açılışıyla geçen haftanın en yüksek değerinin üzerinde gap bırakması (Lunge).
        3. **Iron Discipline:** Bu sekme sadece **1 Haftalık (1W)** grafikleri tarar. Piyasa gürültüsünü yok sayar.
    """)
    
    with st.spinner("1W Kinetik Boşluklar aranıyor..."):
        df_wk = calculate_signals(portfolio_tickers, interval="1wk")
        if not df_wk.empty:
            df_wk_disp = df_wk[['Ticker', 'Sinyal', 'Fiyat', 'Whale Power']]
            st.dataframe(df_wk_disp.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 4: 4H & OMNI RADAR
# ---------------------------------------------------------
with tab4:
    st.subheader("🌐 4H SEKTÖR & ALT SEKTÖR RADARI (WHALE & HOLE)")
    all_etfs_to_scan = list(MAIN_SECTORS.keys()) + list(ETF_INFO.keys())
    etf_name_map = {k: v for k, v in MAIN_SECTORS.items()}
    for k, v in ETF_INFO.items(): etf_name_map[k] = f"Alt Sektör: {v['area']}"

    with st.spinner("Sektör ETF'leri 4H periyotta Kuantum Motoru ile taranıyor..."):
        df_4h_etfs = calculate_signals(all_etfs_to_scan, interval="4h")
        if not df_4h_etfs.empty:
            df_4h_etfs['Sektör Adı'] = df_4h_etfs['Ticker'].map(etf_name_map)
            df_4h_etfs = df_4h_etfs[['Sektör Adı', 'Ticker', 'Sinyal', 'Fiyat', 'Whale Power', 'Fusion']]
            
            df_whale_4h = df_4h_etfs[df_4h_etfs['Sinyal'] == '🔄 WHALE RE-ENTRY']
            df_hole_4h = df_4h_etfs[df_4h_etfs['Sinyal'] == '🕳️ VOLA HOLE']
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<h4 style='color: #00bcd4;'>🔄 4H Whale Re-Entry</h4>", unsafe_allow_html=True)
                st.dataframe(df_whale_4h.style.map(style_signals, subset=['Sinyal']) if not df_whale_4h.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            with c2:
                st.markdown("<h4 style='color: #9c27b0;'>🕳️ 4H Volatility Hole</h4>", unsafe_allow_html=True)
                st.dataframe(df_hole_4h.style.map(style_signals, subset=['Sinyal']) if not df_hole_4h.empty else pd.DataFrame(), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🚨 OMNI RADAR: Tüm Hisseler Günlük Tarama")
    all_market_stocks = list(set([s for data in ETF_INFO.values() for s in data["stocks"]]))
    
    with st.spinner("Tüm piyasa (hisseler) günlük periyotta taranıyor..."):
        df_radar = calculate_signals(all_market_stocks, interval="1d")
        if not df_radar.empty:
            df_whale = df_radar[df_radar['Sinyal'] == '🔄 WHALE RE-ENTRY']
            df_hole = df_radar[df_radar['Sinyal'] == '🕳️ VOLA HOLE']
            
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("<h4 style='color: #00bcd4;'>🔄 Günlük Whale Re-Entry</h4>", unsafe_allow_html=True)
                st.dataframe(df_whale[['Ticker', 'Sinyal', 'Fiyat', 'Fusion']].style.map(style_signals, subset=['Sinyal']) if not df_whale.empty else pd.DataFrame(), use_container_width=True, hide_index=True)
            with col_r2:
                st.markdown("<h4 style='color: #9c27b0;'>🕳️ Günlük Volatility Hole</h4>", unsafe_allow_html=True)
                st.dataframe(df_hole[['Ticker', 'Sinyal', 'Fiyat', 'Fusion']].style.map(style_signals, subset=['Sinyal']) if not df_hole.empty else pd.DataFrame(), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 5: MÜKEMMEL PORTFÖY
# ---------------------------------------------------------
with tab5:
    st.subheader("📋 Genel Portföy & OMNI Radar İzleme Listesi (Fair Value Analizi)")
    
    with st.spinner("Portföy simülasyonu ve veriler hesaplanıyor..."):
        df_port = calculate_signals(portfolio_tickers, interval="1d")
        if not df_port.empty:
            df_port_final = pd.merge(df_port, df_alerts[['Ticker', 'Fair Value', 'Bilanço']], on="Ticker", how="left")
            df_port_final = df_port_final[['Ticker', 'Sinyal', 'Fiyat', 'Fair Value', 'Bilanço', '1 Gün (%)', '1 Hafta (%)', 'Whale Power', 'Fusion']]
            
            st.dataframe(
                df_port_final.style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']),
                use_container_width=True, height=750, hide_index=True
            )
