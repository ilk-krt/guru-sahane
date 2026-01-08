import streamlit as st
import yfinance as yf
import pandas as pd

# --- GURU STRATEJİK AYARLAR ---
st.set_page_config(page_title="GURU V3 - ŞAHANE", layout="wide")

# Görsel tasarım hatasını önlemek için f-string kullanmadan temiz CSS
st.markdown("""
    <style>
    /* Ana Ekran Arka Plan */
    .stApp { background-color: #0b0e14; }
    
    /* Metrik Kartları */
    div[data-testid="stMetric"] {
        background-color: #1e2530;
        border: 2px solid #3e4b5b;
        padding: 20px;
        border-radius: 12px;
    }
    div[data-testid="stMetricLabel"] > div { color: #ffffff; font-size: 16px; font-weight: bold; }
    div[data-testid="stMetricValue"] > div { color: #00ffcc; font-size: 24px; }
    
    /* --- SOL PANEL (SIDEBAR) GÜNCELLEME --- */
    [data-testid="stSidebar"] { background-color: #0e1117; border-right: 1px solid #3e4b5b; }
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    /* Genel Yazı Ayarları */
    h1, h2, h3, p, span { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ GURU V3: ŞAHANE Sektörel Radar")
# --- SEKTÖREL VERİ HARİTASI ---
SECTORS = {
    "BIST - Enerji": ["ENJSA.IS", "AKSEN.IS", "AYDEM.IS", "GWIND.IS", "GALATA.IS", "ODAS.IS", "ZOREN.IS"],
    "BIST - Sanayi & Metal": ["EREGL.IS", "KARDM.IS", "TUPRS.IS", "SISE.IS", "SAHOL.IS", "KCHOL.IS", "ARCLK.IS"],
    "BIST - Gıda & Perakende": ["BIMAS.IS", "MGROS.IS", "SOKM.IS", "AEFES.IS", "CCOLA.IS", "TATGD.IS", "ULKER.IS"],
    "USA - Yarı İletken (AI)": ["NVDA", "AMD", "TSM", "AVGO", "ASML", "INTC", "MU"],
    "USA - Big Tech": ["AAPL", "MSFT", "GOOGL", "META", "AMZN", "NFLX", "TSLA"]
}

# --- FONKSİYONLAR ---
@st.cache_data(ttl=3600)
def get_guru_data(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        cf = t.cashflow
        
        # FCF Hesaplama (En Garanti Yöntem)
        if 'Free Cash Flow' in cf.index:
            fcf = cf.loc['Free Cash Flow'].iloc[0]
        else:
            fcf = cf.loc['Operating Cash Flow'].iloc[0] + cf.loc['Capital Expenditure'].iloc[0]
            
        return info, fcf
    except:
        return None, 0

# --- YAN PANEL ---
st.sidebar.header("🕹️ Komuta Merkezi")
selected_sector = st.sidebar.selectbox("Sektör Radarı", list(SECTORS.keys()))
active_ticker = st.sidebar.selectbox("Analiz Edilecek Hisse", SECTORS[selected_sector])

st.sidebar.divider()
st.sidebar.subheader("🎯 Değerleme Parametreleri")
m_growth = st.sidebar.slider("Yıllık FCF Büyüme (%)", 5, 60, 15)
m_discount = st.sidebar.slider("İskonto Oranı (Risk %)", 10, 35, 15)
m_ebitda_mult = st.sidebar.slider("Hedef FD/FAVÖK", 4.0, 20.0, 8.5)

# --- ANALİZ MOTORU ---
info, fcf = get_guru_data(active_ticker)

if info:
    # ÜST ÖZET PANELİ
    st.subheader(f"📊 {info.get('longName')} ({active_ticker})")
    curr_price = info.get('currentPrice', 1)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Güncel Fiyat", f"{curr_price} TL/USD")
    m2.metric("Piyasa Değeri", f"{round(info.get('marketCap', 0)/1e9, 2)} Milyar")
    m3.metric("F/K Oranı", f"{round(info.get('trailingPE', 0), 2)}x")
    # FCF Yield (Nakit Akışı Getirisi) - GURU'nun en sevdiği gösterge
    fcf_yield = (fcf / info.get('marketCap', 1)) * 100
    m4.metric("FCF Getirisi (Yield)", f"%{round(fcf_yield, 2)}")

    st.divider()

    # DEĞERLEME MODELLERİ
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🎯 Hedef Fiyat Hesaplayıcı")
        c1, c2, c3 = st.columns(3)
        
        # 1. Graham Modeli
        eps = info.get('trailingEps', 0)
        bvps = info.get('bookValue', 0)
        graham = (22.5 * eps * bvps)**0.5 if eps > 0 and bvps > 0 else 0
        c1.metric("Graham Değeri", f"{round(graham, 2)}")

        # 2. FD/FAVÖK Modeli
        ebitda = info.get('ebitda', 1)
        net_debt = info.get('totalDebt', 0) - info.get('totalCash', 0)
        shares = info.get('sharesOutstanding', 1)
        ebitda_target = ((ebitda * m_ebitda_mult) - net_debt) / shares
        c2.metric("FD/FAVÖK Hedefi", f"{round(ebitda_target, 2)}")

        # 3. Akıllı FCF Modeli
        # 3. Akıllı FCF Modeli
        g = m_growth / 100
        r = m_discount / 100
        
        if fcf <= 0:
            fcf_target = 0
            c3.error("FCF Negatif")
            st.sidebar.warning(f"⚠️ {active_ticker}: Şirket nakit yakıyor, FCF modeli çalışmaz.")
        elif r <= g:
            fcf_target = 0
            c3.warning("İskonto > Büyüme")
            st.sidebar.info("💡 İpucu: Soldan Büyüme oranını düşür veya İskonto'yu artır.")
        elif r > g:
            fcf_target = ((fcf * (1 + g)) / (r - g)) / shares
            c3.metric("FCF Hedefi", f"{round(fcf_target, 2)}")

        # KONSOLİDE SONUÇ
        targets = [t for t in [graham, ebitda_target, fcf_target] if t > 0]
        final_price = sum(targets) / len(targets) if targets else 0
        upside = ((final_price / curr_price) - 1) * 100