import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime, timedelta

# ==========================================
# 0. AYARLAR & CSS (DARK MODE & KONTRAST)
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION V127.5", page_icon="🏛️")

st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; color: #e0e0e0 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; }
    div.stButton > button { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #333 !important; border-radius: 8px !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    
    .deep-analysis-box { background: linear-gradient(145deg, #111 0%, #1a1a1a 100%); border-left: 4px solid #f1c40f; padding: 20px; border-radius: 5px; font-size: 0.95rem; line-height: 1.6; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .deep-analysis-title { color: #f1c40f; font-size: 1.2rem; font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 15px; }
    
    .news-timeline { border-left: 2px solid #444; margin-left: 10px; padding-left: 15px; }
    .news-item { margin-bottom: 15px; position: relative; }
    .news-item::before { content: ''; position: absolute; left: -21px; top: 5px; width: 10px; height: 10px; border-radius: 50%; background-color: #00ff88; }
    
    .battery-container { width: 100%; background-color: #222; border-radius: 10px; margin: 5px 0 15px 0; border: 1px solid #444; position: relative; height: 25px; overflow: hidden; }
    .battery-fill { height: 100%; border-radius: 8px; transition: width 0.5s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-weight: bold; color: #000; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

if 'active_trigger' not in st.session_state: st.session_state.active_trigger = "NEUTRAL"
if 'active_sector' not in st.session_state: st.session_state.active_sector = None

# ==========================================
# 1. VERİ HARİTASI & 3 GÜNLÜK HAFIZA
# ==========================================
SYSTEM_TRIGGERS = {
    "GEOPOLITIK": {
        "color": "#ff3333", "impact": "risk_off",
        "news": [
            "T-3: Orta Doğu'da enerji nakil hatlarına yönelik siber saldırı iddiaları piyasayı gerdi.",
            "T-2: ABD ve müttefikleri stratejik petrol rezervlerini kullanıma açabileceğini sinyalledi.",
            "BUGÜN: Tedarik zincirindeki aksamalar nedeniyle Asya-Avrupa nakliye rotalarında sigorta primleri %40 arttı."
        ],
        "analysis": """
            **Sıkışmış Yay Etkisi & Rotasyon Riski:**
            Yüzeyde piyasa endeksleri dar bir bantta sakin görünse de, bu yanıltıcıdır. Görünür sakinlik, riskin azaldığı anlamına gelmez. Mega-cap teknoloji zayıflarken, savunma ve enerji gibi jeopolitik fayda gören sektörlerde ciddi bir rotasyon yaşanıyor. 
            **Strateji Önerisi:** Opsiyon piyasasında put-call skew yüksek. Aktif yatırımcı için defansif pozisyonları (Enerji, Altın) artırmak ve covered call stratejileri ile yatay piyasadan prim toplamak en mantıklı yoldur.
        """,
        "battery": {"Stocks": 30, "Bonds": 80, "Crypto": 25, "Commodities": 95, "RealEstate": 45}
    },
    "LEADING": {
        "color": "#00ff88", "impact": "risk_on",
        "news": [
            "T-3: Küresel imalat PMI verileri son 8 ayın zirvesine tırmandı.",
            "T-2: Çin merkez bankasından teknoloji ve üretime yönelik sürpriz likidite enjeksiyonu geldi.",
            "BUGÜN: ABD'de yeni konut başlangıçları ve tüketici güveni beklentilerin çok üzerinde açıklandı."
        ],
        "analysis": """
            **Ralli Öncesi Güç Toplama (Coiled Spring):**
            Endekslerdeki dar işlem aralığı tarihsel olarak uzun süre devam etmez. Sıkıştıkça enerji birikir ve breakout geldiğinde hareket keskin olur. Makro veriler bu kırılımın yukarı yönlü olacağını destekliyor.
            **Strateji Önerisi:** Likidite döngüsünün hızlandığı bu dönemde teknoloji, yapay zeka (XLK) ve döngüsel tüketim (XLY) sektörlerinde rotasyon fırsatı yüksektir.
        """,
        "battery": {"Stocks": 90, "Bonds": 30, "Crypto": 85, "Commodities": 60, "RealEstate": 70}
    },
    "COINCIDENT": {
        "color": "#f1c40f", "impact": "neutral_mixed",
        "news": [
            "T-3: İstihdam verileri güçlü gelmeye devam ederken, ücret artışları stabil kaldı.",
            "T-2: Merkez bankası tutanaklarında 'bekle ve gör' vurgusu öne çıktı.",
            "BUGÜN: Perakende satışlar beklentilere paralel geldi, piyasada yön arayışı sürüyor."
        ],
        "analysis": """
            **Yatay Piyasa (Whipsaw Riski):**
            Piyasa sessizce nefesini tutmuş gibi duruyor. Volatilite düşük, herkes rahat ancak pozisyonlar aşırı kalabalık. Yön tahmini yapmanın zor olduğu bu dönemde sahte kırılımlar (whipsaw) ciddi zararlar yazdırabilir.
            **Strateji Önerisi:** Yüksek beta hisselerden ziyade temettü verimi yüksek, serbest nakit akışı güçlü şirketlere rotasyon yapılmalı.
        """,
        "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 45, "Commodities": 55, "RealEstate": 50}
    }
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

# ==========================================
# 2. GÖRSELLEŞTİRME MOTORLARI
# ==========================================
def draw_battery(label, percentage):
    color = "#00ff88" if percentage >= 75 else "#f1c40f" if percentage >= 45 else "#ff3333"
    st.markdown(f"""
        <div style="margin-bottom: 5px; font-size: 0.9rem; color: #ccc;">{label} Güç Seviyesi: %{percentage}</div>
        <div class="battery-container"><div class="battery-fill" style="width: {percentage}%; background-color: {color};">{percentage}%</div></div>
    """, unsafe_allow_html=True)

def draw_smart_money_flow(trigger_data):
    dot = graphviz.Digraph()
    dot.attr(bgcolor='#050505', rankdir='LR', size='10,6')
    
    with dot.subgraph(name='cluster_0') as c:
        c.attr(style='dashed', color='#555', label='Kaydi Varlıklar', fontcolor='#888')
        c.node("FIAT", "Fiat Currency", shape='ellipse', style='filled', fillcolor='#4a148c', fontcolor='white')
        c.node("USD", "USD (Merkez)", shape='circle', style='filled', fillcolor='#0277bd', fontcolor='white', width='1.2')
        c.node("STOCK", "Borsalar", shape='box', style='filled', fillcolor='#f57f17', fontcolor='white')
        c.node("BOND", "Tahviller", shape='box', style='filled', fillcolor='#2e7d32', fontcolor='white')
        c.node("CRYPTO", "Kripto", shape='box', style='filled', fillcolor='#d81b60', fontcolor='white')
        
    with dot.subgraph(name='cluster_1') as c:
        c.attr(style='dashed', color='#555', label='Maddi Varlıklar', fontcolor='#888')
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
# 3. YFINANCE OMNI FUSION (GERÇEK VERİ MOTORU & OMNI 650 MANTIĞI)
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

            # Vektörel Pine Script Fonksiyonları
            close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
            
            # 1. WHALE POWER (Apex Whale Motoru)
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(20).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(20).mean()
            rsi_20 = 100 - (100 / (1 + (gain / loss.replace(0, 0.001))))
            
            c_range_q = (high - low).clip(lower=0.001)
            delta_q = ((close - low) - (high - close)) / c_range_q
            vol_sma_20 = vol.rolling(20).mean().clip(lower=0.001)
            delta_vol_q = (delta_q * vol).rolling(20).mean() / vol_sma_20
            rvol_q = (vol / vol_sma_20.clip(lower=1)).clip(upper=2.5)
            
            base_pwr_q = ((rsi_20 - 50) + (delta_vol_q * 50)) * rvol_q * 1.5
            logic_pwr_q = np.log(1 + np.exp(base_pwr_q / 5)) * 5
            cond = (low > high.shift(2)) & (close > open_p)
            logic_pwr_q = np.where(cond, logic_pwr_q + 35, logic_pwr_q)
            
            log_w_q = np.log10(1 + np.clip(logic_pwr_q, a_min=0, a_max=None))
            pct_w_q = np.minimum((log_w_q * 65)**0.8 * 1.8, 100)
            df['w_pwr_q'] = pd.Series(pct_w_q, index=df.index).fillna(0)

            # 🔥 BALİNA YENİDEN GİRİŞ (Whale Re-Entry)
            # w_pwr_q'nun kendi hareketli ortalamasını (pct_pro_q) kestiği anı tespit eder
            df['pct_pro_q'] = df['w_pwr_q'].rolling(9).mean() # Sarı Ortalama (Hareketli Güç)
            curr_wp = df['w_pwr_q'].iloc[-1]
            prev_wp = df['w_pwr_q'].iloc[-2]
            curr_pro = df['pct_pro_q'].iloc[-1]
            prev_pro = df['pct_pro_q'].iloc[-2]
            
            is_whale_reentry = (curr_wp > curr_pro) and (prev_wp <= prev_pro) and (curr_wp > 40) and (vol.iloc[-1] > vol_sma_20.iloc[-1] * 1.2)

            # 2. VOLATILITY HOLE & SQUEEZE (Bollinger & Keltner Daralması)
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            b_up, b_low = sma20 + 2*std20, sma20 - 2*std20
            
            tr = pd.concat([high - low, abs(high - close.shift(1)), abs(low - close.shift(1))], axis=1).max(axis=1)
            atr14 = tr.rolling(14).mean()
            k_up, k_low = sma20 + 1.5*atr14, sma20 - 1.5*atr14
            
            is_sqz = (b_low > k_low) & (b_up < k_up)
            kc_range_half = (k_up - sma20) / 3.0
            vol_hole = is_sqz & (close <= (sma20 - kc_range_half))
            
            # 3. EXP IGNITION (Kinetik Patlama Motoru)
            macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
            macd_sig = macd.rolling(9).mean()
            exp_buy = (~is_sqz) & is_sqz.shift(1) & (macd > macd_sig) & (macd > 0)
            exp_sel = (~is_sqz) & is_sqz.shift(1) & (macd < macd_sig) & (macd < 0)

            # 4. STRICT TRAPS (Ayı/Boğa Tuzağı Yazısız İkonları)
            ema3 = close.ewm(span=3, adjust=False).mean()
            bear_trap_raw = (low < ema3) & (close > ema3) & (vol > vol_sma_20 * 1.8)
            bull_trap_raw = (high > ema3) & (close < ema3) & (vol > vol_sma_20 * 1.8)
            
            bear_trap_hole = vol_hole & (low < low.shift(1)) & (close > open_p)
            bull_trap_hole = (~vol_hole) & (close > k_up * 1.1) & (close < open_p)
            
            is_bear_trap = bear_trap_raw | bear_trap_hole
            is_bull_trap = bull_trap_raw | bull_trap_hole

            # 5. OMNI FUSION SCORING
            curr_c = close.iloc[-1]
            fusion_score = 0
            if curr_c > ema3.iloc[-1]: fusion_score += 1
            if curr_wp > 50: fusion_score += 2
            if vol.iloc[-1] > vol_sma_20.iloc[-1] * 1.5: fusion_score += 1

            # 6. DİNAMİK MESAJ MOTORU (Hiyerarşik Sinyal Karar Ağacı)
            v_hole_curr = vol_hole.iloc[-1]
            exp_buy_curr = exp_buy.iloc[-1]
            exp_sel_curr = exp_sel.iloc[-1]
            btrap_curr = is_bear_trap.iloc[-1]
            bltrap_curr = is_bull_trap.iloc[-1]

            # Önceliklendirilmiş Uyarı Sistemi
            if curr_wp >= 85 and fusion_score >= 3: signal = "☄️ HYPER BUY"
            elif curr_wp <= 15 and fusion_score <= 1: signal = "☄️ HYPER SELL"
            elif bltrap_curr: signal = "⛔" # Yazı yok, sadece ikon (Bull Trap)
            elif btrap_curr: signal = "✅"  # Yazı yok, sadece ikon (Bear Trap)
            elif is_whale_reentry: signal = "🔄 WHALE RE-ENTRY"
            elif exp_buy_curr: signal = "💥 EXP BUY"
            elif exp_sel_curr: signal = "💥 EXP SELL"
            elif v_hole_curr: signal = "🕳️ VOLA HOLE"
            elif curr_wp > 75: signal = "🐋 WHALE IN"
            elif fusion_score >= 3: signal = "✅ BUY"
            elif fusion_score <= 1: signal = "🔴 SELL" # Her zaman Aktif Satış Onayı
            else: signal = "⚪ WAIT"

            results.append({
                "Ticker": t, "Sinyal": signal, "Fiyat": f"${curr_c:.2f}",
                "Whale Power": float(f"{curr_wp:.1f}"), "Fusion": fusion_score
            })
        except Exception:
            continue
            
    if results: return pd.DataFrame(results).sort_values(by="Fusion", ascending=False)
    return pd.DataFrame()

# ==========================================
# 4. ANA EKRAN KOKPİTİ
# ==========================================
st.title("🏛️ AETHER MACRO SYSTEM")

st.subheader("📡 Global Piyasalar & Akıllı Para Tetikleyicileri")
t_cols = st.columns(3)
for i, trig in enumerate(SYSTEM_TRIGGERS.keys()):
    with t_cols[i]:
        if st.button(f"Tetikle: {trig}", use_container_width=True):
            st.session_state.active_trigger = trig
            st.rerun()

active_data = SYSTEM_TRIGGERS.get(st.session_state.active_trigger, SYSTEM_TRIGGERS["COINCIDENT"])

st.divider()
col_news, col_analysis = st.columns([1, 1.5])
with col_news:
    st.markdown(f"<div style='color:{active_data['color']}; font-weight:bold; font-size:1.1rem; margin-bottom:10px;'>📰 {st.session_state.active_trigger} - Haber Akışı</div>", unsafe_allow_html=True)
    st.markdown("<div class='news-timeline'>", unsafe_allow_html=True)
    for news in active_data['news']: st.markdown(f"<div class='news-item'>{news}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_analysis:
    st.markdown(f"<div class='deep-analysis-box'><div class='deep-analysis-title'>🧠 Aether Derin Analiz</div>{active_data['analysis']}</div>", unsafe_allow_html=True)

st.divider()
st.subheader("🌐 Varlık Dünyası Nöro-Ağı & Para Akış Şarjı")
col_map, col_battery = st.columns([2, 1])
with col_map: draw_smart_money_flow(active_data)
with col_battery:
    for asset, charge in active_data['battery'].items(): draw_battery(asset, charge)

st.divider()
st.subheader("🎯 Sektörel Rotasyon Grafiği (RRG)")
fig_rrg, df_rrg_data = draw_rrg_chart()
st.plotly_chart(fig_rrg, use_container_width=True)

st.session_state.active_sector = st.selectbox("Detaylı incelemek için bir sektör seçin:", list(GLOBAL_MAP.keys()))

def style_signals(val):
    if isinstance(val, str):
        if 'HYPER BUY' in val: return 'background-color: #ffeb3b; color: #000; font-weight: bold;'
        if 'HYPER SELL' in val: return 'background-color: #880e4f; color: white; font-weight: bold;'
        if 'WHALE RE-ENTRY' in val: return 'background-color: #00bcd4; color: black; font-weight: bold;'
        if 'WHALE IN' in val: return 'background-color: #01579b; color: white;'
        if 'VOLA HOLE' in val: return 'background-color: #6a1b9a; color: white;'
        if 'EXP BUY' in val: return 'background-color: #00e676; color: black; font-weight: bold;'
        if 'EXP SELL' in val: return 'background-color: #ff3d00; color: white; font-weight: bold;'
        if 'BUY' in val: return 'background-color: #1b5e20; color: #00ff88;'
        if 'SELL' in val: return 'background-color: #440000; color: #ff3333; font-weight: bold;'
        if val == '⛔': return 'background-color: #b71c1c; color: white; font-size: 1.2rem;'
        if val == '✅': return 'background-color: #004d40; color: white; font-size: 1.2rem;'
    return 'background-color: #222; color: white;'

if st.session_state.active_sector:
    st.markdown(f"### 📊 {st.session_state.active_sector} - Gerçek Zamanlı ETF Taraması")
    etf_list = GLOBAL_MAP[st.session_state.active_sector]
    with st.spinner("OMNI FUSION algoritmaları çalıştırılıyor..."):
        df_etfs = calculate_signals(etf_list)
        if not df_etfs.empty:
            st.dataframe(df_etfs.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
        else:
            st.warning("Veri çekilemedi.")

st.divider()
st.subheader("📋 Genel Portföy İzleme Listesi")
raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]
portfolio_tickers = sorted(list(set(raw_tickers)))

with st.spinner("Tüm hisseler için geçmiş veri ile sinyal hesaplanıyor..."):
    df_port_full = calculate_signals(portfolio_tickers)
    if not df_port_full.empty:
        st.dataframe(df_port_full.style.map(style_signals, subset=['Sinyal']), use_container_width=True, height=600, hide_index=True)
    else:
        st.error("Yfinance sunucularından veri alınamadı.")
