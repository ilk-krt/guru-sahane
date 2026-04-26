import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.express as px
from datetime import datetime, timedelta

# ==========================================
# 1. MASTER SEKTÖR & ALT SEKTÖR HARİTASI (V129.5)
# ==========================================
st.set_page_config(page_title="Aether Deep Scanner", layout="wide")
st.title("🛰️ Aether V129.5 - Deep Sector Scanner")

MASTER_MAP = {
    "TEKNOLOJİ (XLK)": {
        "Main": "XLK",
        "Subs": {"Yarı İletkenler": "SMH", "Siber Güvenlik": "CIBR", "Yazılım & SaaS": "IGV", "AI & Robotik": "BOTZ", "Fintech": "ARKF"}
    },
    "SANAYİ & HAVACILIK (XLI)": {
        "Main": "XLI",
        "Subs": {"Savunma & Uzay": "ITA", "Lojistik": "IYT", "Altyapı": "PAVE", "Hava Yolları": "JETS"}
    },
    "ENERJİ (XLE)": {
        "Main": "XLE",
        "Subs": {"Petrol & Gaz Arama": "XOP", "Ekipman & Servis": "OIH", "Uranyum": "URA", "Yenilenebilir": "ICLN"}
    },
    "SAĞLIK (XLV)": {
        "Main": "XLV",
        "Subs": {"Biyoteknoloji": "XBI", "Tıbbi Cihazlar": "IHI", "Genomik": "ARKG"}
    },
    "FİNANS (XLF)": {
        "Main": "XLF",
        "Subs": {"Bölgesel Bankalar": "KRE", "Sigortacılık": "KIE", "Sermaye Piyasaları": "IAI"}
    },
    "KEYFİ TÜKETİM (XLY)": {
        "Main": "XLY",
        "Subs": {"Perakende": "XRT", "Konut İnşaatı": "XHB", "E-Ticaret": "IBUY", "Eğlence/Kumar": "BETZ"}
    },
    "HAM MADDELER (XLB)": {
        "Main": "XLB",
        "Subs": {"Madencilik": "XME", "Altın Madencileri": "GDX", "Lityum": "LIT"}
    },
    "DİĞER KRİTİK": {
        "Main": "SPY",
        "Subs": {"İletişim (XLC)": "XLC", "Gayrimenkul (XLRE)": "XLRE", "Temel Tüketim (XLP)": "XLP", "Kamu Hizmetleri (XLU)": "XLU"}
    }
}

# ==========================================
# 2. HESAPLAMA MOTORU (RRG + AETHER LOGIC)
# ==========================================
def get_analysis(tickers, benchmark="SPY"):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=250)
    data = yf.download(list(tickers) + [benchmark], start=start_date, end=end_date, progress=False)['Close']
    
    results = []
    for t in tickers:
        # RRG Mantığı
        rs = (data[t] / data[benchmark]) * 100
        mom = ta.roc(rs, length=14) + 100
        
        # Aether Logic (ŞAHANE)
        df = pd.DataFrame(data[t]).rename(columns={t: 'Close'})
        ema1 = ta.ema(df['Close'], length=1)
        ema12 = ta.ema(df['Close'], length=12)
        slope = (df['Close'] > df['Close'].shift(1)) & (df['Close'].shift(1) > df['Close'].shift(2))
        stage2 = (df['Close'] > ta.sma(df['Close'], 150))
        
        signal = "✅ BUY" if (ema1.iloc[-1] > ema12.iloc[-1]) and slope.iloc[-1] and stage2.iloc[-1] else "⏳ BEKLE"
        
        results.append({
            "Ticker": t,
            "RS": round(rs.iloc[-1], 2),
            "Momentum": round(mom.iloc[-1], 2),
            "Aether Sinyal": signal
        })
    return pd.DataFrame(results)

# ==========================================
# 3. KOKPİT ARAYÜZÜ (GÖRSELLEŞTİRME)
# ==========================================
st.sidebar.header("🕹️ Kontrol Paneli")
selected_main = st.sidebar.selectbox("Ana Sektör Seçin", list(MASTER_MAP.keys()))

main_ticker = MASTER_MAP[selected_main]["Main"]
sub_dict = MASTER_MAP[selected_main]["Subs"]

st.subheader(f"🔍 {selected_main} - Mikroskop Analizi")
col1, col2 = st.columns([1, 1])

# Verileri Çek
with st.spinner("Veriler işleniyor..."):
    analysis_df = get_analysis([main_ticker] + list(sub_dict.values()))

with col1:
    st.write("📊 **Sinyal ve Güç Tablosu**")
    st.dataframe(analysis_df.style.applymap(
        lambda x: 'background-color: #004d00; color: white' if x == "✅ BUY" else '', subset=['Aether Sinyal']
    ), use_container_width=True)

with col2:
    st.write("🎯 **Alt Sektör Rotasyonu (RRG)**")
    fig = px.scatter(analysis_df, x="RS", y="Momentum", text="Ticker", color="Aether Sinyal",
                     color_discrete_map={"✅ BUY": "green", "⏳ BEKLE": "orange"})
    fig.add_hline(y=100, line_dash="dash")
    fig.add_vline(x=100, line_dash="dash")
    st.plotly_chart(fig, use_container_width=True)

# "Smart Money" Takibi İçin Uyarı Notu
top_sub = analysis_df.iloc[analysis_df['RS'].idxmax()]
st.info(f"💡 **Smart Money Notu:** Şu an {selected_main} içinde en yüksek sermaye gücü (RS) **{top_sub['Ticker']}** odasında toplanmış görünüyor.")
