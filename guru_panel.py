import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime, timedelta

# ==========================================
# 0. AYARLAR & KESİN DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION V127.5", page_icon="🏛️")

st.markdown("""
    <style>
    /* KESİN KARANLIK TEMA ZORLAMALARI */
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    p, h1, h2, h3, h4, h5, h6, span, label, div { color: #e0e0e0 !important; }
    
    /* Dataframe ve Tablo Görünümleri */
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; color: #ffffff !important; }
    
    /* Expander (Açılır Menü) ve Selectbox İçerikleri */
    [data-testid="stExpander"] { background-color: #111111 !important; border: 1px solid #333 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary p { color: #00ff88 !important; font-weight: bold !important; }
    .stSelectbox label { color: #f1c40f !important; font-weight: bold; }
    
    /* Butonlar */
    div.stButton > button { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #444 !important; border-radius: 8px !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    
    /* Özel Kutu Tasarımları */
    .deep-analysis-box { background: linear-gradient(145deg, #111 0%, #1a1a1a 100%); border-left: 4px solid #f1c40f; padding: 20px; border-radius: 5px; font-size: 0.95rem; line-height: 1.6; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .deep-analysis-title { color: #f1c40f !important; font-size: 1.2rem; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
    .news-timeline { border-left: 2px solid #444; margin-left: 10px; padding-left: 15px; }
    .news-item { margin-bottom: 15px; position: relative; }
    .news-item::before { content: ''; position: absolute; left: -21px; top: 5px; width: 10px; height: 10px; border-radius: 50%; background-color: #00ff88; }
    
    /* Batarya Sistemi */
    .battery-container { width: 100%; background-color: #222; border-radius: 10px; margin: 5px 0 15px 0; border: 1px solid #444; position: relative; height: 25px; overflow: hidden; }
    .battery-fill { height: 100%; border-radius: 8px; transition: width 0.5s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-weight: bold; color: #000 !important; font-size: 0.85rem; }
    </style>
""", unsafe_allow_html=True)

if 'active_trigger' not in st.session_state: st.session_state.active_trigger = "NEUTRAL"
if 'active_sector' not in st.session_state: st.session_state.active_sector = None

# ==========================================
# 1. VERİ HARİTASI (GLOBAL MAP & ETF INFO)
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
    "SMH": {"area": "Yarı İletken Devleri & Çip Üretimi", "stocks": ["NVDA", "TSM", "AVGO", "ASML", "AMD", "MU", "INTC"]},
    "SOXX": {"area": "Global Çip Ekosistemi", "stocks": ["TXN", "AMAT", "QCOM", "ADI", "MCHP", "CRDO"]},
    "BOTZ": {"area": "Robotik Sistemler & Endüstriyel AI", "stocks": ["ISRG", "ABB", "PATH", "TER"]},
    "CIBR": {"area": "Siber Güvenlik", "stocks": ["PANW", "CRWD", "FTNT", "NET", "ZS"]},
    "IGV": {"area": "Bulut Yazılım & SaaS", "stocks": ["ADBE", "CRM", "MSFT", "NOW", "SNOW"]},
    "ARKF": {"area": "FinTech & Dijital Ödeme", "stocks": ["COIN", "SQ", "MELI", "HOOD", "PYPL"]},
    "ITA": {"area": "Havacılık & Savunma", "stocks": ["RTX", "LMT", "BA", "GD", "NOC"]},
    "XAR": {"area": "Gelişmiş Uzay Teknolojileri", "stocks": ["GE", "RKLB", "SPCE", "ASTS"]},
    "IYT": {"area": "Lojistik & Kargo", "stocks": ["UNP", "UPS", "UBER", "FDX", "DAL"]},
    "PAVE": {"area": "Altyapı & İnşaat", "stocks": ["ETN", "URI", "DE", "CAT"]},
    "XOP": {"area": "Petrol & Doğalgaz", "stocks": ["XOM", "CVX", "COP", "OXY", "DVN"]},
    "OIH": {"area": "Petrol Servisleri", "stocks": ["SLB", "HAL", "BKR", "VLO"]},
    "URA": {"area": "Nükleer Enerji & Uranyum", "stocks": ["CCJ", "UUUU", "SMR", "CEG", "VST"]},
    "ICLN": {"area": "Temiz Enerji", "stocks": ["FSLR", "ENPH", "PLUG", "NEE"]},
    "TAN": {"area": "Güneş Enerjisi", "stocks": ["SEDG", "RUN", "SHLS"]},
    "XBI": {"area": "Biyoteknoloji", "stocks": ["MRNA", "VRTX", "AMGN", "GILD"]},
    "IHI": {"area": "Tıbbi Cihazlar", "stocks": ["ABT", "MDT", "SYK", "BSX"]},
    "KRE": {"area": "Bölgesel Bankalar", "stocks": ["NYCB", "WAL", "ZION", "CMA"]},
    "KIE": {"area": "Sigortacılık", "stocks": ["CB", "PGR", "ALL", "TRV"]},
    "XRT": {"area": "Perakende", "stocks": ["AMZN", "COST", "WMT", "TGT"]},
    "XME": {"area": "Metaller & Madencilik", "stocks": ["FCX", "NUE", "STLD", "AA", "ALAB"]},
    "LIT": {"area": "Lityum & Batarya", "stocks": ["ALB", "SQM", "TSLA"]},
    "GDX": {"area": "Altın Madencileri", "stocks": ["NEM", "GOLD", "AEM"]},
    "SOCL": {"area": "Sosyal Medya", "stocks": ["META", "GOOG", "SNAP", "PINS"]},
    "SRVR": {"area": "Veri Merkezleri (REIT)", "stocks": ["EQIX", "AMT", "DLR"]},
    "PHO": {"area": "Su Teknolojileri", "stocks": ["AWK", "XYL", "AWR"]}
}

# ==========================================
# 2. MAKRO TETİKLEYİCİLER & SEKTÖR ETKİ MOTORU
# ==========================================
SYSTEM_TRIGGERS = {
    "GEOPOLITIK": {
        "color": "#ff3333", "impact": "risk_off",
        "news": [
            "T-3: Enerji nakil hatlarına yönelik sabotaj iddiaları piyasayı gerdi.",
            "T-2: Merkez bankaları stratejik rezervleri kullanıma açabileceğini sinyalledi.",
            "BUGÜN: Nakliye rotalarında sigorta primleri %40 arttı. Sıkışmış yay (coiled spring) etkisi birikiyor."
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
        "analysis": "Ekonomik öncü göstergeler ralli öncesi güç toplamaya (coiled spring) işaret ediyor. Likidite döngüsü hızlanıyor. Özellikle AI altyapısı, Veri Merkezleri (SRVR) ve bu veri merkezlerini besleyen Nükleer Enerji (URA) sektörlerinde ciddi şarj (para girişi) var.",
        "battery": {"Stocks": 90, "Bonds": 30, "Crypto": 85, "Commodities": 60, "RealEstate": 70}
    },
    "COINCIDENT": {
        "color": "#f1c40f", "impact": "neutral_mixed",
        "news": [
            "T-3: İstihdam verileri güçlü ancak saatlik kazançlar stabil.",
            "T-2: Merkez bankası tutanaklarında 'bekle ve gör' vurgusu öne çıktı.",
            "BUGÜN: Piyasada belirgin bir yön yok, eşit ağırlıklı (equal-weight) fonlara geçiş var."
        ],
        "analysis": "Yatay piyasada whipsaw (sahte kırılım) riski çok yüksek. Mega-cap hisselerden çıkıp temettü ve değer hisselerine rotasyon yaşanıyor. Bu dönemde covered call (prim toplama) stratejileri öne çıkıyor.",
        "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 45, "Commodities": 55, "RealEstate": 50}
    }
}

def get_sector_status(sector_name, trigger):
    # Makro duruma göre sektörel şarj, geçmiş şarj ve özel haber metni üretir
    base_charge = 50
    news = ""
    
    if trigger == "GEOPOLITIK":
        if "Enerji" in sector_name or "Sanayi" in sector_name or "Materyal" in sector_name:
            base_charge = np.random.randint(75, 95)
            prev = base_charge - np.random.randint(10, 25)
            news = f"Küresel arz endişeleri ve tedarik zinciri sıkıntıları, {sector_name} tarafında fiyatlama gücünü artırıyor. Akıllı para, risk-off ortamında bu sektörü güvenli liman (hedge) olarak kullanıyor."
        elif "Teknoloji" in sector_name or "Tüketim" in sector_name:
            base_charge = np.random.randint(20, 45)
            prev = base_charge + np.random.randint(10, 25)
            news = f"Artan jeopolitik riskler ve belirsizlik, yüksek çarpanlı {sector_name} hisselerinden çıkışlara (deşarj) neden oluyor. Yatırımcılar risk iştahını kapatmış durumda."
        else:
            base_charge = np.random.randint(40, 60)
            prev = base_charge + np.random.randint(-5, 5)
            news = f"{sector_name} mevcut jeopolitik sarsıntılardan sınırlı etkilenerek yatay bir bantta (trading range) sıkışmış durumda."
            
    elif trigger == "LEADING":
        if "Teknoloji" in sector_name or "Enerji" in sector_name or "Gayrimenkul" in sector_name:
            base_charge = np.random.randint(80, 98)
            prev = base_charge - np.random.randint(15, 30)
            news = f"Güçlü öncü göstergeler ve AI devrimi, {sector_name} sektöründe devasa bir fon girişini tetikledi. Opsiyon piyasasındaki alımlar (call skew) breakout ihtimalini güçlendiriyor."
        else:
            base_charge = np.random.randint(45, 65)
            prev = base_charge - np.random.randint(5, 15)
            news = f"Risk iştahının artmasıyla defansif alanlardan çıkan para, yavaş yavaş {sector_name} sektöründe de toparlanma emareleri gösteriyor."
            
    else: # COINCIDENT
        base_charge = np.random.randint(45, 65)
        prev = base_charge + np.random.randint(-10, 10)
        news = f"Piyasadaki aşırı sakinlik (whipsaw tehlikesi) nedeniyle {sector_name} sektöründe fon yöneticileri bekle-gör stratejisi uyguluyor. Kararsız para giriş-çıkışları mevcut."
        
    delta_icon = "⬆️ Şarj Oluyor" if base_charge > prev else "⬇️ Deşarj Oluyor" if base_charge < prev else "➖ Stabil"
    return base_charge, prev, delta_icon, news

# ==========================================
# 3. GÖRSEL MOTORLAR (ŞARJ & HARİTA)
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
    dot.attr(bgcolor='#050505', rankdir='LR', size='10,6')
    
    with dot.subgraph(name='cluster_0') as c:
        c.attr(style='dashed', color='#555', label='Kaydi Varlıklar', fontcolor='#e0e0e0')
        c.node("FIAT", "Fiat Currency", shape='ellipse', style='filled', fillcolor='#4a148c', fontcolor='white')
        c.node("USD", "USD (Merkez)", shape='circle', style='filled', fillcolor='#0277bd', fontcolor='white', width='1.2')
        c.node("STOCK", "Borsalar", shape='box', style='filled', fillcolor='#f57f17', fontcolor='white')
        c.node("BOND", "Tahviller", shape='box', style='filled', fillcolor='#2e7d32', fontcolor='white')
        c.node("CRYPTO", "Kripto", shape='box', style='filled', fillcolor='#d81b60', fontcolor='white')
        
    with dot.subgraph(name='cluster_1') as c:
        c.attr(style='dashed', color='#555', label='Maddi Varlıklar', fontcolor='#e0e0e0')
        c.node("COMM", "Emtia & Enerji", shape='circle', style='filled', fillcolor='#00695c', fontcolor='white')
        c.node("GOLD", "Değer Saklama", shape='circle', style='filled', fillcolor='#fbc02d', fontcolor='black')
        c.node("REAL", "Gayrimenkul", shape='box', style='filled', fillcolor='#827717', fontcolor='white', height='2')

    bat = trigger_data['battery']
    def get_pen(val): return str(max(1, val / 15))
    def get_col(val): return "#00ff88" if val >= 60 else "#ff3333" if val <= 40 else "#888"

    dot.edge("FIAT", "USD", color="#aaa", penwidth="2")
    dot.edge("USD", "STOCK", color=get_col(bat['Stocks']), penwidth=get_pen(bat['Stocks']))
    dot.edge("USD", "BOND", color=get_col(bat['Bonds']), penwidth=get_pen(bat['Bonds']))
    dot.edge("USD", "CRYPTO", color=get_col(bat['Crypto']), penwidth=get_pen(bat['Crypto']))
    
    comm_avg = bat['Commodities'] + 10
    dot.edge("USD", "COMM", color=get_col(comm_avg), penwidth=get_pen(comm_avg))
    dot.edge("USD", "GOLD", color=get_col(bat['Commodities']), penwidth=get_pen(bat['Commodities']))
    dot.edge("COMM", "REAL", color=get_col(bat['RealEstate']), penwidth=get_pen(bat['RealEstate']), style="dashed")
    
    st.graphviz_chart(dot)

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
            cond = (low > high.shift(2)) & (close > open_p)
            logic_pwr = np.where(cond, logic_pwr + 35, logic_pwr)
            
            log_w = np.log10(1 + np.clip(logic_pwr, a_min=0, a_max=None))
            wp = np.minimum((log_w * 65)**0.8 * 1.8, 100)
            df['wp'] = pd.Series(wp, index=df.index).fillna(0)
            
            # Whale Re-Entry
            df['wp_ma'] = df['wp'].rolling(9).mean()
            curr_wp, prev_wp = df['wp'].iloc[-1], df['wp'].iloc[-2]
            curr_ma, prev_ma = df['wp_ma'].iloc[-1], df['wp_ma'].iloc[-2]
            is_reentry = (curr_wp > curr_ma) and (prev_wp <= prev_ma) and (curr_wp > 40) and (vol.iloc[-1] > vol_sma.iloc[-1] * 1.2)

            # Volatility Hole (Daralma)
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            b_up, b_low = sma20 + 2*std20, sma20 - 2*std20
            
            tr = pd.concat([high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1).max(axis=1)
            k_up, k_low = sma20 + 1.5*tr.rolling(14).mean(), sma20 - 1.5*tr.rolling(14).mean()
            
            is_sqz = (b_low > k_low) & (b_up < k_up)
            vol_hole = is_sqz & (close <= (sma20 - ((k_up - sma20)/3.0)))
            
            # Traps (Tuzaklar)
            ema3 = close.ewm(span=3, adjust=False).mean()
            is_bear_trap = ((low < ema3) & (close > ema3) & (vol > vol_sma * 1.8)) | (vol_hole & (low < low.shift(1)) & (close > open_p))
            is_bull_trap = ((high > ema3) & (close < ema3) & (vol > vol_sma * 1.8)) | ((~vol_hole) & (close > k_up * 1.1) & (close < open_p))

            # EXP Ignition
            macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
            macd_sig = macd.rolling(9).mean()
            exp_buy = (~is_sqz) & is_sqz.shift(1) & (macd > macd_sig) & (macd > 0)
            exp_sel = (~is_sqz) & is_sqz.shift(1) & (macd < macd_sig) & (macd < 0)

            # Scoring
            fs = 0
            if close.iloc[-1] > ema3.iloc[-1]: fs += 1
            if curr_wp > 50: fs += 2
            if vol.iloc[-1] > vol_sma.iloc[-1] * 1.5: fs += 1

            # Hiyerarşik Sinyal
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

# ==========================================
# 5. ANA EKRAN & SEKTÖR DERİNLİĞİ KOKPİTİ
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

# --- DERİN SEKTÖR ANALİZİ (YENİLENEN BÖLÜM) ---
st.subheader("🎯 Ayrıntılı Sektör ve Hisse Taraması")
st.session_state.active_sector = st.selectbox("Sektörel derinliğe inmek için bir alan seçin:", list(GLOBAL_MAP.keys()))

def style_signals(val):
    if isinstance(val, str):
        if 'HYPER BUY' in val: return 'background-color: #ffeb3b; color: #000 !important; font-weight: bold;'
        if 'HYPER SELL' in val: return 'background-color: #880e4f; color: white !important; font-weight: bold;'
        if 'WHALE RE-ENTRY' in val: return 'background-color: #00bcd4; color: black !important; font-weight: bold;'
        if 'WHALE IN' in val: return 'background-color: #01579b; color: white !important;'
        if 'VOLA HOLE' in val: return 'background-color: #6a1b9a; color: white !important;'
        if 'EXP BUY' in val: return 'background-color: #00e676; color: black !important; font-weight: bold;'
        if 'EXP SELL' in val: return 'background-color: #ff3d00; color: white !important; font-weight: bold;'
        if 'BUY' in val: return 'background-color: #1b5e20; color: #00ff88 !important;'
        if 'SELL' in val: return 'background-color: #440000; color: #ff3333 !important; font-weight: bold;'
        if val == '⛔': return 'background-color: #b71c1c; color: white !important; font-size: 1.2rem;'
        if val == '✅': return 'background-color: #004d40; color: white !important; font-size: 1.2rem;'
    return ''

if st.session_state.active_sector:
    sec = st.session_state.active_sector
    st.markdown(f"### 🔍 {sec} Ekosistemi")
    
    # 1. Sektör Haberleri ve Pil Durumu
    cur_chg, prev_chg, delta_icon, sec_news = get_sector_status(sec, st.session_state.active_trigger)
    
    c_info, c_batt = st.columns([1.5, 1])
    with c_info:
        box_color = "#00ff88" if cur_chg >= 75 else "#f1c40f" if cur_chg >= 45 else "#ff3333"
        st.markdown(f"""
            <div style="border-left: 4px solid {box_color}; padding: 15px; background: #111; border-radius: 5px;">
                <strong style="color: {box_color};">Makro Etki Analizi:</strong><br>
                <span style="color: #e0e0e0;">{sec_news}</span>
            </div>
        """, unsafe_allow_html=True)
    with c_batt:
        draw_battery_with_delta(sec, cur_chg, prev_chg, delta_icon)

    # 2. İlgili Tüm Hisselerin Tek Seferde Taranması (Performans için)
    etfs_in_sector = GLOBAL_MAP[sec]
    all_stocks_to_scan = []
    for etf in etfs_in_sector:
        all_stocks_to_scan.extend(ETF_INFO.get(etf, {}).get("stocks", []))
    all_stocks_to_scan = list(set(all_stocks_to_scan)) # Benzersiz hisseler
    
    with st.spinner(f"{sec} içindeki tüm hisseler analiz ediliyor..."):
        df_sector_all = calculate_signals(all_stocks_to_scan)
        
        # 3. Alt Sektör Kırılımı (ETF Expander'ları)
        st.markdown("#### 📂 Alt Sektör Kırılımları ve Hisse Sinyalleri")
        for etf in etfs_in_sector:
            etf_data = ETF_INFO.get(etf, {"area": "Genel Kapsam", "stocks": []})
            with st.expander(f"📁 {etf} - {etf_data['area']}"):
                if not df_sector_all.empty:
                    df_etf_specific = df_sector_all[df_sector_all['Ticker'].isin(etf_data['stocks'])]
                    if not df_etf_specific.empty:
                        st.dataframe(df_etf_specific.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
                    else:
                        st.write("Bu alt sektöre ait hisselerde yeterli veri oluşmadı.")
                else:
                    st.write("Veri alınamadı.")
