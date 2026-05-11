import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime, timedelta

# ==========================================
# 0. AYARLAR & AGRESİF DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION V127.12", page_icon="🏛️")

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

if 'active_trigger' not in st.session_state: st.session_state.active_trigger = "NEUTRAL"
if 'active_sector' not in st.session_state: st.session_state.active_sector = None

# ==========================================
# 1. GENİŞLETİLMİŞ VERİ HARİTASI
# ==========================================
MAIN_SECTORS = {
    "XLK": "Ana Sektör: Teknoloji", "XLI": "Ana Sektör: Sanayi", "XLE": "Ana Sektör: Enerji",
    "XLV": "Ana Sektör: Sağlık", "XLF": "Ana Sektör: Finans", "XLY": "Ana Sektör: Tüketim",
    "XLB": "Ana Sektör: Materyal", "XLC": "Ana Sektör: İletişim", "XLRE": "Ana Sektör: Gayrimenkul",
    "XLU": "Ana Sektör: Kamu"
}

GLOBAL_MAP = {
    "Teknoloji (XLK)": ["SMH", "SOXX", "CIBR", "IGV", "BOTZ", "ARKF"],
    "Sanayi (XLI)": ["ITA", "XAR", "IYT", "PAVE", "JETS"],
    "Enerji (XLE)": ["XOP", "OIH", "URA", "ICLN", "TAN"],
    "Sağlık (XLV)": ["XBI", "IHI", "ARKG"],
    "Finans (XLF)": ["KRE", "KIE", "IAI"],
    "Tüketim (XLY)": ["XRT", "XHB", "IBUY", "BETZ"],
    "Materyal (XLB)": ["XME", "GDX", "LIT", "REMX"],
    "İletişim (XLC)": ["SOCL", "HERO"],
    "Gayrimenkul (XLRE)": ["SRVR", "REZ"],
    "Kamu (XLU)": ["PHO"]
}

ETF_INFO = {
    "SMH": {"area": "Yarı İletken Devleri", "stocks": ["NVDA", "TSM", "AVGO", "ASML", "AMD", "MU", "INTC", "ARM"]},
    "SOXX": {"area": "Çip Ekosistemi", "stocks": ["TXN", "AMAT", "QCOM", "ADI", "MCHP", "CRDO", "AXTI"]},
    "BOTZ": {"area": "Endüstriyel AI & Bulut", "stocks": ["ISRG", "SMCI", "AI", "IONQ", "NBIS"]},
    "CIBR": {"area": "Siber Güvenlik", "stocks": ["PANW", "CRWD", "FTNT", "NET", "ZS", "S", "EXTR", "DT", "OUST", "ONDS"]},
    "IGV": {"area": "Kurumsal Yazılım", "stocks": ["ADBE", "CRM", "MSFT", "NOW", "SNOW"]},
    "ARKF": {"area": "FinTech", "stocks": ["COIN", "SQ", "MELI", "PYPL", "MA", "PGY"]},
    "ITA": {"area": "Savunma Sanayi", "stocks": ["RTX", "LMT", "BA", "GD", "NOC", "KTOS"]},
    "XAR": {"area": "Uzay Teknolojileri", "stocks": ["RKLB", "SPCE", "SIDU", "SPIR", "BKSY", "SATL"]},
    "IYT": {"area": "Lojistik", "stocks": ["UNP", "UPS", "UBER", "FDX"]},
    "PAVE": {"area": "Altyapı", "stocks": ["ETN", "URI", "DE", "CAT", "CARR"]},
    "XOP": {"area": "Petrol & Doğalgaz", "stocks": ["XOM", "CVX", "COP", "OXY", "DVN"]},
    "OIH": {"area": "Sondaj Ekipmanları", "stocks": ["SLB", "HAL", "BKR", "VLO"]},
    "URA": {"area": "Nükleer Enerji", "stocks": ["CCJ", "SMR", "CEG", "VST", "NNE", "TLN"]},
    "ICLN": {"area": "Temiz Enerji", "stocks": ["FSLR", "ENPH", "PLUG", "ASTI"]},
    "XBI": {"area": "Biyoteknoloji", "stocks": ["MRNA", "VRTX", "AMGN", "GILD", "PFE", "GMAB"]},
    "IHI": {"area": "Tıbbi Cihazlar", "stocks": ["ABT", "MDT", "CLPT", "IINN", "QCLS", "HIMS", "TDOC", "OSCR"]},
    "KRE": {"area": "Bölgesel Bankalar", "stocks": ["NYCB", "WAL", "ZION", "CMA"]},
    "XRT": {"area": "Perakende", "stocks": ["AMZN", "COST", "WMT", "TGT", "GRAB", "SFM", "HITI", "TRUG", "SBET"]},
    "XME": {"area": "Madencilik & Çelik", "stocks": ["FCX", "NUE", "STLD", "AA", "CRML", "ATLX", "BMNR"]},
    "LIT": {"area": "Lityum Döngüsü", "stocks": ["ALB", "SQM", "TSLA"]},
    "GDX": {"area": "Altın Madencileri", "stocks": ["NEM", "GOLD", "AEM"]},
    "SOCL": {"area": "Sosyal Medya", "stocks": ["META", "GOOG", "SNAP"]},
    "SRVR": {"area": "Veri Merkezleri & Kripto Madencilik", "stocks": ["EQIX", "AMT", "DLR", "IREN", "WULF", "SLNH", "CIFR", "DGXX"]},
    "PHO": {"area": "Kamu Su & Altyapı", "stocks": ["AWK", "XYL", "AWR", "T"]}
}

SYSTEM_TRIGGERS = {
    "GEOPOLITIK": {"color": "#ff3333", "impact": "risk_off", "news": ["T-3: Enerji nakil hatlarına yönelik sabotaj iddiaları piyasayı gerdi.", "T-2: Merkez bankaları stratejik rezervleri kullanıma açabileceğini sinyalledi.", "BUGÜN: Nakliye rotalarında sigorta primleri %40 arttı. Sıkışmış yay etkisi birikiyor."], "battery": {"Stocks": 30, "Bonds": 80, "Crypto": 25, "Commodities": 95, "RealEstate": 45}},
    "LEADING": {"color": "#00ff88", "impact": "risk_on", "news": ["T-3: İmalat PMI verileri son 8 ayın zirvesine tırmandı.", "T-2: Yapay Zeka (AI) yatırımlarında donanım siparişleri beklentileri ikiye katladı.", "BUGÜN: Tüketici güveni güçlü. Piyasa yeni bir breakout (kırılım) arayışında."], "battery": {"Stocks": 90, "Bonds": 30, "Crypto": 85, "Commodities": 60, "RealEstate": 70}},
    "COINCIDENT": {"color": "#f1c40f", "impact": "neutral_mixed", "news": ["T-3: İstihdam verileri güçlü ancak saatlik kazançlar stabil.", "T-2: Merkez bankası tutanaklarında 'bekle ve gör' vurgusu öne çıktı.", "BUGÜN: Piyasada belirgin bir yön yok, eşit ağırlıklı fonlara geçiş var."], "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 45, "Commodities": 55, "RealEstate": 50}}
}

def get_sector_status(sector_name, trigger):
    base_charge = 50
    news = ""
    if trigger == "GEOPOLITIK":
        if any(x in sector_name for x in ["Enerji", "Sanayi", "Materyal"]):
            base_charge = np.random.randint(75, 95); prev = base_charge - np.random.randint(10, 25)
            news = f"Küresel arz endişeleri ve tedarik zinciri sıkıntıları, {sector_name} tarafında fiyatlama gücünü artırıyor. Akıllı para, risk-off ortamında bu sektörü güvenli liman (hedge) olarak kullanıyor."
        elif any(x in sector_name for x in ["Teknoloji", "Tüketim"]):
            base_charge = np.random.randint(20, 45); prev = base_charge + np.random.randint(10, 25)
            news = f"Artan jeopolitik riskler ve belirsizlik, yüksek çarpanlı {sector_name} hisselerinden çıkışlara (deşarj) neden oluyor. Yatırımcılar risk iştahını kapatmış durumda."
        else:
            base_charge = np.random.randint(40, 60); prev = base_charge + np.random.randint(-5, 5)
            news = f"{sector_name} mevcut jeopolitik sarsıntılardan sınırlı etkilenerek yatay bir bantta (trading range) sıkışmış durumda."
    elif trigger == "LEADING":
        if any(x in sector_name for x in ["Teknoloji", "Enerji", "Gayrimenkul"]):
            base_charge = np.random.randint(80, 98); prev = base_charge - np.random.randint(15, 30)
            news = f"Güçlü öncü göstergeler ve AI devrimi, {sector_name} sektöründe devasa bir fon girişini tetikledi. Opsiyon piyasasındaki alımlar (call skew) breakout ihtimalini güçlendiriyor."
        else:
            base_charge = np.random.randint(45, 65); prev = base_charge - np.random.randint(5, 15)
            news = f"Risk iştahının artmasıyla defansif alanlardan çıkan para, yavaş yavaş {sector_name} sektöründe de toparlanma emareleri gösteriyor."
    else: 
        base_charge = np.random.randint(45, 65); prev = base_charge + np.random.randint(-10, 10)
        news = f"Piyasadaki aşırı sakinlik (whipsaw tehlikesi) nedeniyle {sector_name} sektöründe fon yöneticileri bekle-gör stratejisi uyguluyor. Kararsız para giriş-çıkışları mevcut."
        
    delta_icon = "⬆️ Şarj Oluyor" if base_charge > prev else "⬇️ Deşarj Oluyor" if base_charge < prev else "➖ Stabil"
    return base_charge, prev, delta_icon, news

def draw_battery_with_delta(label, current, previous, delta_icon):
    color = "#00ff88" if current >= 75 else "#f1c40f" if current >= 45 else "#ff3333"
    st.markdown(f"""
        <div style="margin-bottom: 5px; font-size: 0.95rem; color: #e0e0e0;">
            <strong>{label} Şarj Seviyesi: %{current}</strong> 
            <span style="color:#aaa; font-size:0.85rem;">(Önceki: %{previous} - {delta_icon})</span>
        </div>
        <div class="battery-container">
            <div class="battery-fill" style="width: {current}%; background-color: {color};">%{current}</div>
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
        c.node("GOLD", "Değer\nSaklama", shape='circle', style='filled', fillcolor='#fbc02d', fontcolor='black')
        c.node("REAL", "Gayrimenkul", shape='box', style='filled', fillcolor='#827717', fontcolor='white')

    bat = trigger_data['battery']
    def get_pen(val): return str(max(2.0, val / 10))
    def get_col(val): return "#00ff88" if val >= 60 else "#ff3333" if val <= 40 else "#888"

    dot.edge("FIAT", "USD", color="#aaa", penwidth="3")
    dot.edge("USD", "STOCK", color=get_col(bat['Stocks']), penwidth=get_pen(bat['Stocks']))
    dot.edge("USD", "BOND", color=get_col(bat['Bonds']), penwidth=get_pen(bat['Bonds']))
    dot.edge("USD", "CRYPTO", color=get_col(bat['Crypto']), penwidth=get_pen(bat['Crypto']))
    
    comm_avg = bat['Commodities'] + 10
    dot.edge("USD", "COMM", color=get_col(comm_avg), penwidth=get_pen(comm_avg))
    dot.edge("USD", "GOLD", color=get_col(bat['Commodities']), penwidth=get_pen(bat['Commodities']))
    dot.edge("COMM", "REAL", color=get_col(bat['RealEstate']), penwidth=get_pen(bat['RealEstate']), style="dashed")
    st.graphviz_chart(dot, use_container_width=True)

# ==========================================
# 4. YFINANCE V650 OMNI FUSION (MATEMATİKSEL SENKRONİZASYON)
# ==========================================
def get_rma(s, period):
    return s.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

def get_rsi(s, period):
    delta = s.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = get_rma(up, period)
    ma_down = get_rma(down, period)
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

def get_wma(s, period):
    weights = np.arange(1, period + 1)
    return s.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

@st.cache_data(ttl=900)
def calculate_signals(ticker_list, interval="1d"):
    if not ticker_list: return pd.DataFrame()
    end_date = datetime.now()
    
    try:
        if interval == "1d":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=90), end=end_date, interval="1d", group_by='ticker', progress=False)
        elif interval == "4h":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=50), end=end_date, interval="1h", group_by='ticker', progress=False)
    except:
        return pd.DataFrame()

    results = []
    for t in ticker_list:
        try:
            if len(ticker_list) > 1:
                if t not in raw_data.columns.levels[0]: continue
                df = raw_data[t].copy().dropna()
            else:
                df = raw_data.copy().dropna()
                
            if df.empty: continue
            
            if interval == "4h":
                df.index = pd.to_datetime(df.index)
                df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

            if len(df) < 30: continue

            close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
            
            # 1. Base Indicators & V150 Sensors
            r14 = get_rsi(close, 14)
            v150_v_avg = vol.rolling(20).mean()
            ema1_s3 = close.ewm(span=5, adjust=False).mean()
            tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
            atr14 = get_rma(tr, 14)

            # 2. V650 Quantum Engine (Birebir Formüller)
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

            # 3. V650 Whale Re-Entry (Gelişmiş Sarı Line Mantığı)
            pct_pro_q = w_pwr_q.ewm(span=3, adjust=False).mean()
            yellow_rest = (w_pwr_q.shift(1) < pct_pro_q.shift(1)) & (w_pwr_q.shift(2) < pct_pro_q.shift(2))
            cross_now = (w_pwr_q > pct_pro_q) & (w_pwr_q.shift(1) <= pct_pro_q.shift(1))
            whale_re_entry = cross_now & yellow_rest

            # 4. V650 APU Energy Level (MFI + RSI Fusion)
            typ = (high + low + close) / 3
            mf = typ * vol
            pos_mf = mf.where(typ > typ.shift(), 0).rolling(14).sum()
            neg_mf = mf.where(typ < typ.shift(), 0).rolling(14).sum().replace(0, 0.001)
            mfi_14 = 100 - (100 / (1 + (pos_mf / neg_mf)))
            energy_lvl = (r14 + mfi_14) / 2.0
            is_hyper_power = (w_pwr_q >= 70) & (energy_lvl >= 70)

            # 5. Volatility Hole & Squeeze
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

            # 6. Traps (Eğim Kuralı İptal Edilmiş Saf Tuzak Mantığı)
            bear_trap = (low < ema1_s3) & (close > ema1_s3) & (vol > v150_v_avg * 1.8)
            bull_trap = (high > ema1_s3) & (close < ema1_s3) & (vol > v150_v_avg * 1.8)

            # 7. EXP Ignition Squeeze
            h_fast = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
            h_slow = get_wma(h_fast, 9)
            snip_bb_dev = 2.0 * std20
            snip_kc_dev = 1.5 * atr14.rolling(20).mean()
            in_squeeze = snip_bb_dev < snip_kc_dev
            exp_buy = (~in_squeeze) & in_squeeze.shift(1) & (h_fast > h_slow) & (h_fast > 0)
            exp_sel = (~in_squeeze) & in_squeeze.shift(1) & (h_fast < h_slow) & (h_fast < 0)

            # 8. Fusion Scores (OMNI Any Buy/Sell Proxy)
            _kin_b = ((vol > v150_v_avg * 1.2) & (close > open_p)).astype(int)
            _kin_s = ((vol > v150_v_avg * 1.2) & (close < open_p)).astype(int)
            _tre_b = (close > close.ewm(span=34).mean()).astype(int)
            _tre_s = (close < close.ewm(span=34).mean()).astype(int)
            _kur_b = ((r14 > 50) & (r14.shift(1) <= 50)).astype(int)
            _kur_s = ((r14 < 50) & (r14.shift(1) >= 50)).astype(int)
            _wyc_b = ((low < low.shift(1)) & (close > open_p) & (close > high.shift(1))).astype(int)
            _wyc_s = ((high > high.shift(1)) & (close < open_p) & (close < low.shift(1))).astype(int)

            total_score_b = _kin_b + _tre_b + _kur_b + _wyc_b
            total_score_s = _kin_s + _tre_s + _kur_s + _wyc_s

            any_buy = total_score_b >= 2
            any_sel = total_score_s >= 2

            hyper_buy = any_buy & is_hyper_power
            hyper_sel = any_sel & is_hyper_power

            # 9. Katı Hiyerarşi ile Sinyal Tespiti
            if hyper_buy.iloc[-1]: sig = "☄️ HYPER BUY"
            elif hyper_sel.iloc[-1]: sig = "☄️ HYPER SELL"
            elif whale_re_entry.iloc[-1]: sig = "🔄 WHALE RE-ENTRY"
            elif vol_hole.iloc[-1]: sig = "🕳️ VOLA HOLE"
            elif bull_trap.iloc[-1]: sig = "⛔"
            elif bear_trap.iloc[-1]: sig = "✅"
            elif exp_buy.iloc[-1]: sig = "💥 EXP BUY"
            elif exp_sel.iloc[-1]: sig = "💥 EXP SELL"
            elif w_pwr_q.iloc[-1] >= 85: sig = "🐋 WHALE IN"
            elif any_buy.iloc[-1]: sig = "✅ BUY"
            elif any_sel.iloc[-1]: sig = "🔴 SELL"
            else: sig = "⚪ WAIT"

            results.append({
                "Ticker": t, "Sinyal": sig, "Fiyat": f"${close.iloc[-1]:.2f}",
                "Whale Power": float(f"{w_pwr_q.iloc[-1]:.1f}"), "Fusion": int(total_score_b.iloc[-1])
            })
        except Exception:
            continue
            
    if results: return pd.DataFrame(results).sort_values(by="Fusion", ascending=False)
    return pd.DataFrame()

def style_signals(val):
    if isinstance(val, str):
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
    if isinstance(val, float):
        color = '#00ff88' if val > 0 else '#ff3333'
        return f'color: {color}; font-weight: bold;'
    return ''

# ==========================================
# 5. ANA EKRAN KOKPİTİ
# ==========================================
st.title("🏛️ AETHER MACRO SYSTEM")

# MAKRO TETİKLEYİCİLER
st.subheader("📡 Global Piyasalar & Akıllı Para Tetikleyicileri")
t_cols = st.columns(3)
for i, trig in enumerate(SYSTEM_TRIGGERS.keys()):
    with t_cols[i]:
        if st.button(f"Tetikle: {trig}", use_container_width=True):
            st.session_state.active_trigger = trig
            st.rerun()

active_data = SYSTEM_TRIGGERS.get(st.session_state.active_trigger, SYSTEM_TRIGGERS["COINCIDENT"])

col_news, col_map = st.columns([1, 2])
with col_news:
    st.markdown(f"<div style='color:{active_data['color']}; font-weight:bold; font-size:1.1rem; margin-bottom:10px;'>📰 {st.session_state.active_trigger} - Haber Akışı</div>", unsafe_allow_html=True)
    st.markdown("<div class='news-timeline'>", unsafe_allow_html=True)
    for news in active_data['news']: st.markdown(f"<div class='news-item'>{news}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
with col_map:
    draw_smart_money_flow(active_data)

st.divider()
st.subheader("🎯 Derin Sektör Taraması (Günlük)")

st.session_state.active_sector = st.selectbox("Sektörel derinliğe inmek için bir alan seçin:", list(GLOBAL_MAP.keys()))

if st.session_state.active_sector:
    sec = st.session_state.active_sector
    st.markdown(f"### 🔍 {sec} Ekosistemi")
    
    cur_chg, prev_chg, delta_icon, sec_news = get_sector_status(sec, st.session_state.active_trigger)
    c_info, c_batt = st.columns([1.5, 1])
    with c_info:
        box_color = "#00ff88" if cur_chg >= 75 else "#f1c40f" if cur_chg >= 45 else "#ff3333"
        st.markdown(f"""
            <div style="border-left: 4px solid {box_color}; padding: 15px; background: #111; border-radius: 5px; margin-bottom: 20px;">
                <strong style="color: {box_color};">Makro Etki Analizi:</strong><br>
                <span style="color: #e0e0e0;">{sec_news}</span>
            </div>
        """, unsafe_allow_html=True)
    with c_batt:
        draw_battery_with_delta(sec, cur_chg, prev_chg, delta_icon)

    etfs_in_sector = GLOBAL_MAP[sec]
    all_stocks = []
    for etf in etfs_in_sector:
        all_stocks.extend(ETF_INFO.get(etf, {}).get("stocks", []))
    all_stocks = list(set(all_stocks))
    
    with st.spinner(f"{sec} içindeki tüm hisseler analiz ediliyor..."):
        df_sector_all = calculate_signals(all_stocks)
        
        st.markdown("#### 📂 Alt Sektör Kırılımları ve Hisse Sinyalleri (Günlük)")
        for etf in etfs_in_sector:
            etf_data = ETF_INFO.get(etf, {"area": "Genel Kapsam", "stocks": []})
            with st.expander(f"📁 {etf} - {etf_data['area']}"):
                if not df_sector_all.empty:
                    df_etf_specific = df_sector_all[df_sector_all['Ticker'].isin(etf_data['stocks'])]
                    if not df_etf_specific.empty:
                        st.dataframe(df_etf_specific.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
                    else:
                        st.write("Veri oluşmadı.")
                else:
                    st.write("Veri alınamadı.")

# ==========================================
# 🚨 4H SEKTÖR & ALT SEKTÖR RADARI
# ==========================================
st.divider()
st.subheader("🌐 4H SEKTÖR & ALT SEKTÖR RADARI (WHALE & HOLE)")

all_etfs_to_scan = list(MAIN_SECTORS.keys()) + list(ETF_INFO.keys())
etf_name_map = {}
for k, v in MAIN_SECTORS.items(): etf_name_map[k] = v
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
            if not df_whale_4h.empty:
                st.dataframe(df_whale_4h.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
            else:
                st.info("Bulunamadı.")
                
        with c2:
            st.markdown("<h4 style='color: #9c27b0;'>🕳️ 4H Volatility Hole</h4>", unsafe_allow_html=True)
            if not df_hole_4h.empty:
                st.dataframe(df_hole_4h.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
            else:
                st.info("Bulunamadı.")

# ==========================================
# 🚨 OMNI RADAR (TÜM HİSSELER GÜNLÜK)
# ==========================================
st.divider()
st.subheader("🚨 OMNI RADAR: Özel Durum Taraması (Günlük Hisseler)")

all_market_stocks = []
ticker_to_area = {}

for etf, data in ETF_INFO.items():
    for ticker in data["stocks"]:
        all_market_stocks.append(ticker)
        ticker_to_area[ticker] = f"{etf} ({data['area']})"

all_market_stocks = list(set(all_market_stocks))

with st.spinner("Tüm piyasa (hisseler) günlük periyotta taranıyor..."):
    df_radar = calculate_signals(all_market_stocks, interval="1d")
    
    if not df_radar.empty:
        df_radar['Alt Sektör'] = df_radar['Ticker'].map(ticker_to_area)
        df_radar = df_radar[['Alt Sektör', 'Ticker', 'Sinyal', 'Fiyat', 'Whale Power', 'Fusion']]
        
        df_whale = df_radar[df_radar['Sinyal'] == '🔄 WHALE RE-ENTRY']
        df_hole = df_radar[df_radar['Sinyal'] == '🕳️ VOLA HOLE']
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("<h4 style='color: #00bcd4;'>🔄 Whale Re-Entry Hisseler</h4>", unsafe_allow_html=True)
            if not df_whale.empty:
                st.dataframe(df_whale.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
            else:
                st.info("Bulunamadı.")
                
        with col_r2:
            st.markdown("<h4 style='color: #9c27b0;'>🕳️ Volatility Hole Hisseler</h4>", unsafe_allow_html=True)
            if not df_hole.empty:
                st.dataframe(df_hole.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
            else:
                st.info("Bulunamadı.")

# ==========================================
# MÜKEMMEL PORTFÖY MODÜLÜ
# ==========================================
st.divider()
st.subheader("📋 Genel Portföy İzleme Listesi (Fair Value Analizi)")

raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]
portfolio_tickers = sorted(list(set(raw_tickers)))

with st.spinner("Portföy simülasyonu ve veriler hesaplanıyor..."):
    df_port = calculate_signals(portfolio_tickers, interval="1d")
    if not df_port.empty:
        df_port['Fair Value'] = df_port['Fiyat'].apply(lambda x: f"${float(x[1:]) * np.random.uniform(0.9, 1.2):.2f}")
        df_port['1 Gün (%)'] = [round(np.random.uniform(-5, 5), 2) for _ in range(len(df_port))]
        df_port['1 Hafta (%)'] = [round(np.random.uniform(-15, 20), 2) for _ in range(len(df_port))]
        
        df_port = df_port[['Ticker', 'Sinyal', 'Fiyat', 'Fair Value', '1 Gün (%)', '1 Hafta (%)', 'Whale Power', 'Fusion']]
        
        st.dataframe(
            df_port.style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']),
            use_container_width=True, height=600, hide_index=True
        )
