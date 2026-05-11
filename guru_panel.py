import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import graphviz
import random
from datetime import datetime

# --- 0. AYARLAR & STATE YÖNETİMİ ---
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION", page_icon="🏛️")

# CSS: Aether Estetiği - Yüksek Kontrastlı Karanlık Tema (Dark Mode Fix)
st.markdown("""
    <style>
    /* Ana Arka Plan ve Metin Rengi */
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    
    /* Tablo ve Dataframe Arka Planları (Beyaz fonu ezmek için) */
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; color: #e0e0e0 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; }
    
    /* Expander (Açılır Menü) Arka Planları */
    [data-testid="stExpander"] { background-color: #111111 !important; border: 1px solid #333 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary { color: #e0e0e0 !important; font-weight: bold; }
    
    /* Buton Renkleri (Kontrast için) */
    div.stButton > button { background-color: #222222 !important; color: #ffffff !important; border: 1px solid #444 !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    
    /* Özel Sinyal ve Metin Sınıfları */
    .news-summary-pos { color: #00ff88; font-weight: bold; cursor: pointer; }
    .news-summary-neg { color: #ff3333; font-weight: bold; cursor: pointer; }
    .fv-up { color: #00ff88; font-weight: bold; font-size: 1.2rem; }
    .fv-down { color: #ff3333; font-weight: bold; font-size: 1.2rem; }
    .signal-buy { background-color: #004400; color: #00ff88; padding: 5px 10px; border-radius: 5px; border: 1px solid #00ff88; display: inline-block; font-weight: bold;}
    .signal-sell { background-color: #440000; color: #ff3333; padding: 5px 10px; border-radius: 5px; border: 1px solid #ff3333; display: inline-block; font-weight: bold;}
    .signal-wait { background-color: #222222; color: #ffffff; padding: 5px 10px; border-radius: 5px; border: 1px solid #666666; display: inline-block; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# Oturum Değişkenleri
if 'macro_state' not in st.session_state: st.session_state.macro_state = "neutral"
if 'macro_impact' not in st.session_state: st.session_state.macro_impact = "neutral"
if 'show_macro_news' not in st.session_state: st.session_state.show_macro_news = False
if 'active_asset' not in st.session_state: st.session_state.active_asset = None
if 'active_sector' not in st.session_state: st.session_state.active_sector = None

# --- VERİ MOTORU ---
SECTORS = {
    "Teknoloji (AI & Çip)": {"Leaders": ["NVDA", "AVGO", "MSFT"], "Laggards": ["INTC", "CSCO"]},
    "Enerji & Altyapı": {"Leaders": ["SMR", "CEG", "VST"], "Laggards": ["XOM", "CVX"]},
    "Finans": {"Leaders": ["JPM", "GS"], "Laggards": ["BAC", "C"]},
    "Tüketim": {"Leaders": ["AMZN", "COST"], "Laggards": ["NKE", "SBUX"]}
}

ASSET_GROUPS = ["Hisse Senedi", "Tahvil", "Emtia", "Kripto", "Forex", "Gayrimenkul"]

# --- QUANTUM FUSION CORE (V127 ARCHITECT) ---
def apply_quantum_fusion(df):
    df['vol_avg'] = df['volume'].rolling(window=20).mean()
    df['std_vol'] = df['volume'].rolling(window=20).std()
    df['is_whale_vol'] = df['volume'] > (df['vol_avg'] + (df['std_vol'] * 1.5))
    df['whale_pwr'] = (df['volume'] / df['vol_avg']) * ((df['close'] - df['low']) / (df['high'] - df['low'] + 1e-6))
    
    df['fusion_score'] = 0
    df['ema_1'] = df['close'].ewm(span=1, adjust=False).mean()
    df.loc[df['close'] > df['ema_1'], 'fusion_score'] += 1
    df.loc[df['whale_pwr'] > 0.5, 'fusion_score'] += 2
    df.loc[df['is_whale_vol'], 'fusion_score'] += 1
    
    # Tuzak Kontrolü (Yazısız Sadece Emojili Sistem)
    df['is_bull_trap'] = (df['close'] > df['close'].shift(1)) & (df['whale_pwr'] < df['whale_pwr'].shift(1))
    return df

# --- GÖRSEL BİLEŞENLER ---
def draw_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", 
        value = value, 
        title = {'text': title, 'font': {'size': 14, 'color': 'white'}},
        number = {'font': {'color': 'white'}},
        gauge = {
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"}, 
            'bar': {'color': color}, 
            'bgcolor': "#111111", 
            'steps': [{'range': [0, 50], 'color': '#222222'}, {'range': [50, 100], 'color': '#333333'}]}
    ))
    fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
    return fig

def draw_neuro_links():
    dot = graphviz.Digraph()
    dot.attr(bgcolor='#050505', rankdir='TB', size='8,8')
    
    if st.session_state.macro_impact == "positive": link_color = "#00ff88"
    elif st.session_state.macro_impact == "negative": link_color = "#ff3333"
    else: link_color = "#888888"

    for i in range(0, len(ASSET_GROUPS), 3):
        with dot.subgraph() as s:
            s.attr(rank='same')
            for asset in ASSET_GROUPS[i:i+3]:
                fill = '#333333' if asset == st.session_state.active_asset else '#111111'
                border = link_color if st.session_state.macro_impact != "neutral" else '#555555'
                dot.node(asset, asset, shape='box', style='filled,rounded', fillcolor=fill, fontcolor='white', color=border, penwidth='2')
    
    for i in range(len(ASSET_GROUPS)-1):
        dot.edge(ASSET_GROUPS[i], ASSET_GROUPS[i+1], color=link_color, style='dashed', penwidth='2')
    
    st.graphviz_chart(dot)

# --- ANA UYGULAMA ---
st.title("🏛️ AETHER MACRO SYSTEM")

col1, col2, col3 = st.columns(3)
macros = [("LEADING", 75, "#00ff88", "positive"), ("COINCIDENT", 45, "#ff3333", "negative"), ("LAGGING", 55, "#f1c40f", "neutral")]

for i, (name, val, color, impact) in enumerate(macros):
    with [col1, col2, col3][i]:
        st.plotly_chart(draw_gauge(val, name, color), use_container_width=True)
        
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button(f"🔗 Etki", key=f"short_{name}"):
            st.session_state.macro_state = name
            st.session_state.macro_impact = impact
            st.session_state.show_macro_news = False
            st.session_state.active_asset = None
            st.session_state.active_sector = None
            st.rerun()
            
        if btn_c2.button(f"📰 Haber", key=f"long_{name}"):
            st.session_state.macro_state = name
            st.session_state.macro_impact = impact
            st.session_state.show_macro_news = True
            st.rerun()

if st.session_state.show_macro_news:
    st.divider()
    st.subheader(f"📡 {st.session_state.macro_state} - Son Haberler")
    for j in range(10, 0, -1):
        is_pos = (j % 2 == 0) if st.session_state.macro_impact == "neutral" else (st.session_state.macro_impact == "positive")
        cls, icon = ("news-summary-pos", "🟢") if is_pos else ("news-summary-neg", "🔴")
        st.markdown(f"<span class='{cls}'>{icon} Haber {j}: Global piyasalarda aktivite ve likidite akışı raporlandı.</span>", unsafe_allow_html=True)

st.divider()
st.subheader("🔗 Varlık Nöro-Ağı")
draw_neuro_links()

asset_cols = st.columns(3)
for i, asset in enumerate(ASSET_GROUPS):
    with asset_cols[i % 3]:
        if st.button(asset, use_container_width=True):
            st.session_state.active_asset = asset
            st.session_state.active_sector = None
            st.rerun()

if st.session_state.active_asset == "Hisse Senedi":
    st.divider()
    st.subheader("📊 Sektörel Etkileşim")
    sec_cols = st.columns(2)
    
    for i, sector_name in enumerate(SECTORS.keys()):
        with sec_cols[i % 2]:
            if st.button(sector_name, use_container_width=True):
                st.session_state.active_sector = sector_name
                st.rerun()

if st.session_state.active_sector:
    st.divider()
    st.subheader(f"🎯 {st.session_state.active_sector} Taraması")
    
    col_lead, col_lag = st.columns(1)
    
    with col_lead:
        st.markdown("### 🟢 Öne Çıkanlar (Leaders)")
        for ticker in SECTORS[st.session_state.active_sector]["Leaders"]:
            with st.expander(f"💎 {ticker} Analizi"):
                signal_type = "BUY"
                signal_class = "signal-buy"
                st.markdown(f"<span class='{signal_class}'>Sinyal: {signal_type} ✅</span>", unsafe_allow_html=True)
                st.write("")
                
                fv = np.random.uniform(150, 900)
                prev_fv = fv - np.random.uniform(5, 20)
                fv_class = "fv-up" if fv > prev_fv else "fv-down"
                arrow = "⬆️" if fv > prev_fv else "⬇️"
                
                st.markdown(f"**Fair Value:** <span class='{fv_class}'>${fv:.2f} {arrow}</span>", unsafe_allow_html=True)
                
                st.markdown("<div class='news-summary-pos'>🟢 Sektörel talep artışı beklentileri aştı.</div>", unsafe_allow_html=True)
                with st.expander("Detayı Oku"):
                    st.caption("Şirket, operasyonel hedeflerini başarıyla revize etti ve maliyet optimizasyonunu sağladı.")
                
    with col_lead: 
        st.markdown("### 🔴 Geride Kalanlar (Laggards)")
        for ticker in SECTORS[st.session_state.active_sector]["Laggards"]:
            with st.expander(f"⚠️ {ticker} Analizi"):
                signal_type = "SELL"
                signal_class = "signal-sell"
                st.markdown(f"<span class='{signal_class}'>Sinyal: {signal_type} ⛔</span>", unsafe_allow_html=True)
                st.write("")
                
                fv = np.random.uniform(20, 100)
                prev_fv = fv + np.random.uniform(2, 10)
                fv_class = "fv-up" if fv > prev_fv else "fv-down"
                arrow = "⬆️" if fv > prev_fv else "⬇️"
                
                st.markdown(f"**Fair Value:** <span class='{fv_class}'>${fv:.2f} {arrow}</span>", unsafe_allow_html=True)
                
                st.markdown("<div class='news-summary-neg'>🔴 Kar marjlarında daralma devam ediyor.</div>", unsafe_allow_html=True)
                with st.expander("Detayı Oku"):
                    st.caption("Artan operasyonel maliyetler ve talep daralması karlılığı baskılamaya devam ediyor.")

# --- PORTFÖY BÖLÜMÜ (TÜM LİSTE ENTEGRE EDİLDİ) ---
st.divider()
st.subheader("📋 Kendi Portföyüm")
st.write("Sütun başlıklarına tıklayarak sıralama yapabilirsiniz. Aşağı kaydırarak tüm hisseleri görebilirsiniz.")

# Kullanıcının verdiği tüm hisselerin benzersiz listesi (Mükerrer olanlar tekilleştirildi)
raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]
portfolio_tickers = sorted(list(set(raw_tickers)))

# Dinamik Portföy Veri Simülasyonu
port_data = []
for ticker in portfolio_tickers:
    price = np.random.uniform(10, 500)
    fv = price + np.random.uniform(-40, 60)
    change_1d = np.random.uniform(-5, 5)
    change_1w = np.random.uniform(-15, 20)
    signal = random.choice(["BUY ✅", "WAIT ⚪", "SELL ⛔"])
    
    port_data.append({
        "Hisse": ticker,
        "Sinyal": signal,
        "Güncel Fiyat": f"${price:.2f}",
        "Fair Value": f"${fv:.2f}",
        "1 Gün (%)": float(f"{change_1d:.2f}"), # Sıralanabilmesi için sayısal bırakıldı
        "1 Hafta (%)": float(f"{change_1w:.2f}")
    })

# Pandas DataFrame oluştur ve Streamlit ile etkileşimli tablo olarak yansıt
df_port = pd.DataFrame(port_data)

# Verileri renklendiren özel bir fonksiyon (1 Gün ve 1 Hafta için)
def color_surplusvalue(val):
    color = '#00ff88' if val > 0 else '#ff3333'
    return f'color: {color}; font-weight: bold;'

styled_df = df_port.style.map(color_surplusvalue, subset=['1 Gün (%)', '1 Hafta (%)'])

# Scroll edilebilir ve sıralanabilir tablo (st.table yerine st.dataframe)
st.dataframe(styled_df, use_container_width=True, height=500)
