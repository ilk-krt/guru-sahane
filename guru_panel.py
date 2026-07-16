import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime
import calendar
import time

# ==========================================
# 0. AYARLAR & AGRESİF DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER APEX V136.0 - KOKPİT", page_icon="🏛️")

st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    p, h1, h2, h3, h4, h5, h6, span, label, div { color: #e0e0e0 !important; }
    div[data-baseweb="select"] > div { background-color: #111111 !important; color: #ffffff !important; border: 1px solid #00ff88 !important; }
    div[data-baseweb="popover"] > div { background-color: #111111 !important; }
    ul[role="listbox"] { background-color: #111111 !important; }
    ul[role="listbox"] li { color: #ffffff !important; background-color: #111111 !important; }
    ul[role="listbox"] li:hover { background-color: #222222 !important; color: #00ff88 !important; font-weight: bold !important; }
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; color: #ffffff !important; }
    div.stButton > button { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #444 !important; border-radius: 8px !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    </style>
""", unsafe_allow_html=True)

if 'active_trigger' not in st.session_state: st.session_state.active_trigger = "OPEX PINNING"
if 'macro_nonce' not in st.session_state: st.session_state.macro_nonce = str(time.time())

# ==========================================
# 1. SİSTEM TETİKLEYİCİLERİ & TAM HİSSE EVRENİ
# ==========================================
SYSTEM_TRIGGERS = {
    "GAMMA SQUEEZE": {"color": "#00ff88", "battery": {"Stocks": 95, "Bonds": 20, "Crypto": 90, "Commodities": 55, "RealEstate": 65}},
    "OPEX PINNING": {"color": "#f1c40f", "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 48, "Commodities": 52, "RealEstate": 50}},
    "GEOPOLITICAL SHOCK": {"color": "#ff3333", "battery": {"Stocks": 25, "Bonds": 85, "Crypto": 35, "Commodities": 95, "RealEstate": 40}},
    "STAGFLATION / SUPPLY SUPER-CYCLE": {"color": "#e67e22", "battery": {"Stocks": 40, "Bonds": 15, "Crypto": 60, "Commodities": 98, "RealEstate": 75}},
    "FED HAWKISH PIVOT / LIQUIDITY CRUNCH": {"color": "#9b59b6", "battery": {"Stocks": 15, "Bonds": 90, "Crypto": 10, "Commodities": 35, "RealEstate": 25}}
}

MAIN_SECTORS = {
    "XLK": "Ana Sektör: Teknoloji", "XLI": "Ana Sektör: Sanayi", "XLE": "Ana Sektör: Enerji",
    "XLV": "Ana Sektör: Sağlık", "XLF": "Ana Sektör: Finans", "XLY": "Ana Tüketim",
    "XLB": "Ana Sektör: Materyal", "XLC": "Ana Sektör: İletişim", "XLRE": "Ana Sektör: Gayrimenkul",
    "XLU": "Ana Sektör: Kamu Hizmetleri"
}

ETF_INFO = {
    "XLU": {"area": "Utilities & Şebeke", "stocks": ["NEE", "SO", "DUK", "CEG", "AEP", "SRE", "D", "ETR", "VST", "XEL"]},
    "PAVE": {"area": "Altyapı Yenileme", "stocks": ["ETN", "PH", "HUBB", "POWL", "TT", "CARR", "JCI", "URI", "FAST", "GWW", "VMC", "MLM", "EXP", "J", "ACM", "PWR", "EME"]},
    "XLK": {"area": "Teknoloji Devleri", "stocks": ["NVDA", "AAPL", "MSFT", "MU", "AVGO", "AMD", "INTC", "CSCO", "PLTR", "AMAT"]},
    "CLOU": {"area": "Bulut Bilişim", "stocks": ["DOCN", "DDOG", "AKAM", "TWLO", "ZS", "SNOW", "PAYC", "ZM", "NOW", "NET"]},
    "IGV": {"area": "Yazılım ve SaaS", "stocks": ["MSFT", "CRM", "ORCL", "ADBE", "NOW", "INTU", "WDAY", "PLTR", "PAYC", "SNOW", "DDOG", "DT", "TEAM", "PANW", "CRWD", "NET"]},
    "CIBR": {"area": "Siber Güvenlik", "stocks": ["CRWD", "PANW", "ZS", "FTNT", "CHKP", "CSCO", "JNPR", "OKTA", "CYBR", "TENB", "QLYS", "GEN", "NET", "AKAM"]},
    "BOTZ": {"area": "Robotik ve Endüstriyel AI", "stocks": ["NVDA", "ISRG", "PATH", "AI", "CGNX", "ABBN", "ROK"]},
    "AIQ": {"area": "Global Yapay Zekâ", "stocks": ["000660.KS", "MU", "005930.KS", "INTC", "AMD", "CSCO", "AVGO", "NVDA", "TSM", "GOOGL", "AAPL"]},
    "SOXX": {"area": "Çip Tasarım ve Ekipman", "stocks": ["MU", "AMD", "INTC", "AVGO", "NVDA", "MRVL", "AMAT", "QCOM", "MPWR", "TXN", "ADI", "MCHP", "NXPI", "LRCX", "KLAC"]},
    "SMH": {"area": "Global Çip Dökümhaneleri", "stocks": ["TSM", "INTC", "ASML", "NVDA", "AMD", "AVGO", "MRVL", "QCOM", "AMAT", "LRCX", "KLAC", "TOELY"]},
    "EUV": {"area": "Litografi & Fotonik", "stocks": ["TSM", "ASML", "GLW", "LRCX", "AMAT", "LITE", "CIEN", "KLAC", "COHR", "MTSI"]},
    "ARKX": {"area": "Uzay İnovasyonu", "stocks": ["RKLB", "AMD", "LHX", "TER", "KTOS", "DE", "AVAV", "AMZN", "ACHR", "GOOG"]},
    "XAR": {"area": "Savunma ve Jet Ekipmanları", "stocks": ["LMT", "RTX", "NOC", "GD", "LHX", "TDG", "HWM", "HEI", "SPR", "CW", "TXT", "BWXT", "HII", "PSN"]},
    "UFO": {"area": "Uydu ve Uzay Ekonomisi", "stocks": ["SIRI", "IRDM", "SATS", "VSAT", "GRMN", "LMT", "BA", "NOC", "LHX", "RKLB", "SPCE"]},
    "XLE": {"area": "Entegre Enerji Devleri", "stocks": ["XOM", "CVX", "COP", "EOG", "OXY", "DVN", "SLB", "BKR", "HAL", "MPC", "VLO", "PSX", "WMB", "OKE", "KMI"]},
    "XOP": {"area": "Petrol ve Gaz Arama", "stocks": ["FANG", "CTRA", "EQT", "MRO", "APA", "AR", "CHK", "RRC", "MTDR", "COP", "XOM", "CVX", "OXY"]},
    "OIH": {"area": "Sondaj Ekipmanları", "stocks": ["SLB", "HAL", "BKR", "RIG", "NE", "VAL", "SDRL", "HP", "PTEN", "NBR", "NOV", "CHX", "WHD", "TDW"]},
    "COPX": {"area": "Bakır Üreticileri", "stocks": ["FCX", "SCCO", "IVPAF", "ANFGY", "LUNMF", "FQVLF", "BHP", "RIO", "TECK", "GLNCY", "VALE"]},
    "LIT": {"area": "Lityum ve Batarya", "stocks": ["ALB", "SQM", "ALTM", "TSLA", "RIVN", "LCID"]},
    "URA": {"area": "Uranyum ve Nükleer", "stocks": ["CCJ", "KAP", "NXE", "UEC", "UUUU", "DNN", "BWXT", "LEU", "SMR", "CEG"]},
    "REMX": {"area": "Nadir Top Elementleri", "stocks": ["MP", "LYSDY", "ALB", "ALTM"]},
    "GDX": {"area": "Altın Madencileri", "stocks": ["NEM", "GOLD", "AEM", "GFI", "AU", "KGC", "WPM", "FNV", "RGLD", "EGO", "BTG", "HMY", "SBSW"]},
    "XME": {"area": "Metal ve Çelik Üreticileri", "stocks": ["NUE", "STLD", "CLF", "X", "RS", "AA", "KALU", "FCX", "AMR", "HCC", "ARCH", "HL", "RGLD"]},
    "ICLN": {"area": "Küresel Temiz Enerji", "stocks": ["ENPH", "FSLR", "SEDG", "VWDRY", "ORSTY", "IBDRY", "NEP", "PLUG", "BE"]},
    "JOUL": {"area": "Elektrik Altyapısı", "stocks": ["PWR", "ETN", "QUAN", "HUBB"]},
    "XLY": {"area": "İsteğe Bağlı Tüketim", "stocks": ["AMZN", "EBAY", "TSLA", "F", "GM", "HD", "LOW", "MCD", "SBUX", "MAR", "HLT", "CMG", "NKE", "TJX", "LULU", "BKNG", "ABNB"]},
    "XRT": {"area": "Perakende", "stocks": ["CVNA", "AMZN", "CHWY", "ANF", "GPS", "BOOT", "ROST", "TJX", "M", "JWN", "COST", "WMT", "TGT", "DLTR", "DG", "AZO", "BBY"]},
    "XHB": {"area": "Ev İnşaatı ve Malzemeler", "stocks": ["DHI", "LEN", "PHM", "NVR", "TOL", "KBH", "HD", "LOW", "BLDR", "SHW", "WHR", "TT", "MHK", "OC"]},
    "XLV": {"area": "Sağlık ve Mega İlaç", "stocks": ["LLY", "MRK", "ABBV", "PFE", "BMY", "JNJ", "UNH", "ELV", "HUM", "CVS", "AMGN", "GILD", "REGN", "VRTX", "TMO", "DHR"]},
    "IHI": {"area": "Tıbbi Cihazlar", "stocks": ["ISRG", "SYK", "BSX", "MDT", "EW", "ZBH", "DXCM", "ABT", "TMO", "BDX"]},
    "XBI": {"area": "Biyoteknoloji", "stocks": ["VRTX", "AMGN", "GILD", "MRNA", "BIIB", "REGN", "ALNY", "BMRN", "INCY", "UTHR", "EXAS"]},
    "ARKG": {"area": "Genom ve Kök Hücre", "stocks": ["CRSP", "NTLA", "BEAM", "EDIT", "EXAS", "GH", "TWST", "PACB", "ILMN", "IONS", "ALNY", "SDGR", "RXRX"]},
    "XLRE": {"area": "Büyük GYO'lar", "stocks": ["PLD", "AMT", "CCI", "SBAC", "EQIX", "DLR", "SPG", "O", "WELL", "VTR", "PSA", "EXR"]},
    "REZ": {"area": "Konut ve Yaşam GYO", "stocks": ["WELL", "VTR", "OHI", "EQR", "AVB", "UDR", "CPT", "INVH", "AMH", "SUI", "ELS", "PSA", "CUBE"]},
    "SRVR": {"area": "Veri Merkezi ve Kuleler", "stocks": ["EQIX", "DLR", "AMT", "CCI", "SBAC", "IRM", "UNIT"]},
    "VNQ": {"area": "Geniş Gayrimenkul Pazarı", "stocks": ["PLD", "AMT", "EQIX", "CCI", "DLR", "SPG", "O", "KIM", "PSA", "AVB", "EQR", "WY", "RYN"]},
    "XLF": {"area": "Büyük Finans Devleri", "stocks": ["JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "V", "MA", "AXP", "BRK-B", "MMC", "CB", "PGR"]},
    "KRE": {"area": "Bölgesel Bankalar", "stocks": ["MTB", "RF", "HBAN", "FITB", "KEY", "CFG", "TFC", "FHN", "WAL", "ZION", "CMA", "NYCB"]},
    "ARKF": {"area": "Fintek İnovasyonu", "stocks": ["COIN", "HOOD", "SQ", "PYPL", "TOST", "AFRM", "SOFI", "SHOP", "MELI", "SE", "NU", "INTR"]},
    "XLC": {"area": "İletişim ve Dijital Medya", "stocks": ["META", "GOOGL", "PINS", "NFLX", "DIS", "WBD", "PARA", "TMUS", "T", "VZ", "CMCSA", "CHTR"]},
    "WGMI": {"area": "Bitcoin Madenciliği", "stocks": ["MARA", "RIOT", "CLSK", "HUT", "CIFR", "IREN", "WULF", "CORZ", "HIVE", "BTDR", "BRPHF", "NVDA", "AMD"]},
    "IYT": {"area": "Kargo ve Lojistik", "stocks": ["UNP", "CSX", "NSC", "UPS", "FDX", "EXPD", "JBHT", "ODFL", "UBER", "LYFT", "DAL", "UAL", "LUV"]},
    "JETS": {"area": "Havayolları Ekosistemi", "stocks": ["DAL", "UAL", "AAL", "LUV", "JBLU", "ALK", "ALGT", "ULCC", "SKYW", "BA", "ERJ", "EADSY", "IAG", "DLAKY", "AFLYY"]}
}

FUTURE_THEMES_MAP = {
    "Chokepoint (Darboğaz) Çarpanları": ["NVDA", "AVGO", "CEG", "ETN", "EQIX", "FCX", "PLD"],
    "Agentic AI & Yazılım": ["NOW", "ADEA", "DOCN", "SOUN", "TDIC", "ADBE", "DT", "S", "EXTR"],
    "Uzay Bilişimi (Space Computing)": ["PL", "BKSY", "SATL", "SPIR", "RKLB", "RDW", "VOYG", "VELO", "ASTS", "SIDU", "MNTS"],
    "Humanoid & Robotik Algı": ["MBLY", "AEVA", "OUST", "CGNX", "NOVT", "RR", "INDI", "ZBRA", "KLIC", "XPEV", "NEO", "VPG", "LASR"],
    "Neocloud & Enerji Pivotu": ["IREN", "NBIS", "DGXX", "APLD", "CIFR", "WULF", "CORZ", "BTDR", "CLSK", "MARA", "RIOT"],
    "Çip Mimarisi & Fotonik": ["NVDA", "ARM", "ASML", "LRCX", "KLAC", "TSM", "INTC", "AMD", "CDNS", "SNPS", "MU", "SNDK", "AMKR", "ASX", "ALAB", "MCHP", "RMBS", "COHR", "LITE", "APH", "AXTI", "AAOI", "POET"],
    "Güç, Soğutma & Altyapı": ["VRT", "ETN", "MPWR", "ADI", "DELL", "SMCI", "PENG", "SLNH", "FCEL", "FLNC", "NVTS", "WOLF"],
    "Nükleer & Temel Materyal": ["CEG", "TLN", "SMR", "NNE", "UUUU", "MP", "CRML", "ATLX", "BMNR"]
}

raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]

# BÜTÜN EVRENİ BİRLEŞTİR (Benzersiz ve Sıralı)
all_market_stocks = list(set(
    list(MAIN_SECTORS.keys()) + 
    [s for data in ETF_INFO.values() for s in data["stocks"]] + 
    [t for tkrs in FUTURE_THEMES_MAP.values() for t in tkrs] + 
    raw_tickers
))
DEFAULT_UNIVERSE = sorted(all_market_stocks)

# ==========================================
# 2. KURUMSAL HABER & MAKRO MOTORU
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
    
    if 0 <= days_to_opex <= 10:
        alerts.append(f"🚨 **OPEX DYNAMICS (Vadeye {days_to_opex} Gün):** Options expiration yaklaşıyor. Market Maker'lar long gamma pozisyonunda kilitli. Yapay bir sakinlik ve ağır **Strike Pinning** mekanizması devrede.")
    elif -3 <= days_to_opex < 0:
        alerts.append("💥 **GAMMA UNWIND & REBALANCE:** OpEx tamamlandı. Dealer hedge yükümlülükleri eriyor. Sert **Dealer Gamma Unwinds** ve kurumsal **Systematic Flow Rebalances** dalgasına hazırlıklı olun.")
    else:
        alerts.append(f"📊 **CLEAN FLOW:** OpEx gravitesi zayıf. Fiyat hareketleri tamamen Dark Pool emir blokları ve tematik **Basket Hedging** akışları üzerinden şekilleniyor.")

    if trigger == "GEOPOLITICAL SHOCK":
        alerts.extend(["🌍 **SUPPLY SHOCK:** Jeopolitik tansiyon zirvede. Algoritmik fonlar $HULL (Deniz Lojistiği) ve $GASZ (Doğalgaz) sepetlerine ağır sermaye park ediyor.", "🛢️ **CONTRARIAN FLOW:** Büyüme tezi rafa kalktı. Nakit, emtia ve sert varlıklara sığınıyor."])
    elif trigger == "GAMMA SQUEEZE":
        alerts.extend(["📈 **VOLATILITY ACCELERATION:** AI Altyapı ve Çip mimarilerinde kurumsal opsiyon talebi zirvede.", "🤖 **RE-RATING MATRIX:** Akıllı para otonom sistemler ve Robotik katmanında hacim büyütüyor."])
    elif trigger == "STAGFLATION / SUPPLY SUPER-CYCLE":
        alerts.extend(["🌾 **HARD COMMODITIES BOOM:** Arz tedarik darboğazları kalıcı enflasyonu besliyor. Sermaye Bakır, Uranyum ve Nadir Elementler şebekelerine akıyor."])
    elif trigger == "FED HAWKISH PIVOT / LIQUIDITY CRUNCH":
        alerts.extend(["🏛️ **REVERSE REPO DRAIN:** Fed likidite musluklarını sıkıyor. Riskli varlıklardan muazzam bir çıkış var.", "💵 **CASH IS KING:** Kısa vadeli tahviller ve nakit dışındaki tüm piller deşarj moduna geçti."])
    else:
        alerts.extend(["⚖️ **EQUITY NEUTRAL:** Piyasa makro kararları konsolide ediyor. Kantitatif fonlar arbitraj çalıştırıyor."])
        
    return alerts

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
        c.node("REAL", "Gayrimenkul", shape='box', style='filled', fillcolor='#827717', fontcolor='white')
    bat = trigger_data['battery']
    def get_pen(val): return str(max(2.0, val / 10))
    def get_col(val): return "#00ff88" if val >= 60 else "#ff3333" if val <= 40 else "#888"
    dot.edge("FIAT", "USD", color="#aaa", penwidth="3")
    dot.edge("USD", "STOCK", color=get_col(bat['Stocks']), penwidth=get_pen(bat['Stocks']))
    dot.edge("USD", "BOND", color=get_col(bat['Bonds']), penwidth=get_pen(bat['Bonds']))
    dot.edge("USD", "CRYPTO", color=get_col(bat['Crypto']), penwidth=get_pen(bat['Crypto']))
    dot.edge("USD", "COMM", color=get_col(bat['Commodities']), penwidth=get_pen(bat['Commodities']))
    dot.edge("COMM", "REAL", color=get_col(bat['RealEstate']), penwidth=get_pen(bat['RealEstate']), style="dashed")
    st.graphviz_chart(dot, use_container_width=True)

# ==========================================
# 3. KUSURSUZ YALITILMIŞ BİLANÇO, OPEX & ADİL DEĞER MOTORU
# ==========================================
@st.cache_data(ttl=3600)
def fetch_opex_fair_value(ticker_list):
    data = []
    
    if not ticker_list:
        return pd.DataFrame()
        
    for t in ticker_list:
        tk = yf.Ticker(t)
        
        # Standart Boş Değerler Tanımlaması (Hata durumunda bunlar ekranda kalır)
        current = 0
        fv = "Bilinmiyor"
        gap = "-"
        
        earn_date_str = "Bilinmiyor"
        days_left = "-"
        days_left_sort = 9999
        
        max_pain_str = "-"
        gamma_squeeze_str = "-"
        opex_date_str = "-"
        opex_days_str = "-"

        # ------------------------------------------------
        # 1. BLOK: ADİL DEĞER VE FİYAT (Tamamen Bağımsız)
        # ------------------------------------------------
        try:
            info = tk.info
            current = info.get('currentPrice', info.get('previousClose', 0))
            fv = info.get('targetMeanPrice', info.get('targetMedianPrice', 'Bilinmiyor'))
            
            if isinstance(fv, (int, float)) and isinstance(current, (int, float)) and current > 0:
                diff = ((fv / current) - 1) * 100
                gap = f"%{diff:.1f} {'Ucuz' if diff > 0 else 'Pahalı'}"
        except Exception:
            pass 

        # ------------------------------------------------
        # 2. BLOK: BİLANÇO TARİHİ (Tamamen Bağımsız)
        # ------------------------------------------------
        try:
            cal = tk.calendar
            first_date = None

            if isinstance(cal, dict) and 'Earnings Date' in cal:
                dates = cal['Earnings Date']
                if isinstance(dates, list) and len(dates) > 0:
                    first_date = dates[0]
                elif dates:
                    first_date = dates
            elif hasattr(cal, 'empty') and not cal.empty:
                if 'Earnings Date' in cal:
                    first_date = cal['Earnings Date'].iloc[0]
                elif 'Earnings Date' in cal.index:
                    first_date = cal.loc['Earnings Date'].iloc[0]

            if first_date:
                if hasattr(first_date, 'date'):
                    earn_date = first_date.date()
                else:
                    earn_date = pd.to_datetime(first_date).date()
                    
                days_left_sort = (earn_date - datetime.now().date()).days
                
                if days_left_sort >= 0:
                    days_left = f"{days_left_sort} Gün"
                    earn_date_str = earn_date.strftime("%d-%m-%Y")
                else:
                    earn_date_str = "Bekleniyor"
        except Exception:
            pass 

        # ------------------------------------------------
        # 3. BLOK: OPEX, MAX PAIN & GAMMA SQUEEZE (Tamamen Bağımsız)
        # ------------------------------------------------
        try:
            expirations = tk.options
            if expirations:
                nearest_exp = expirations[0] 
                chain = tk.option_chain(nearest_exp)
                
                calls = chain.calls.copy()
                puts = chain.puts.copy()
                
                calls['openInterest'] = calls['openInterest'].fillna(0)
                puts['openInterest'] = puts['openInterest'].fillna(0)
                
                # Max Pain Vektörel Hesaplama
                strikes = sorted(set(calls['strike']).union(set(puts['strike'])))
                min_total_pain = float("inf")
                best_strike = 0
                
                for test_strike in strikes:
                    call_pain = (test_strike - calls['strike']).clip(lower=0) * calls['openInterest']
                    put_pain = (puts['strike'] - test_strike).clip(lower=0) * puts['openInterest']
                    total_pain = call_pain.sum() + put_pain.sum()
                    
                    if total_pain < min_total_pain:
                        min_total_pain = total_pain
                        best_strike = test_strike
                        
                max_pain_str = f"${best_strike:.2f}"
                
                # Gamma Squeeze (Call Wall) Hesaplaması
                if not calls.empty and calls['openInterest'].sum() > 0:
                    max_call_oi_idx = calls['openInterest'].idxmax()
                    if pd.notna(max_call_oi_idx):
                        gamma_strike = calls.loc[max_call_oi_idx, 'strike']
                        gamma_squeeze_str = f"${gamma_strike:.2f}"
                
                # Opex Tarihi ve Kalan Gün Hesaplaması
                exp_date = datetime.strptime(nearest_exp, '%Y-%m-%d').date()
                days_left_opex = (exp_date - datetime.now().date()).days
                opex_date_str = exp_date.strftime("%d-%m-%Y")
                opex_days_str = f"{max(0, days_left_opex)} Gün"
        except Exception:
            pass 
            
        # Hatasız toplanan tüm verileri evrene kaydet
        data.append({
            "Hisse / ETF": t,
            "Güncel Fiyat": f"${current:.2f}" if current > 0 else "-",
            "Max Pain Noktası": max_pain_str,
            "Gamma Squeeze (Call Wall)": gamma_squeeze_str,
            "OpEx Tarihi": opex_date_str,
            "OpEx Kalan": opex_days_str,
            "Adil Değer (Fair Value)": f"${fv:.2f}" if isinstance(fv, (int, float)) else fv,
            "Potansiyel": gap,
            "Bilanço Tarihi": earn_date_str,
            "Bilanço Kalan": days_left,
            "_sort": days_left_sort
        })
            
    df = pd.DataFrame(data).sort_values(by="_sort")
    df = df.drop(columns=["_sort"])
    return df

def style_percentages(val):
    if isinstance(val, str) and "%" in val:
        if "Ucuz" in val: return "color: #00ff88; font-weight: bold;"
        if "Pahalı" in val: return "color: #ff3333; font-weight: bold;"
    return ''

# ==========================================
# 4. KOKPİT ARAYÜZÜ ATEŞLEME
# ==========================================
tab1, tab2 = st.tabs([
    "🌐 INSTITUTIONAL DESK (Makro & Likidite)", 
    "📊 OPEX, GAMMA & BİLANÇO RADARI"
])

# ---------------------------------------------------------
# TAB 1: GÜÇLENDİRİLMİŞ MAKRO & OPEX KOKPİT
# ---------------------------------------------------------
with tab1:
    st.subheader("⚙️ Institutional Desk: Gelişmiş Makro Tetikleyiciler & Likidite Akışları")
    
    col_refresh, col_empty = st.columns([1, 4])
    if col_refresh.button("🔄 Makro Motoru ve Akışı Güncelle", use_container_width=True):
        st.session_state.macro_nonce = str(time.time())
        st.success("Makro akış simülatörü sıfırlandı!")
        
    t_cols = st.columns(5)
    for i, trig in enumerate(SYSTEM_TRIGGERS.keys()):
        with t_cols[i]:
            if st.button(f"Tetikleyici: {trig}", use_container_width=True):
                st.session_state.active_trigger = trig

    alerts = generate_institutional_news(st.session_state.active_trigger)
    for alert in alerts:
        st.markdown(f"<div style='border-left: 3px solid {SYSTEM_TRIGGERS[st.session_state.active_trigger]['color']}; padding-left: 10px; margin-bottom: 10px; font-size:1rem; background-color:#1a1a1a; padding:10px; border-radius:5px;'>{alert}</div>", unsafe_allow_html=True)
    
    st.divider()
    
    col_chart, col_docs = st.columns([3, 2])
    
    with col_chart:
        st.markdown(f"#### 💸 **Sermaye Akış Rotası:** ({st.session_state.active_trigger})")
        draw_smart_money_flow(SYSTEM_TRIGGERS[st.session_state.active_trigger])
        
    with col_docs:
        st.markdown("""
        <div style="background-color: #111; padding: 20px; border-radius: 10px; border: 1px solid #333;">
            <h4 style="color: #00ff88; margin-top: 0;">📚 Kurumsal Piyasa Mekanikleri Kontrol Listesi</h4>
            <hr style="border-color: #222;">
            <p><strong>1. GAMMA SQUEEZE MEKANİĞİ</strong></p>
            <p style="font-size: 0.85rem; color: #b0b0b0;">
                Bireysel ve kurumsal aktörlerin yoğun şekilde Out-of-the-Money (Kâr Dışı) Call opsiyon almasıyla tetiklenir. Opsiyonu satan piyasa yapıcılar (Dealers), delta risklerini sıfırlamak için spot piyasadan agresif hisse almak zorunda kalır. Fiyat yükseldikçe deltanın ivmelenmesi (Gamma Tepesi) dealer'ları daha fazla hisse almaya zorlar ve dikey, parabolik bir yükseliş döngüsü (Melt-Up) oluşur.
            </p>
            <hr style="border-color: #222; margin-top: 15px;">
            <p><strong>2. OPEX PINNING MEKANİĞİ</strong></p>
            <p style="font-size: 0.85rem; color: #b0b0b0;">
                Her ayın 3. Cuma günü gerçekleşen opsiyon vadelerinin (OpEx) yaklaşmasıyla oluşur. Yoğun açık pozisyon (Open Interest) bulunan büyük strike (kullanım) fiyatlarında, piyasa yapıcıların 'Long Gamma' profilinde olması fiyatı o seviyeye doğru çeker ve hapseder. Piyasa yapıcı fiyat yükselirken satıp düşerken alarak volatiliteyi yapay olarak baskılar (Gravity Effect).
            </p>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: MANUEL YÖNETİLEBİLİR OPEX & BİLANÇO RADARI
# ---------------------------------------------------------
with tab2:
    st.subheader("🎯 OpEx Max Pain, Gamma Squeeze & Değerleme Matrisi")
    
    st.info(f"Sistemde toplam **{len(DEFAULT_UNIVERSE)}** adet Kurumsal Hisse ve Sektör ETF'i bulunmaktadır. Tarama işlemi bağlantı hızınıza bağlı olarak 1-2 dakika sürebilir.")
    
    # Tüm evren otomatik olarak seçili gelir
    selected_tickers = st.multiselect(
        "Taranacak Evreni Düzenle (Hisse veya ETF Sembolü Yazarak Ekleyebilir/Çıkarabilirsiniz):",
        options=DEFAULT_UNIVERSE, 
        default=DEFAULT_UNIVERSE
    )
    
    if st.button("🚀 Tüm Kapsamı Tara (Tam Evren)", use_container_width=True, type="primary"):
        with st.spinner(f"{len(selected_tickers)} sembol için veri ağları taranıyor... Lütfen bekleyin."):
            df_radar = fetch_opex_fair_value(selected_tickers)
            
            if not df_radar.empty:
                st.dataframe(
                    df_radar.style.map(style_percentages, subset=['Potansiyel']),
                    use_container_width=True, 
                    height=800, 
                    hide_index=True
                )
            else:
                st.warning("Veri çekilemedi. Bağlantınızı kontrol edin.")
