import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta
import calendar

# ==========================================
# 0. AYARLAR & AGRESİF DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION V128.2", page_icon="🏛️")

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
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 1. GENİŞLETİLMİŞ NİŞ TEMATİK VERİ HARİTASI
# ==========================================
GLOBAL_MAP = {
    "Teknoloji (XLK)": ["SMH", "IGV", "CIBR", "SOXX"],
    "Enerji & Altyapı": ["JOUL", "XLE", "PAVE", "URA", "GASZ", "ICLN"],
    "Robotik & Uzay": ["CBOT", "BOTZ", "ARKQ", "XAR", "UFO"],
    "Biyoteknoloji & Sağlık": ["XBI", "ARKG", "IHI"],
    "Lojistik & Taşıma": ["HULL", "IYT", "JETS"],
    "Kozmetik & Tüketim": ["GLAM", "XRT", "XHB"],
    "Emtia & Materyal": ["COPX", "LIT", "GDX", "URNM", "REMX"],
    "Finans & Kripto": ["ARKF", "KRE", "IBIT", "WGMI"],
    "Veri Merkezi & GYO": ["SRVR", "VNQ", "REZ", "INDS"]
}

ETF_INFO = {
    "CBOT": {"area": "Endüstriyel Robotlar", "stocks": ["ISRG", "PATH", "SYM", "ROCK"]},
    "WATS": {"area": "Batarya & Depolama", "stocks": ["ENPH", "PLUG", "STEM", "FLNC"]},
    "GLAM": {"area": "Kozmetik & Bakım", "stocks": ["ELF", "EL", "COTY", "ULTA"]},
    "JOUL": {"area": "Elektrik Altyapısı", "stocks": ["PWR", "ETN", "QUAN", "HUBB"]},
    "GASZ": {"area": "Fosil & LNG Zinciri", "stocks": ["LNG", "TRGP", "WMB", "OKE"]},
    "HULL": {"area": "Deniz & Konteyner", "stocks": ["ZIM", "TRMD", "STNG", "SBLK"]},
    "EUV": {"area": "Litografi Ekosistemi", "stocks": ["ASML", "AMAT", "LRCX", "KLAC"]},
    "COPX": {"area": "Bakır Madenciliği", "stocks": ["FCX", "SCCO", "TECK", "ERO"]},
    "LIT": {"area": "Lityum Batarya", "stocks": ["ALB", "SQM", "TSLA", "LTHM"]},
    "UFO": {"area": "Uzay Ekonomisi", "stocks": ["RKLB", "LUNR", "ASTS", "SPIR"]},
    "SRVR": {"area": "Veri Merkezleri", "stocks": ["EQIX", "AMT", "DLR", "IREN"]},
    "WGMI": {"area": "Kripto Madencilik", "stocks": ["MARA", "RIOT", "CLSK", "WULF"]},
    "SMH": {"area": "Yarı İletken Devleri", "stocks": ["NVDA", "TSM", "AVGO", "AMD"]},
    "IGV": {"area": "Kurumsal Yazılım", "stocks": ["ADBE", "CRM", "MSFT", "NOW"]},
    "CIBR": {"area": "Siber Güvenlik", "stocks": ["PANW", "CRWD", "FTNT", "NET"]},
    "PAVE": {"area": "ABD Altyapı", "stocks": ["URI", "BLDR", "VMC", "CAT"]},
    "URA": {"area": "Uranyum & Nükleer", "stocks": ["CCJ", "SMR", "CEG", "VST"]}
}

# ==========================================
# 2. ALGORİTMİK OPEX & GAMMA HESAPLAYICI (YENİLENDİ)
# ==========================================
def get_third_friday(year, month):
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    month_cal = c.monthdatescalendar(year, month)
    fridays = [day for week in month_cal for day in week if day.weekday() == calendar.FRIDAY and day.month == month]
    return fridays[2]

def get_next_opex_date(current_date):
    year = current_date.year
    month = current_date.month
    third_friday = get_third_friday(year, month)
    
    # Eğer bu ayın OpEx'ini ve Gamma Unwind süresini (4 gün) geçtiysek, bir sonraki aya kilitlen
    if (current_date - third_friday).days > 3:
        month += 1
        if month > 12:
            month = 1
            year += 1
        third_friday = get_third_friday(year, month)
    return third_friday

def generate_market_mechanics_alert():
    today = datetime.now().date()
    next_opex = get_next_opex_date(today)
    days_to_opex = (next_opex - today).days
    
    alerts = []
    
    # Uyarı süresi 10 güne (1.5 hafta) çıkarıldı ve geri sayım mantığı eklendi
    if 0 <= days_to_opex <= 10:
        alerts.append(f"🚨 **OPEX RADARI (Vadeye {days_to_opex} Gün Kaldı):** Dev opsiyon vadesi (OpEx) yaklaşıyor. Market Maker'lar (Piyasa Yapıcılar) Dealer Gamma pozisyonlarını ayarlamaya başlıyor. 'Strike Pinning' (fiyatın kritik opsiyon seviyelerine mıknatıslanması) riski artıyor. Vadeye kadar yön bulamayan sahte kırılımlara (whipsaw) dikkat!")
    elif -3 <= days_to_opex < 0:
        alerts.append("💥 **GAMMA UNWIND (Vade Sonu Çözülmesi):** OpEx geride kaldı. Vade sonu prangaları çözüldü (Dealer hedges rolling off). Piyasada yön arayışı ve sert sistematik fon rotasyonları (Basket Hedging) görmemiz muhtemel. Gerçek fiyatlamalar şimdi başlıyor.")
    else:
        alerts.append(f"📊 **FLOW REBALANCE (Sakin Dönem - Sonraki Vadeye {days_to_opex} Gün):** OpEx baskısı şu an aktif değil. Fiyat hareketleri opsiyonlardan ziyade saf arz/talep (Dark Pool) ve makro tematik fon girişlerine dayanıyor.")
        
    return alerts

# ==========================================
# 3. YFINANCE MATEMATİK & OMNI FUSION
# ==========================================
def get_rma(s, period): return s.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

def get_rsi(s, period):
    delta = s.diff()
    ma_up = get_rma(delta.clip(lower=0), period)
    ma_down = get_rma(-1 * delta.clip(upper=0), period)
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=3600)
def fetch_matrix_data():
    all_etfs = []
    for etfs in GLOBAL_MAP.values(): all_etfs.extend(etfs)
    all_etfs = list(set(all_etfs))
    
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
            bb_width = ((sma20 + 2*std20) - (sma20 - 2*std20)) / sma20 * 100
            current_bbw = bb_width.iloc[-1]
            
            cat = "Diğer"
            for k, v in GLOBAL_MAP.items():
                if t in v: cat = k; break
            
            if r14 > 70: state, color = "Aşırı Alım (Tehlike)", "#ff3333"
            elif r14 < 35: state, color = "Vakum (Contrarian Fırsat)", "#00ff88"
            else: state, color = "Nötr Sıkışma", "#f1c40f"
            
            matrix_results.append({"Sektör": cat, "ETF": t, "RSI (Enerji)": r14, "Volatilite (BBW)": current_bbw, "Durum": state, "Renk": color})
        except: continue
    return pd.DataFrame(matrix_results)

@st.cache_data(ttl=900)
def calculate_signals(ticker_list, interval="1d"):
    if not ticker_list: return pd.DataFrame()
    end_date = datetime.now()
    try:
        if interval == "1d":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=90), end=end_date, interval="1d", group_by='ticker', progress=False)
        elif interval == "1wk":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=200), end=end_date, interval="1wk", group_by='ticker', progress=False)
    except: return pd.DataFrame()

    results = []
    for t in ticker_list:
        try:
            df = raw_data[t].copy().dropna() if len(ticker_list) > 1 else raw_data.copy().dropna()
            if len(df) < 15: continue

            close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
            r14 = get_rsi(close, 14)
            sma20 = close.rolling(20).mean()
            
            # Balina Gücü
            c_range = (high - low).clip(lower=0.001)
            delta_q = ((close - low) - (high - close)) / c_range
            delta_vol_q = (delta_q * vol).rolling(10).mean() / vol.rolling(10).mean().clip(lower=0.001)
            wp = np.clip(((r14 - 50) + (delta_vol_q * 50)) * 2, 0, 100).rolling(2).mean()

            sig = "⚪ WAIT"
            if interval == "1wk":
                # GELİŞMİŞ MOMENTUM GAP (Prior Momentum: VCP Sıkışması)
                range_wk1 = high.shift(1) - low.shift(1)
                range_wk2 = high.shift(2) - low.shift(2)
                vcp_tightening = range_wk1 < range_wk2
                prior_momentum = vcp_tightening & (close.shift(1) > sma20.shift(1))
                
                bull_gap = (low > high.shift(1)) & (close > open_p)
                bear_gap = (high < low.shift(1)) & (close < open_p)
                
                if prior_momentum.iloc[-1] and bull_gap.iloc[-1]: sig = "🚀 MOMENTUM GAP (UP)"
                elif bear_gap.iloc[-1]: sig = "🩸 MOMENTUM GAP (DOWN)"
                elif wp.iloc[-1] > 80: sig = "🐋 WHALE ACCUMULATION"
                elif r14.iloc[-1] < 35: sig = "🕳️ DEEP VALUE (DCA)"
            else:
                is_sqz = (close.rolling(20).std() * 2) < (get_rma(high-low, 14).rolling(20).mean() * 1.5)
                vol_hole = is_sqz & (close <= sma20)
                bull_trap = (high > close.ewm(span=5).mean()) & (close < open_p) & (vol > vol.rolling(20).mean() * 1.5)
                
                if wp.iloc[-1] >= 85: sig = "☄️ HYPER BUY"
                elif vol_hole.iloc[-1]: sig = "🕳️ VOLA HOLE"
                elif bull_trap.iloc[-1]: sig = "⛔ BULL TRAP"
                elif r14.iloc[-1] > 60: sig = "✅ BUY"
                
            results.append({
                "Ticker": t, "Sinyal": sig, "Fiyat": f"${close.iloc[-1]:.2f}",
                "RSI": float(f"{r14.iloc[-1]:.1f}"), "Whale Power": float(f"{wp.iloc[-1]:.1f}")
            })
        except Exception: continue
    return pd.DataFrame(results)

# Bilanço ve Fair Value Çekici (Yfinance)
@st.cache_data(ttl=86400) # Günde 1 kez yeniler
def fetch_fundamental_data(ticker_list):
    funds = []
    for t in ticker_list:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            target = info.get('targetMeanPrice', 'N/A')
            
            # Fair Value (Eğer target price varsa hesapla)
            fv = f"${target:.2f}" if isinstance(target, (int, float)) else "N/A"
            
            # Earnings Date
            calendar_data = tk.calendar
            earn_date = "N/A"
            if calendar_data and 'Earnings Date' in calendar_data:
                dates = calendar_data['Earnings Date']
                if len(dates) > 0:
                    earn_date = dates[0].strftime('%Y-%m-%d')
            
            funds.append({"Ticker": t, "Adil Değer (Fair Value)": fv, "Sıradaki Bilanço": earn_date})
        except:
            funds.append({"Ticker": t, "Adil Değer (Fair Value)": "N/A", "Sıradaki Bilanço": "N/A"})
    return pd.DataFrame(funds)

def style_signals(val):
    if isinstance(val, str):
        if 'MOMENTUM GAP (UP)' in val: return 'background-color: #00e676; color: black; font-weight: bold;'
        if 'DEEP VALUE' in val: return 'background-color: #00b0ff; color: black; font-weight: bold;'
        if 'MOMENTUM GAP (DOWN)' in val: return 'background-color: #d50000; color: white; font-weight: bold;'
        if 'HYPER BUY' in val: return 'background-color: #827717; color: white; font-weight: bold;'
        if 'WHALE ACCUMULATION' in val: return 'background-color: #01579b; color: white; font-weight: bold;'
        if 'VOLA HOLE' in val: return 'background-color: #4a148c; color: white;'
        if 'BUY' in val: return 'background-color: #004d40; color: white; font-weight: bold;'
        if 'TRAP' in val: return 'background-color: #b71c1c; color: white;'
    return 'background-color: #111111; color: white;'

# ==========================================
# 4. KOKPİT ARAYÜZÜ 
# ==========================================
st.title("🏛️ AETHER THEMATIC & MOMENTUM-GAP ARCHITECT")

tab1, tab2, tab3 = st.tabs(["🔋 GERÇEK ZAMANLI OMNI-MATRIX", "🔭 TEMATİK ETF'LER & GÜNLÜK FUSION", "🦈 HAFTALIK MOMENTUM-GAP & FUNDAMENTALS"])

# ---------------------------------------------------------
# TAB 1: OMNI-MATRIX & PİYASA MEKANİKLERİ
# ---------------------------------------------------------
with tab1:
    st.subheader("⚙️ Gizli Piyasa Mekanikleri (OpEx & Gamma Algoritması)")
    mechanics_alerts = generate_market_mechanics_alert()
    for alert in mechanics_alerts:
        st.info(alert)
    
    st.divider()
    st.subheader("🔋 Tüm ETF Sektörleri Pil Ekranı (Gerçek Veri)")
    st.markdown("Arka planda tüm tematik ETF'lerin son 3 aylık verisi çekilip gerçek RSI (Para Akışı) ve Bollinger Sıkışması hesaplanmıştır.")
    
    with st.spinner("Gerçek piyasa verileri çekiliyor... (Birkaç saniye sürebilir)"):
        df_matrix = fetch_matrix_data()
        
        if not df_matrix.empty:
            fig = go.Figure()
            for state in ["Aşırı Alım (Tehlike)", "Nötr Sıkışma", "Vakum (Contrarian Fırsat)"]:
                df_sub = df_matrix[df_matrix["Durum"] == state]
                fig.add_trace(go.Scatter(
                    x=df_sub["Volatilite (BBW)"], y=df_sub["RSI (Enerji)"], mode='markers+text',
                    marker=dict(size=16, color=df_sub["Renk"], line=dict(width=1, color='white'), opacity=0.9),
                    text=df_sub["ETF"], textposition="top center", name=state,
                    hovertemplate="<b>%{text}</b><br>Tema: " + df_sub["Sektör"] + "<br>RSI (Enerji): %{y:.1f}<br>Sıkışma (BBW): %{x:.1f}%<extra></extra>"
                ))
                
            fig.add_hline(y=70, line_dash="dash", line_color="#ff3333", annotation_text="Tehlike (Aşırı Isınma)")
            fig.add_hline(y=35, line_dash="dash", line_color="#00ff88", annotation_text="Fırsat (Capital Rotation)")
            fig.update_layout(title="Gerçek Zamanlı Sektörel Enerji Matrisi", xaxis_title="Bollinger Bant Genişliği (Düşük = Sıkışma)", yaxis_title="RSI (Hacimsel Enerji Yükü)", height=600, paper_bgcolor="#050505", plot_bgcolor="#111", font=dict(color="#e0e0e0"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Matrix verileri alınamadı.")

# ---------------------------------------------------------
# TAB 2: TEMATİK ETF'LER & GÜNLÜK FUSION
# ---------------------------------------------------------
with tab2:
    st.subheader("🔭 Tematik Trendler ve Niche Ekosistemler (Günlük)")
    
    selected_theme = st.selectbox("Analiz edilecek temayı seçin:", list(GLOBAL_MAP.keys()))
    
    if selected_theme:
        etfs_in_theme = GLOBAL_MAP[selected_theme]
        all_theme_stocks = []
        for etf in etfs_in_theme:
            all_theme_stocks.extend(ETF_INFO.get(etf, {}).get("stocks", []))
        all_theme_stocks = list(set(all_theme_stocks))
        
        with st.spinner("Tematik hisseler günlük kuantum motorundan geçiriliyor..."):
            df_theme_daily = calculate_signals(all_theme_stocks, interval="1d")
            
            for etf in etfs_in_theme:
                area_info = ETF_INFO.get(etf, {"area": "Genel Kapsam", "stocks": []})
                with st.expander(f"📂 {etf} ETF - {area_info['area']} Ekosistemi"):
                    if not df_theme_daily.empty:
                        df_specific = df_theme_daily[df_theme_daily['Ticker'].isin(area_info['stocks'])]
                        if not df_specific.empty:
                            st.dataframe(df_specific.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
                        else: st.write("Bu ETF içinde güncel sinyal yok.")

# ---------------------------------------------------------
# TAB 3: HAFTALIK MOMENTUM-GAP & FUNDAMENTALS
# ---------------------------------------------------------
with tab3:
    st.subheader("🦈 Haftalık Momentum-Gap & Temel Analiz Avcısı")
    st.markdown("""
        **VCP & Gap Algoritması Aktif:** Sisteme 'Volatility Contraction' (Mum boylarında daralma) şartı eklendi.
        Eğer bir hissede bilançosu yaklaşırken derin bir 'Vola Hole' veya 'DCA' bölgesi görürseniz bu kusursuz bir fırtınadır.
    """)
    
    conviction_tickers = ["NVDA", "ASML", "CRWD", "SMCI", "PWR", "ISRG", "ASTS", "ZIM", "LNG", "CEG", "ALB", "FCX", "MARA", "PLUG", "CCJ"]
    
    with st.spinner("Haftalık (1W) Kinetik Boşluklar aranıyor ve Bilanço tarihleri çekiliyor..."):
        df_weekly = calculate_signals(conviction_tickers, interval="1wk")
        df_fundamentals = fetch_fundamental_data(conviction_tickers)
        
        if not df_weekly.empty and not df_fundamentals.empty:
            # Sinyaller ve Temel Verileri Birleştir
            df_final = pd.merge(df_weekly, df_fundamentals, on="Ticker", how="left")
            df_final['Strateji'] = df_final['Sinyal'].apply(lambda x: "Ekle (DCA)" if "UP" in x or "WHALE" in x or "DEEP" in x else "Bekle/İzle")
            
            st.dataframe(df_final.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)
            
            st.success("🚨 Market Mekaniği Notu: Yukarıdaki tabloda 'Sıradaki Bilanço' tarihine 2 haftadan az kalmış ve Sinyal durumu 'DEEP VALUE' veya 'VOLA HOLE' olan bir hisse yakalarsanız, kurumsal yatırımcılar (Smart Money) bilanço öncesi fiyatı kasıtlı baskılıyor demektir. Asıl Relentless DCA yeri orasıdır.")
        else:
            st.error("Veri çekilemedi.")
