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
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION V127.6", page_icon="🏛️")

st.markdown("""
    <style>
    /* Ana Arka Plan ve Metinler */
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    p, h1, h2, h3, h4, h5, h6, span, label, div { color: #e0e0e0 !important; }
    
    /* Selectbox (Açılır Menü) - Beyaz Üzeri Gri Sorununun Çözümü */
    div[data-baseweb="select"] > div { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #444 !important; }
    div[data-baseweb="popover"] > div { background-color: #1a1a1a !important; }
    ul[role="listbox"] { background-color: #1a1a1a !important; }
    ul[role="listbox"] li { color: #ffffff !important; background-color: #1a1a1a !important; }
    ul[role="listbox"] li:hover { background-color: #333333 !important; color: #00ff88 !important; }
    
    /* Dataframe ve Tablo Görünümleri */
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; color: #ffffff !important; }
    
    /* Expander (Açılır Sekmeler) */
    [data-testid="stExpander"] { background-color: #111111 !important; border: 1px solid #333 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary p { color: #00ff88 !important; font-weight: bold !important; font-size: 1.1rem !important; }
    
    /* Butonlar */
    div.stButton > button { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #444 !important; border-radius: 8px !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    
    /* Özel Kutular */
    .deep-analysis-box { background: linear-gradient(145deg, #111 0%, #1a1a1a 100%); border-left: 4px solid #f1c40f; padding: 20px; border-radius: 5px; font-size: 0.95rem; line-height: 1.6; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.5); }
    .deep-analysis-title { color: #f1c40f !important; font-size: 1.2rem; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
    .news-timeline { border-left: 2px solid #444; margin-left: 10px; padding-left: 15px; }
    .news-item { margin-bottom: 15px; position: relative; }
    .news-item::before { content: ''; position: absolute; left: -21px; top: 5px; width: 10px; height: 10px; border-radius: 50%; background-color: #00ff88; }
    .battery-container { width: 100%; background-color: #222; border-radius: 10px; margin: 5px 0 15px 0; border: 1px solid #444; position: relative; height: 25px; overflow: hidden; }
    .battery-fill { height: 100%; border-radius: 8px; transition: width 0.5s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-weight: bold; color: #000 !important; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

if 'active_trigger' not in st.session_state: 
    st.session_state.active_trigger = "NEUTRAL"
if 'active_sector' not in st.session_state: 
    st.session_state.active_sector = None

# ==========================================
# 1. GENİŞLETİLMİŞ VERİ HARİTASI
# ==========================================
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

# ==========================================
# 2. MAKRO TETİKLEYİCİLER & SEKTÖR MOTORU
# ==========================================
SYSTEM_TRIGGERS = {
    "GEOPOLITIK": {
        "color": "#ff3333", "impact": "risk_off",
        "news": [
            "T-3: Enerji nakil hatlarına yönelik sabotaj iddiaları piyasayı gerdi.",
            "T-2: Merkez bankaları stratejik rezervleri kullanıma açabileceğini sinyalledi.",
            "BUGÜN: Nakliye rotalarında sigorta primleri %40 arttı. Sıkışmış yay etkisi birikiyor."
        ],
        "analysis": "Yüzeydeki düşük volatilite yanıltıcıdır. Savunma ve Enerji hisselerinde rotasyon hızlanırken, Teknoloji'den (XLK) para çıkışı görülüyor. Put-call skew oranları yüksek; piyasa aşağı yönlü sürpriz bir şoka hazırlanıyor olabilir.",
        "battery": {"Stocks": 30, "Bonds": 80, "Crypto": 25, "Commodities": 95, "RealEstate": 45}
    },
    "LEADING": {
        "color": "#00ff88", "impact": "risk_on",
        "news": [
            "T-3: İmalat PMI verileri son 8 ayın zirvesine tırmandı.",
            "T-2: Yapay Zeka (AI) yatırımlarında donanım siparişleri beklentileri ikiye katladı.",
            "BUGÜN: Tüketici güveni güçlü. Piyasa yeni bir breakout (kırılım) arayışında."
        ],
        "analysis": "Ekonomik öncü göstergeler ralli öncesi güç toplamaya (coiled spring) işaret ediyor. Likidite döngüsü hızlanıyor. Özellikle AI altyapısı, Veri Merkezleri (SRVR) ve bu merkezleri besleyen Nükleer Enerji (URA) sektörlerinde ciddi şarj (para girişi) var.",
        "battery": {"Stocks": 90, "Bonds": 30, "Crypto": 85, "Commodities": 60, "RealEstate": 70}
    },
    "COINCIDENT": {
        "color": "#f1c40f", "impact": "neutral_mixed",
        "news": [
            "T-3: İstihdam verileri güçlü ancak saatlik kazançlar stabil.",
            "T-2: Merkez bankası tutanaklarında 'bekle ve gör' vurgusu öne çıktı.",
            "BUGÜN: Piyasada belirgin bir yön yok, eşit ağırlıklı fonlara geçiş var."
        ],
        "analysis": "Yatay piyasada whipsaw (sahte kırılım) riski çok yüksek. Mega-cap hisselerden çıkıp temettü ve değer hisselerine rotasyon yaşanıyor. Bu dönemde covered call (prim toplama) stratejileri öne çıkıyor.",
        "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 45, "Commodities": 55, "RealEstate": 50}
    }
}

def get_sector_status(sector_name, trigger):
    base_charge = 50
    news = ""
    if trigger == "GEOPOLITIK":
        if any(x in sector_name for x in ["Enerji", "Sanayi", "Materyal"]):
            base_charge = np.random.randint(75, 95)
            prev = base_charge - np.random.randint(10, 25)
            news = f"Küresel arz endişeleri ve tedarik zinciri sıkıntıları, {sector_name} tarafında fiyatlama gücünü artırıyor. Akıllı para, risk-off ortamında bu sektörü güvenli liman (hedge) olarak kullanıyor."
        elif any(x in sector_name for x in ["Teknoloji", "Tüketim"]):
            base_charge = np.random.randint(20, 45)
            prev = base_charge + np.random.randint(10, 25)
            news = f"Artan jeopolitik riskler ve belirsizlik, yüksek çarpanlı {sector_name} hisselerinden çıkışlara (deşarj) neden oluyor. Yatırımcılar risk iştahını kapatmış durumda."
        else:
            base_charge = np.random.randint(40, 60)
            prev = base_charge + np.random.randint(-5, 5)
            news = f"{sector_name} mevcut jeopolitik sarsıntılardan sınırlı etkilenerek yatay bir bantta (trading range) sıkışmış durumda."
    elif trigger == "LEADING":
        if any(x in sector_name for x in ["Teknoloji", "Enerji", "Gayrimenkul"]):
            base_charge = np.random.randint(80, 98)
            prev = base_charge - np.random.randint(15, 30)
            news = f"Güçlü öncü göstergeler ve AI devrimi, {sector_name} sektöründe devasa bir fon girişini tetikledi. Opsiyon piyasasındaki alımlar (call skew) breakout ihtimalini güçlendiriyor."
        else:
            base_charge = np.random.randint(45, 65)
            prev = base_charge - np.random.randint(5, 15)
            news = f"Risk iştahının artmasıyla defansif alanlardan çıkan para, yavaş yavaş {sector_name} sektöründe de toparlanma emareleri gösteriyor."
    else: 
        base_charge = np.random.randint(45, 65)
        prev = base_charge + np.random.randint(-10, 10)
        news = f"Piyasadaki aşırı sakinlik (whipsaw tehlikesi) nedeniyle {sector_name} sektöründe fon yöneticileri bekle-gör stratejisi uyguluyor. Kararsız para giriş-çıkışları mevcut."
        
    delta_icon = "⬆️ Şarj Oluyor" if base_charge > prev else "⬇️ Deşarj Oluyor" if base_charge < prev else "➖ Stabil"
    return base_charge, prev, delta_icon, news

# ==========================================
# 3. GÖRSEL MOTORLAR
# ==========================================
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
    
    # Yüksek çözünürlük, sığdırma (size) kısıtlamasının kaldırılması
    dot.attr(bgcolor='#050505', rankdir='LR', dpi='300')
    dot.attr('node', fontsize='28', fontname='Arial', margin='0.3,0.1')
    dot.attr('edge', fontsize='24')
    
    with dot.subgraph(name='cluster_0') as c:
        c.attr(style='dashed', color='#555', label='Kaydi Varlıklar', fontcolor='#e0e0e0', fontsize='36')
        c.node("FIAT", "Fiat\nCurrency", shape='ellipse', style='filled', fillcolor='#4a148c', fontcolor='white')
        c.node("USD", "USD\n(Merkez)", shape='circle', style='filled', fillcolor='#0277bd', fontcolor='white', width='2.5', fixedsize='true')
        c.node("STOCK", "Borsalar", shape='box', style='filled', fillcolor='#f57f17', fontcolor='white', height='1.5')
        c.node("BOND", "Tahviller", shape='box', style='filled', fillcolor='#2e7d32', fontcolor='white', height='1.5')
        c.node("CRYPTO", "Kripto", shape='box', style='filled', fillcolor='#d81b60', fontcolor='white', height='1.5')
        
    with dot.subgraph(name='cluster_1') as c:
        c.attr(style='dashed', color='#555', label='Maddi Varlıklar', fontcolor='#e0e0e0', fontsize='36')
        c.node("COMM", "Emtia &\nEnerji", shape='circle', style='filled', fillcolor='#00695c', fontcolor='white', width='2.4', fixedsize='true')
        c.node("GOLD", "Değer\nSaklama", shape='circle', style='filled', fillcolor='#fbc02d', fontcolor='black', width='2.4', fixedsize='true')
        c.node("REAL", "Gayrimenkul", shape='box', style='filled', fillcolor='#827717', fontcolor='white', height='1.5')

    bat = trigger_data['battery']
    def get_pen(val): return str(max(3.0, val / 6))
    def get_col(val): return "#00ff88" if val >= 60 else "#ff3333" if val <= 40 else "#888"

    dot.edge("FIAT", "USD", color="#aaa", penwidth="5")
    dot.edge("USD", "STOCK", color=get_col(bat['Stocks']), penwidth=get_pen(bat['Stocks']))
    dot.edge("USD", "BOND", color=get_col(bat['Bonds']), penwidth=get_pen(bat['Bonds']))
    dot.edge("USD", "CRYPTO", color=get_col(bat['Crypto']), penwidth=get_pen(bat['Crypto']))
    
    comm_avg = bat['Commodities'] + 10
    dot.edge("USD", "COMM", color=get_col(comm_avg), penwidth=get_pen(comm_avg))
    dot.edge("USD", "GOLD", color=get_col(bat['Commodities']), penwidth=get_pen(bat['Commodities']))
    dot.edge("COMM", "REAL", color=get_col(bat['RealEstate']), penwidth=get_pen(bat['RealEstate']), style="dashed")
    
    st.graphviz_chart(dot, use_container_width=True)

def draw_rrg_chart():
    data = []
    for sec in GLOBAL_MAP.keys():
        rs, mom = np.random.uniform(93, 140), np.random.uniform(85, 115)
        quad = "Leading" if rs>=100 and mom>=100 else "Weakening" if rs>=100 else "Lagging" if mom<100 else "Improving"
        data.append({"Sektör": sec, "RS": rs, "Momentum": mom, "Durum": quad})
        
    df_rrg = pd.DataFrame(data)
    fig = go.Figure()

    fig.add_shape(type="rect", x0=93, y0=100, x1=100, y1=118, fillcolor="rgba(0,100,255,0.1)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=100, y0=100, x1=145, y1=118, fillcolor="rgba(0,255,0,0.1)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=93, y0=84, x1=100, y1=100, fillcolor="rgba(255,0,0,0.1)", line_width=0, layer="below")
    fig.add_shape(type="rect", x0=100, y0=84, x1=145, y1=100, fillcolor="rgba(255,165,0,0.1)", line_width=0, layer="below")

    fig.add_hline(y=100, line_dash="dash", line_color="#888")
    fig.add_vline(x=100, line_dash="dash", line_color="#888")

    for quad, color in zip(["Leading", "Weakening", "Lagging", "Improving"], ["#00ff88", "#fbc02d", "#ff3333", "#03a9f4"]):
        df_sub = df_rrg[df_rrg["Durum"] == quad]
        fig.add_trace(go.Scatter(x=df_sub["RS"], y=df_sub["Momentum"], mode='markers+text', 
            marker=dict(size=14, color=color, line=dict(width=2, color='white')),
            text=df_sub["Sektör"].apply(lambda x: x.split(" ")[1]), textposition="top center", name=quad))

    fig.update_layout(title="Sektörel Relative Rotation Graph (RRG)", xaxis_title="Relative Strength (RS) > 100", yaxis_title="RS Momentum > 100", xaxis=dict(range=[93, 145]), yaxis=dict(range=[84, 118]), height=500, paper_bgcolor="#050505", plot_bgcolor="#111", font=dict(color="#e0e0e0"))
    return fig, df_rrg

# ==========================================
# 4. YFINANCE OMNI FUSION (VEKTÖREL MOTOR)
# ==========================================
@st.cache_data(ttl=900)
def calculate_signals(ticker_list):
    if not ticker_list: return pd.DataFrame()
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    try:
        raw_data = yf.download(ticker_list, start=start_date, end=end_date, group_by='ticker', progress=False)
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
                
            if len(df) < 30: continue

            close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
            
            # Whale Power Calculation
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(20).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(20).mean()
            rsi_20 = 100 - (100 / (1 + (gain / loss.replace(0, 0.001))))
            
            c_range = (high - low).clip(lower=0.001)
            delta_q = ((close - low) - (high - close)) / c_range
            vol_sma = vol.rolling(20).mean().clip(lower=0.001)
            delta_vol_q = (delta_q * vol).rolling(20).mean() / vol_sma
            rvol = (vol / vol_sma.clip(lower=1)).clip(upper=2.5)
            
            base_pwr = ((rsi_20 - 50) + (delta_vol_q * 50)) * rvol * 1.5
            logic_pwr = np.log(1 + np.exp(base_pwr / 5)) * 5
            logic_pwr = np.where((low > high.shift(2)) & (close > open_p), logic_pwr + 35, logic_pwr)
            
            wp = np.minimum((np.log10(1 + np.clip(logic_pwr, 0, None)) * 65)**0.8 * 1.8, 100)
            df['wp'] = pd.Series(wp, index=df.index).fillna(0)
            
            # Whale Re-Entry
            df['wp_ma'] = df['wp'].rolling(9).mean()
            curr_wp, curr_ma = df['wp'].iloc[-1], df['wp_ma'].iloc[-1]
            is_reentry = (curr_wp > curr_ma) and (df['wp'].iloc[-2] <= df['wp_ma'].iloc[-2]) and (curr_wp > 40) and (vol.iloc[-1] > vol_sma.iloc[-1] * 1.2)

            # Volatility Hole & Squeeze
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            b_up, b_low = sma20 + 2*std20, sma20 - 2*std20
            
            tr = pd.concat([high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1).max(axis=1)
            k_up, k_low = sma20 + 1.5*tr.rolling(14).mean(), sma20 - 1.5*tr.rolling(14).mean()
            
            is_sqz = (b_low > k_low) & (b_up < k_up)
            vol_hole = is_sqz & (close <= (sma20 - ((k_up - sma20)/3.0)))
            
            # Traps
            ema3 = close.ewm(span=3, adjust=False).mean()
            is_bear_trap = ((low < ema3) & (close > ema3) & (vol > vol_sma * 1.8)) | (vol_hole & (low < low.shift(1)) & (close > open_p))
            is_bull_trap = ((high > ema3) & (close < ema3) & (vol > vol_sma * 1.8)) | ((~vol_hole) & (close > k_up * 1.1) & (close < open_p))

            # EXP Ignition
            macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
            exp_buy = (~is_sqz) & is_sqz.shift(1) & (macd > macd.rolling(9).mean()) & (macd > 0)
            exp_sel = (~is_sqz) & is_sqz.shift(1) & (macd < macd.rolling(9).mean()) & (macd < 0)

            # Scoring
            fs = 0
            if close.iloc[-1] > ema3.iloc[-1]: fs += 1
            if curr_wp > 50: fs += 2
            if vol.iloc[-1] > vol_sma.iloc[-1] * 1.5: fs += 1

            # Hiyerarşi
            if curr_wp >= 85 and fs >= 3: sig = "☄️ HYPER BUY"
            elif curr_wp <= 15 and fs <= 1: sig = "☄️ HYPER SELL"
            elif is_bull_trap.iloc[-1]: sig = "⛔"
            elif is_bear_trap.iloc[-1]: sig = "✅"
            elif is_reentry: sig = "🔄 WHALE RE-ENTRY"
            elif exp_buy.iloc[-1]: sig = "💥 EXP BUY"
            elif exp_sel.iloc[-1]: sig = "💥 EXP SELL"
            elif vol_hole.iloc[-1]: sig = "🕳️ VOLA HOLE"
            elif curr_wp > 75: sig = "🐋 WHALE IN"
            elif fs >= 3: sig = "✅ BUY"
            elif fs <= 1: sig = "🔴 SELL"
            else: sig = "⚪ WAIT"

            results.append({
                "Ticker": t, "Sinyal": sig, "Fiyat": f"${close.iloc[-1]:.2f}",
                "Whale Power": float(f"{curr_wp:.1f}"), "Fusion": fs
            })
        except Exception:
            continue
            
    if results: return pd.DataFrame(results).sort_values(by="Fusion", ascending=False)
    return pd.DataFrame()

# Pandas Styler Sinyal Renklendirme
def style_signals(val):
    if isinstance(val, str):
        if 'HYPER BUY' in val: return 'background-color: #ffeb3b; color: #000000 !important; font-weight: bold;'
        if 'HYPER SELL' in val: return 'background-color: #880e4f; color: #ffffff !important; font-weight: bold;'
        if 'WHALE RE-ENTRY' in val: return 'background-color: #00bcd4; color: #000000 !important; font-weight: bold;'
        if 'WHALE IN' in val: return 'background-color: #01579b; color: #ffffff !important;'
        if 'VOLA HOLE' in val: return 'background-color: #6a1b9a; color: #ffffff !important;'
        if 'EXP BUY' in val: return 'background-color: #00e676; color: #000000 !important; font-weight: bold;'
        if 'EXP SELL' in val: return 'background-color: #ff3d00; color: #ffffff !important; font-weight: bold;'
        if 'BUY' in val: return 'background-color: #1b5e20; color: #00ff88 !important; font-weight: bold;'
        if 'SELL' in val: return 'background-color: #440000; color: #ff3333 !important; font-weight: bold;'
        if val == '⛔': return 'background-color: #b71c1c; color: #ffffff !important; font-size: 1.2rem; text-align: center;'
        if val == '✅': return 'background-color: #004d40; color: #ffffff !important; font-size: 1.2rem; text-align: center;'
    return 'background-color: #222222; color: #ffffff !important;'

def style_percentages(val):
    if isinstance(val, float):
        color = '#00ff88' if val > 0 else '#ff3333'
        return f'color: {color} !important; font-weight: bold;'
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

# HABER VE HARİTA
col_news, col_map = st.columns([1, 2])
with col_news:
    st.markdown(f"<div style='color:{active_data['color']}; font-weight:bold; font-size:1.1rem; margin-bottom:10px;'>📰 {st.session_state.active_trigger} - Haber Akışı</div>", unsafe_allow_html=True)
    st.markdown("<div class='news-timeline'>", unsafe_allow_html=True)
    for news in active_data['news']: st.markdown(f"<div class='news-item'>{news}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
with col_map:
    draw_smart_money_flow(active_data)

st.divider()

# --- RRG VE DERİN SEKTÖR ANALİZİ ---
st.subheader("🎯 Sektörel Rotasyon Grafiği (RRG) & Derin Tarama")
fig_rrg, df_rrg_data = draw_rrg_chart()
st.plotly_chart(fig_rrg, use_container_width=True)

st.session_state.active_sector = st.selectbox("Sektörel derinliğe inmek için bir alan seçin:", list(GLOBAL_MAP.keys()))

if st.session_state.active_sector:
    sec = st.session_state.active_sector
    st.markdown(f"### 🔍 {sec} Ekosistemi")
    
    # Haberler ve Pil
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

    # Toplu İndirme
    etfs_in_sector = GLOBAL_MAP[sec]
    all_stocks = []
    for etf in etfs_in_sector:
        all_stocks.extend(ETF_INFO.get(etf, {}).get("stocks", []))
    all_stocks = list(set(all_stocks))
    
    with st.spinner(f"{sec} içindeki tüm hisseler analiz ediliyor..."):
        df_sector_all = calculate_signals(all_stocks)
        
        st.markdown("#### 📂 Alt Sektör Kırılımları ve Hisse Sinyalleri")
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

# --- MÜKEMMEL PORTFÖY MODÜLÜ ---
st.divider()
st.subheader("📋 Genel Portföy İzleme Listesi (Fair Value Analizi)")

raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]
portfolio_tickers = sorted(list(set(raw_tickers)))

with st.spinner("Portföy simülasyonu ve veriler hesaplanıyor..."):
    df_port = calculate_signals(portfolio_tickers)
    if not df_port.empty:
        # Fair Value ve Değişimleri Simüle Ediyoruz
        df_port['Fair Value'] = df_port['Fiyat'].apply(lambda x: f"${float(x[1:]) * np.random.uniform(0.9, 1.2):.2f}")
        df_port['1 Gün (%)'] = [round(np.random.uniform(-5, 5), 2) for _ in range(len(df_port))]
        df_port['1 Hafta (%)'] = [round(np.random.uniform(-15, 20), 2) for _ in range(len(df_port))]
        
        # Sütun sırasını düzenle
        df_port = df_port[['Ticker', 'Sinyal', 'Fiyat', 'Fair Value', '1 Gün (%)', '1 Hafta (%)', 'Whale Power', 'Fusion']]
        
        st.dataframe(
            df_port.style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']),
            use_container_width=True, height=600, hide_index=True
        )
    else:
        st.error("Yfinance sunucularından veri alınamadı.")
