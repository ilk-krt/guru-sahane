import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import graphviz
from datetime import datetime

# --- 0. AYARLAR & STATE YÖNETİMİ ---
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION", page_icon="🏛️")

# CSS: Aether Estetiği ve Tıklanabilir Alanlar
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #e0e0e0; }
    .news-summary-pos { color: #00ff88; font-weight: bold; cursor: pointer; }
    .news-summary-neg { color: #ff3333; font-weight: bold; cursor: pointer; }
    .fv-up { color: #00ff88; font-weight: bold; font-size: 1.2rem; }
    .fv-down { color: #ff3333; font-weight: bold; font-size: 1.2rem; }
    .leader-stock { border: 1px solid #00ff88; border-radius: 5px; padding: 10px; margin: 5px; }
    .laggard-stock { border: 1px solid #ff3333; border-radius: 5px; padding: 10px; margin: 5px; }
    </style>
""", unsafe_allow_html=True)

# Oturum Değişkenleri (Hiyerarşik Gezinti İçin)
if 'macro_state' not in st.session_state: st.session_state.macro_state = "neutral"
if 'macro_impact' not in st.session_state: st.session_state.macro_impact = "neutral"
if 'show_macro_news' not in st.session_state: st.session_state.show_macro_news = False
if 'active_asset' not in st.session_state: st.session_state.active_asset = None
if 'active_sector' not in st.session_state: st.session_state.active_sector = None

# --- VERİ MOTORU ---
# 0. Sektörel Gruplandırma
SECTORS = {
    "Teknoloji (AI & Çip)": {"Leaders": ["NVDA", "AVGO", "MSFT"], "Laggards": ["INTC", "CSCO"]},
    "Enerji & Altyapı": {"Leaders": ["SMR", "CEG", "VST"], "Laggards": ["XOM", "CVX"]},
    "Finans": {"Leaders": ["JPM", "GS"], "Laggards": ["BAC", "C"]},
    "Tüketim": {"Leaders": ["AMZN", "COST"], "Laggards": ["NKE", "SBUX"]}
}

ASSET_GROUPS = ["Hisse Senedi", "Tahvil", "Emtia", "Kripto", "Forex", "Gayrimenkul"]

# --- QUANTUM FUSION CORE (V127 ARCHITECT) ---
def apply_quantum_fusion(df):
    # 1. Whale Power Motoru
    df['vol_avg'] = df['volume'].rolling(window=20).mean()
    df['std_vol'] = df['volume'].rolling(window=20).std()
    df['is_whale_vol'] = df['volume'] > (df['vol_avg'] + (df['std_vol'] * 1.5))
    df['whale_pwr'] = (df['volume'] / df['vol_avg']) * ((df['close'] - df['low']) / (df['high'] - df['low'] + 1e-6))
    
    # 2. Skorlama (3-Mum kuralı hariç)
    df['fusion_score'] = 0
    df['ema_1'] = df['close'].ewm(span=1, adjust=False).mean()
    df.loc[df['close'] > df['ema_1'], 'fusion_score'] += 1
    df.loc[df['whale_pwr'] > 0.5, 'fusion_score'] += 2
    df.loc[df['is_whale_vol'], 'fusion_score'] += 1
    
    # 3. Tuzak Kontrolü (✅/⛔) - Eğim yerine fiyat artışına bakılır
    df['is_bull_trap'] = (df['close'] > df['close'].shift(1)) & (df['whale_pwr'] < df['whale_pwr'].shift(1))
    return df

def get_trap_signal(is_trap):
    return "⛔" if is_trap else "✅"

# --- GÖRSEL BİLEŞENLER ---
# 5. Hız Göstergesi (Gauge)
def draw_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value, title = {'text': title, 'font': {'size': 16, 'color': 'white'}},
        gauge = {'axis': {'range': [0, 100], 'tickwidth': 1}, 'bar': {'color': color}, 'bgcolor': "black",
                 'steps': [{'range': [0, 50], 'color': '#222'}, {'range': [50, 100], 'color': '#444'}]}
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"})
    return fig

# 7 & 8. Nöro Link Bağlantıları
def draw_neuro_links():
    dot = graphviz.Digraph()
    dot.attr(bgcolor='transparent', rankdir='TB', size='8,8')
    
    # Makro etkiye göre renk belirleme
    if st.session_state.macro_impact == "positive": link_color = "#00ff88"
    elif st.session_state.macro_impact == "negative": link_color = "#ff3333"
    else: link_color = "#666666"

    # Varlık gruplarını 3'erli alt alta diz
    for i in range(0, len(ASSET_GROUPS), 3):
        with dot.subgraph() as s:
            s.attr(rank='same')
            for asset in ASSET_GROUPS[i:i+3]:
                # Eğer Hisse Senedi seçiliyse onu vurgula
                fill = '#333' if asset == st.session_state.active_asset else '#111'
                border = link_color if st.session_state.macro_impact != "neutral" else '#444'
                dot.node(asset, asset, shape='box', style='filled,rounded', fillcolor=fill, fontcolor='white', color=border, penwidth='2')
    
    # Nöro Bağlantıları çiz (İlk varlıktan diğerlerine ve aralarında)
    for i in range(len(ASSET_GROUPS)-1):
        dot.edge(ASSET_GROUPS[i], ASSET_GROUPS[i+1], color=link_color, style='dashed', penwidth='2')
    
    st.graphviz_chart(dot)

# --- ANA UYGULAMA ---
st.title("🏛️ AETHER MACRO SYSTEM")

# 5, 6, 8. Makro Başlıklar, Puanlar ve Etkileşimler
col1, col2, col3 = st.columns(3)
macros = [("LEADING", 75, "#00ff88", "positive"), ("COINCIDENT", 45, "#ff3333", "negative"), ("LAGGING", 55, "#f1c40f", "neutral")]

for i, (name, val, color, impact) in enumerate(macros):
    with [col1, col2, col3][i]:
        st.plotly_chart(draw_gauge(val, name, color), use_container_width=True)
        
        # Streamlit'te Uzun/Kısa Basma Simülasyonu
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button(f"🔗 Etki (Kısa)", key=f"short_{name}"):
            st.session_state.macro_state = name
            st.session_state.macro_impact = impact
            st.session_state.show_macro_news = False
            st.session_state.active_asset = None
            st.session_state.active_sector = None
            st.rerun()
            
        if btn_c2.button(f"📰 Haber (Uzun)", key=f"long_{name}"):
            st.session_state.macro_state = name
            st.session_state.macro_impact = impact
            st.session_state.show_macro_news = True
            st.rerun()

# 6. Uzun Basılınca Haberlerin Sondan Başa Çıkması
if st.session_state.show_macro_news:
    st.divider()
    st.subheader(f"📡 {st.session_state.macro_state} - Son 10 Makro Haber")
    for j in range(10, 0, -1): # Sondan başa sıralama
        is_pos = (j % 2 == 0) if st.session_state.macro_impact == "neutral" else (st.session_state.macro_impact == "positive")
        cls, icon = ("news-summary-pos", "🟢") if is_pos else ("news-summary-neg", "🔴")
        st.markdown(f"<span class='{cls}'>{icon} Haber {j}: Global likidite endekslerinde { 'artış' if is_pos else 'daralma'} tespit edildi.</span>", unsafe_allow_html=True)

# 7 & 8. Varlık Tipleri ve Nöro Linkler
st.divider()
st.subheader("🔗 Varlık Sınıfları Nöro-Ağı")
draw_neuro_links()

# 8 (Devamı). Varlık Grubuna Tıklama Simülasyonu
st.write("Ağı yönlendirmek için etkilenecek varlık sınıfını seçin:")
asset_cols = st.columns(len(ASSET_GROUPS))
for i, asset in enumerate(ASSET_GROUPS):
    with asset_cols[i]:
        if st.button(asset, use_container_width=True):
            st.session_state.active_asset = asset
            st.session_state.active_sector = None
            st.rerun()

# 9. Hisse Senetleri Seçildiğinde Sektörel Gruplar Çıkar
if st.session_state.active_asset == "Hisse Senedi":
    st.divider()
    st.subheader("📊 Sektörel Etkileşim")
    sec_cols = st.columns(len(SECTORS))
    
    for i, sector_name in enumerate(SECTORS.keys()):
        with sec_cols[i]:
            # Makro etkiye göre buton rengini simüle et
            btn_type = "primary" if st.session_state.macro_impact == "positive" else "secondary"
            if st.button(sector_name, type=btn_type, use_container_width=True):
                st.session_state.active_sector = sector_name
                st.rerun()

# 10, 1, 2, 3, 4. Sektör Seçilince Hisseler ve Detayları
if st.session_state.active_sector:
    st.divider()
    st.subheader(f"🎯 {st.session_state.active_sector} Sektör Taraması")
    
    # 1. Öne Çıkanlar (Leaders) ve Geride Kalanlar (Laggards)
    col_lead, col_lag = st.columns(2)
    
    with col_lead:
        st.markdown("### 🟢 Öne Çıkanlar (Leaders)")
        for ticker in SECTORS[st.session_state.active_sector]["Leaders"]:
            with st.expander(f"💎 {ticker} Analizi"):
                # 4. Fair Value Hesaplaması
                fv = np.random.uniform(150, 900)
                prev_fv = fv - np.random.uniform(5, 20)
                fv_class = "fv-up" if fv > prev_fv else "fv-down"
                arrow = "⬆️" if fv > prev_fv else "⬇️"
                
                st.markdown(f"**Güncel Fair Value:** <span class='{fv_class}'>${fv:.2f} {arrow}</span> (Önceki: ${prev_fv:.2f})", unsafe_allow_html=True)
                
                # 2 & 3. Haber Özetleri ve Detayları
                st.write("**Son Çeyrek Önemli Haberler:**")
                st.markdown("<div class='news-summary-pos'>🟢 Sektörel talep patlaması nedeniyle gelir tahminleri yukarı revize edildi.</div>", unsafe_allow_html=True)
                with st.expander("Detayı Oku"):
                    st.caption("Şirket, özellikle yeni nesil veri merkezlerinden gelen siparişlerin %40 oranında arttığını ve tedarik zincirinde sorun yaşanmadığını açıkladı.")
                
                st.markdown("<div class='news-summary-neg'>🔴 Çin pazarındaki regülasyon baskıları belirsizlik yaratıyor.</div>", unsafe_allow_html=True)
                with st.expander("Detayı Oku"):
                    st.caption("Yeni ihracat kısıtlamaları nedeniyle Asya pazarındaki genişleme planları 2027'ye ertelendi.")

    with col_lag:
        st.markdown("### 🔴 Geride Kalanlar (Laggards)")
        for ticker in SECTORS[st.session_state.active_sector]["Laggards"]:
            with st.expander(f"⚠️ {ticker} Analizi"):
                fv = np.random.uniform(20, 100)
                prev_fv = fv + np.random.uniform(2, 10) # Laggard için fv düşmüş olsun
                fv_class = "fv-up" if fv > prev_fv else "fv-down"
                arrow = "⬆️" if fv > prev_fv else "⬇️"
                
                st.markdown(f"**Güncel Fair Value:** <span class='{fv_class}'>${fv:.2f} {arrow}</span> (Önceki: ${prev_fv:.2f})", unsafe_allow_html=True)
                
                st.write("**Son Çeyrek Önemli Haberler:**")
                st.markdown("<div class='news-summary-neg'>🔴 Kar marjlarında daralma devam ediyor.</div>", unsafe_allow_html=True)
                with st.expander("Detayı Oku"):
                    st.caption("Artan operasyonel maliyetler ve düşen ürün fiyatları karlılığı baskılamaya devam ediyor.")

# --- PORTFÖY BÖLÜMÜ ---
st.divider()
st.subheader("📋 Kendi Portföyüm")
# İstenilen formatta portföy detayları
portfolio_data = {
    "Hisse": ["AAPL", "NVDA", "SMR", "CRDO"],
    "Güncel Fiyat": ["$185.20", "$890.10", "$15.40", "$22.10"],
    "Fair Value": ["$195.00", "$950.00", "$18.00", "$28.00"],
    "1 Gün": ["+1.2% 🟢", "+3.5% 🟢", "-0.5% 🔴", "+2.1% 🟢"],
    "1 Hafta": ["+2.1% 🟢", "+12.0% 🟢", "+4.2% 🟢", "-1.5% 🔴"],
    "1 Ay": ["-1.5% 🔴", "+25.4% 🟢", "+18.2% 🟢", "+15.0% 🟢"],
    "1 Çeyrek": ["+8.4% 🟢", "+85.2% 🟢", "+45.1% 🟢", "+32.4% 🟢"],
    "1 Yıl": ["+12.5% 🟢", "+210.4% 🟢", "+115.0% 🟢", "+88.5% 🟢"]
}
df_port = pd.DataFrame(portfolio_data)
st.table(df_port)
