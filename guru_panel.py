import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime, timedelta
import calendar
import random

# ==========================================
# 0. AYARLAR & AGRESİF DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER APEX V129.2", page_icon="🏛️")

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
GLOBAL_MAP = {
    "Teknoloji (XLK)": ["SMH", "IGV", "CIBR", "SOXX"],
    "Enerji & Altyapı": ["JOUL", "XLE", "PAVE", "URA", "GASZ", "ICLN", "WATS"],
    "Robotik & Uzay": ["CBOT", "BOTZ", "ARKQ", "XAR", "UFO"],
    "Biyoteknoloji & Sağlık": ["XBI", "ARKG", "IHI"],
    "Lojistik & Taşıma": ["HULL", "IYT", "JETS"],
    "Kozmetik & Tüketim": ["GLAM", "XRT", "XHB"],
    "Emtia & Materyal": ["COPX", "LIT", "GDX", "URNM", "REMX"],
    "Finans & Kripto": ["ARKF", "KRE", "IBIT", "WGMI"],
    "Veri Merkezi & GYO": ["SRVR", "VNQ", "REZ", "INDS"],
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

SYSTEM_TRIGGERS = {
    "GAMMA SQUEEZE": {"color": "#00ff88", "battery": {"Stocks": 90, "Bonds": 30, "Crypto": 85, "Commodities": 60, "RealEstate": 70}},
    "OPEX PINNING": {"color": "#f1c40f", "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 45, "Commodities": 55, "RealEstate": 50}},
    "GEOPOLITICAL SHOCK": {"color": "#ff3333", "battery": {"Stocks": 30, "Bonds": 80, "Crypto": 25, "Commodities": 95, "RealEstate": 45}}
}

# ==========================================
# 2. KURUMSAL HABER & OPEX MOTORU (YENİ)
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
    
    # 1. OPEX & GAMMA DİNAMİKLERİ
    if 0 <= days_to_opex <= 10:
        alerts.append(f"🚨 **OPEX MEKANİĞİ (Vadeye {days_to_opex} Gün):** Dealer Gamma pozisyonları kritik seviyede. Büyüme (Growth) hisselerinde 'Strike Pinning' ihtimali yüksek. Algoritmik whipsaw'lara (sahte kırılım) dikkat et.")
    elif -3 <= days_to_opex < 0:
        alerts.append("💥 **GAMMA UNWIND & FLOW:** Vade sonu prangaları çözüldü (Dealer hedges rolling off). Piyasada sert sistematik fon rotasyonları (Systematic Flow Rebalances) ve Basket Hedging satımları görebiliriz.")
    else:
        alerts.append(f"📊 **FLOW REBALANCE:** OpEx etkisi sıfırlandı. Piyasa saf kurumsal arz/talep ve Dark Pool blok işlemleriyle yön buluyor.")

    # 2. TEMATİK & JEOPOLİTİK HABERLER
    macro_news = []
    if trigger == "GEOPOLITICAL SHOCK":
        macro_news = [
            "🌍 **GEOPOLİTİK:** Deniz rotalarında navlun sıkıntısı. Akıllı Para $HULL (Lojistik) ETF'sine sığınıyor.",
            "🛢️ **MACRO SHIFT:** Fosil enerji arz endişesi. $GASZ ve $XLE temalarına contrarian flow (ters para) girişi var."
        ]
    elif trigger == "GAMMA SQUEEZE":
        macro_news = [
            "📈 **FAIR VALUE UPDATE:** Çip donanım ($SMH, $EUV) analistleri hedef fiyatları yukarı güncelledi (Re-rating).",
            "🤖 **THEME ROTATION:** Sermaye hızla $CBOT (Robotik) ve Yapay Zeka Altyapısı ($JOUL) alanına akıyor."
        ]
    else:
        macro_news = [
            "⚖️ **BASKET HEDGING:** Endeks fonları teknoloji ağırlığını hafifletip, Value (Değer) hisselerine eşit ağırlıklı rotasyon yapıyor."
        ]
    
    alerts.extend(macro_news)
    return alerts

def draw_battery(label, current, color):
    st.markdown(f"""
        <div style="margin-bottom: 2px; font-size: 0.85rem; color: #ccc;">{label}</div>
        <div class="battery-container" style="height: 20px;">
            <div class="battery-fill" style="width: {current}%; background-color: {color}; font-size: 0.8rem;">%{int(current)}</div>
        </div>
    """, unsafe_allow_html=True)

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
            elif r14 < 35: state, color = "Vakum (Contrarian)", "#00ff88"
            else: state, color = "Sıkışma (VCP)", "#f1c40f"
            
            matrix_results.append({"Sektör": cat, "ETF": t, "RSI": r14, "BBW": current_bbw, "Durum": state, "Renk": color})
        except: continue
    return pd.DataFrame(matrix_results)

@st.cache_data(ttl=900)
def calculate_signals(ticker_list, interval="1d"):
    if not ticker_list: return pd.DataFrame()
    end_date = datetime.now()
    try:
        raw_data = yf.download(ticker_list, start=end_date - timedelta(days=200), end=end_date, interval=interval, group_by='ticker', progress=False)
    except: return pd.DataFrame()

    results = []
    for t in ticker_list:
        try:
            df = raw_data[t].copy().dropna() if len(ticker_list) > 1 else raw_data.copy().dropna()
            if len(df) < 20: continue

            close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
            
            pct_1d = (close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0
            pct_1w = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else 0

            r14 = get_rsi(close, 14)
            sma20 = close.rolling(20).mean()
            v150_v_avg = vol.rolling(20).mean()
            
            c_range = (high - low).clip(lower=0.001)
            delta_vol_q = (((close - low) - (high - close)) / c_range * vol).rolling(10).mean() / vol.rolling(10).mean().clip(lower=0.001)
            wp = np.clip(((r14 - 50) + (delta_vol_q * 50)) * 2, 0, 100).rolling(2).mean()

            # FUSION SKORU
            fusion_score = (((vol > v150_v_avg * 1.2) & (close > open_p)).astype(int) + 
                            (close > close.ewm(span=34).mean()).astype(int) + 
                            ((r14 > 50) & (r14.shift(1) <= 50)).astype(int) + 
                            ((low < low.shift(1)) & (close > open_p) & (close > high.shift(1))).astype(int)).iloc[-1]

            sig = "⚪ WAIT"
            if interval == "1wk":
                # KUSURSUZ MOMENTUM-GAP ŞARTLARI
                range_wk1 = high.shift(1) - low.shift(1)
                range_wk2 = high.shift(2) - low.shift(2)
                vcp_tightening = range_wk1 < range_wk2
                prior_momentum = vcp_tightening & (close.shift(1) > sma20.shift(1))
                bull_gap = (low > high.shift(1)) & (close > open_p)
                
                if prior_momentum.iloc[-1] and bull_gap.iloc[-1]: sig = "🚀 MOMENTUM GAP (UP)"
                elif wp.iloc[-1] > 80: sig = "🐋 WHALE ACCUMULATION"
                elif r14.iloc[-1] < 35: sig = "🕳️ DEEP VALUE (DCA)"
            else:
                pct_pro_q = wp.ewm(span=3, adjust=False).mean()
                whale_re_entry = (wp > pct_pro_q) & (wp.shift(1) <= pct_pro_q.shift(1)) & ((wp.shift(1) < pct_pro_q.shift(1)) & (wp.shift(2) < pct_pro_q.shift(2)))
                is_sqz = (close.rolling(20).std() * 2) < (get_rma(high-low, 14).rolling(20).mean() * 1.5)
                vol_hole = is_sqz & (close <= sma20)
                
                if whale_re_entry.iloc[-1]: sig = "🔄 WHALE RE-ENTRY"
                elif wp.iloc[-1] >= 85: sig = "☄️ HYPER BUY"
                elif vol_hole.iloc[-1]: sig = "🕳️ VOLA HOLE"
                elif fusion_score >= 2: sig = "✅ BUY"
                elif wp.iloc[-1] < 30: sig = "🔴 SELL"
                
            results.append({
                "Ticker": t, "Sinyal": sig, "Fiyat": f"${close.iloc[-1]:.2f}",
                "Whale Power": float(f"{wp.iloc[-1]:.1f}"), "Fusion": int(fusion_score),
                "1 Gün (%)": round(pct_1d, 2), "1 Hafta (%)": round(pct_1w, 2)
            })
        except Exception: continue
    return pd.DataFrame(results)

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

            funds.append({"Ticker": t, "Fair Value": fv, "Target": target, "Bilanço": earn_date, "DaysToEarn": days_to_earn})
        except: funds.append({"Ticker": t, "Fair Value": "N/A", "Target": None, "Bilanço": "N/A", "DaysToEarn": 999})
    return pd.DataFrame(funds)

def style_signals(val):
    if isinstance(val, str):
        if 'GAP' in val: return 'background-color: #00e676; color: black; font-weight: bold;'
        if 'DEEP' in val: return 'background-color: #00b0ff; color: black; font-weight: bold;'
        if 'RE-ENTRY' in val: return 'background-color: #006064; color: white; font-weight: bold;'
        if 'HYPER' in val: return 'background-color: #827717; color: white; font-weight: bold;'
        if 'WHALE' in val: return 'background-color: #01579b; color: white;'
        if 'HOLE' in val: return 'background-color: #4a148c; color: white;'
        if 'BUY' in val: return 'background-color: #004d40; color: white; font-weight: bold;'
        if 'SELL' in val: return 'background-color: #3e2723; color: white; font-weight: bold;'
    return 'background-color: #111111; color: white;'

def style_percentages(val):
    if isinstance(val, (float, int)): return f"color: {'#00ff88' if val > 0 else '#ff3333'}; font-weight: bold;"
    return ''

# ==========================================
# 4. KOKPİT ARAYÜZÜ 
# ==========================================
st.title("🏛️ AETHER APEX: THEMATIC & MOMENTUM ARCHITECT")

# --- ACİL UYARI RADARI (EARNINGS & FAIR VALUE) ---
raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "SMCI", "AI", "CRWD", "RKLB", "SMR", "CEG", "ASTI", "IREN", "WULF", "HIMS", "PYPL", "LNG", "ZIM", "ISRG"]
with st.spinner("Piyasa Radar Kontrolü..."):
    df_alerts = fetch_fundamental_data(raw_tickers)
    urgent_earn = df_alerts[(df_alerts['DaysToEarn'] >= 0) & (df_alerts['DaysToEarn'] <= 7)]
    if not urgent_earn.empty:
        st.warning(f"🔔 **YAKLAŞAN BİLANÇO DİKKAT:** {', '.join(urgent_earn['Ticker'].tolist())} hisselerinin bilançosuna 7 günden az kaldı! Volatilite artabilir.")

tab1, tab2, tab3, tab4 = st.tabs([
    "🌐 MAKRO & OPEX", 
    "🔋 OMNI-MATRIX (Tüm Piller)", 
    "🦈 HAFTALIK MOMENTUM-GAP",
    "📋 OMNI RADAR & PORTFÖY"
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

# ---------------------------------------------------------
# TAB 2: OMNI-MATRIX (TÜM PİLLER & SCATTER)
# ---------------------------------------------------------
with tab2:
    st.subheader("🔋 Tüm Sektörler Pil Enerjisi & Contrarian Matris")
    st.markdown("Trade the theme you have, not the theme you want. Hangi temanın pili şarj oluyor? Hangi tema Volatilite Vakumuna (Hole) düştü? Bir bakışta gör.")
    
    with st.spinner("Tüm Matrix ve Pil verileri hesaplanıyor..."):
        df_m = fetch_matrix_data()
        if not df_m.empty:
            # PİL GRID EKRANI
            theme_avg = df_m.groupby('Sektör')['RSI'].mean().reset_index()
            cols = st.columns(4)
            for i, row in theme_avg.iterrows():
                with cols[i % 4]:
                    col = "#00ff88" if row['RSI'] > 60 else "#ff3333" if row['RSI'] < 40 else "#f1c40f"
                    draw_battery(row['Sektör'], row['RSI'], col)
            
            st.divider()
            
            # PLOTLY SCATTER (Tooltipli)
            fig = go.Figure()
            for state in ["Aşırı Alım (Dağıtım)", "Sıkışma (VCP)", "Vakum (Contrarian)"]:
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
        **Kurallar:** 1. **Prior Momentum (VCP):** Gap öncesi haftalarda mum boyları giderek daralmalı (Swimming like sharks).
        2. **Valid Gap:** Pazartesi açılışı, geçen haftanın en yüksek değerinin üzerinde olmalı (Lunge).
        3. **Iron Discipline:** Bu tablo sadece yüksek inançlı (High Conviction) hisseleri 1 Haftalık (1W) periyotta tarar.
    """)
    
    with st.spinner("1W Kinetik Boşluklar aranıyor..."):
        df_wk = calculate_signals(raw_tickers, interval="1wk")
        if not df_wk.empty:
            df_wk_disp = df_wk[['Ticker', 'Sinyal', 'Fiyat', 'Whale Power']]
            st.dataframe(df_wk_disp.style.map(style_signals, subset=['Sinyal']), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 4: OMNI RADAR & MÜKEMMEL PORTFÖY
# ---------------------------------------------------------
with tab4:
    st.subheader("📋 Genel Portföy & OMNI Radar İzleme Listesi")
    
    with st.spinner("Portföy simülasyonu ve veriler hesaplanıyor..."):
        df_port = calculate_signals(raw_tickers, interval="1d")
        if not df_port.empty:
            df_port_final = pd.merge(df_port, df_alerts[['Ticker', 'Fair Value', 'Bilanço']], on="Ticker", how="left")
            df_port_final = df_port_final[['Ticker', 'Sinyal', 'Fiyat', 'Fair Value', 'Bilanço', '1 Gün (%)', '1 Hafta (%)', 'Whale Power', 'Fusion']]
            
            st.dataframe(
                df_port_final.style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']),
                use_container_width=True, height=750, hide_index=True
            )
