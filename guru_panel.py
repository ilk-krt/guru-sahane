import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import yfinance as yf
from datetime import datetime, timedelta
import calendar
import time

# ==========================================
# 0. AYARLAR & AGRESİF DARK MODE CSS
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER APEX V134.0", page_icon="🏛️")

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
    [data-testid="stExpander"] { background-color: #111111 !important; border: 1px solid #333 !important; border-radius: 8px !important; }
    [data-testid="stExpander"] summary p { color: #00ff88 !important; font-weight: bold !important; font-size: 1.1rem !important; }
    div.stButton > button { background-color: #1a1a1a !important; color: #ffffff !important; border: 1px solid #444 !important; border-radius: 8px !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    .battery-container { width: 100%; background-color: #222; border-radius: 10px; margin: 5px 0 15px 0; border: 1px solid #444; position: relative; height: 25px; overflow: hidden; }
    .battery-fill { height: 100%; border-radius: 8px; transition: width 0.5s ease; display: flex; align-items: center; justify-content: flex-end; padding-right: 10px; font-weight: bold; color: #000 !important; font-size: 0.9rem; }
    </style>
""", unsafe_allow_html=True)

if 'active_trigger' not in st.session_state: st.session_state.active_trigger = "OPEX PINNING"
if 'macro_nonce' not in st.session_state: st.session_state.macro_nonce = str(time.time())
if 'battery_nonce' not in st.session_state: st.session_state.battery_nonce = str(time.time())

# ==========================================
# 1. KURUMSAL NİŞ ETF & HİSSE EVRENİ (DERİNLEŞTİRİLMİŞ)
# ==========================================
MAIN_SECTORS = {
    "XLK": "Ana Sektör: Teknoloji", "XLI": "Ana Sektör: Sanayi", "XLE": "Ana Sektör: Enerji",
    "XLV": "Ana Sektör: Sağlık", "XLF": "Ana Sektör: Finans", "XLY": "Ana Tüketim",
    "XLB": "Ana Sektör: Materyal", "XLC": "Ana Sektör: İletişim", "XLRE": "Ana Sektör: Gayrimenkul",
    "XLU": "Ana Sektör: Kamu Hizmetleri"
}

GLOBAL_MAP = {
    "Teknoloji (Bulut & AI)": ["XLK", "CLOU", "IGV", "AIQ", "CIBR", "BOTZ"],
    "Yarı İletken (Çip Mimarisi)": ["SOXX", "SMH", "EUV"],
    "Enerji & Altyapı": ["XLE", "XOP", "OIH", "XLU", "URA", "ICLN", "PAVE", "JOUL"],
    "Emtia & Madencilik": ["COPX", "LIT", "REMX", "GDX", "XME"],
    "Lojistik & Havacılık": ["IYT", "JETS", "HULL"],
    "Savunma & Uzay": ["XAR", "ARKX", "UFO"],
    "Finans & Kripto": ["XLF", "KRE", "ARKF", "IBIT", "WGMI"],
    "Gayrimenkul & Veri Merkezleri": ["XLRE", "REZ", "SRVR", "VNQ"],
    "Tüketim & Perakende": ["XLY", "XRT", "XHB"],
    "Sağlık & Genomik": ["XLV", "IHI", "XBI", "ARKG"]
}

ETF_INFO = {
    # Kamu ve Altyapı
    "XLU": {"area": "Utilities & Şebeke", "stocks": ["NEE", "SO", "DUK", "CEG", "AEP", "SRE", "D", "ETR", "VST", "XEL"]},
    "PAVE": {"area": "Altyapı Yenileme", "stocks": ["ETN", "PH", "HUBB", "POWL", "TT", "CARR", "JCI", "URI", "FAST", "GWW", "VMC", "MLM", "EXP", "J", "ACM", "PWR", "EME"]},
    # Teknoloji ve Bulut
    "XLK": {"area": "Teknoloji Devleri", "stocks": ["NVDA", "AAPL", "MSFT", "MU", "AVGO", "AMD", "INTC", "CSCO", "PLTR", "AMAT"]},
    "CLOU": {"area": "Bulut Bilişim", "stocks": ["DOCN", "DDOG", "AKAM", "TWLO", "ZS", "SNOW", "PAYC", "ZM", "NOW", "NET"]},
    "IGV": {"area": "Yazılım ve SaaS", "stocks": ["MSFT", "CRM", "ORCL", "ADBE", "NOW", "INTU", "WDAY", "PLTR", "PAYC", "SNOW", "DDOG", "DT", "TEAM", "PANW", "CRWD", "NET"]},
    "CIBR": {"area": "Siber Güvenlik", "stocks": ["CRWD", "PANW", "ZS", "FTNT", "CHKP", "CSCO", "JNPR", "OKTA", "CYBR", "TENB", "QLYS", "GEN", "NET", "AKAM"]},
    "BOTZ": {"area": "Robotik ve Endüstriyel AI", "stocks": ["NVDA", "ISRG", "PATH", "AI", "CGNX", "ABBN", "ROK"]},
    "AIQ": {"area": "Global Yapay Zekâ", "stocks": ["000660.KS", "MU", "005930.KS", "INTC", "AMD", "CSCO", "AVGO", "NVDA", "TSM", "GOOGL", "AAPL"]},
    # Yarı İletkenler
    "SOXX": {"area": "Çip Tasarım ve Ekipman", "stocks": ["MU", "AMD", "INTC", "AVGO", "NVDA", "MRVL", "AMAT", "QCOM", "MPWR", "TXN", "ADI", "MCHP", "NXPI", "LRCX", "KLAC"]},
    "SMH": {"area": "Global Çip Dökümhaneleri", "stocks": ["TSM", "INTC", "ASML", "NVDA", "AMD", "AVGO", "MRVL", "QCOM", "AMAT", "LRCX", "KLAC", "TOELY"]},
    "EUV": {"area": "Litografi & Fotonik", "stocks": ["TSM", "ASML", "GLW", "LRCX", "AMAT", "LITE", "CIEN", "KLAC", "COHR", "MTSI"]},
    # Uzay ve Savunma
    "ARKX": {"area": "Uzay İnovasyonu", "stocks": ["RKLB", "AMD", "LHX", "TER", "KTOS", "DE", "AVAV", "AMZN", "ACHR", "GOOG"]},
    "XAR": {"area": "Savunma ve Jet Ekipmanları", "stocks": ["LMT", "RTX", "NOC", "GD", "LHX", "TDG", "HWM", "HEI", "SPR", "CW", "TXT", "BWXT", "HII", "PSN"]},
    "UFO": {"area": "Uydu ve Uzay Ekonomisi", "stocks": ["SIRI", "IRDM", "SATS", "VSAT", "GRMN", "LMT", "BA", "NOC", "LHX", "RKLB", "SPCE"]},
    # Enerji, Uranyum ve Madenler
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
    # Tüketim, Gayrimenkul, Kripto ve Lojistik
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

SYSTEM_TRIGGERS = {
    "GAMMA SQUEEZE": {"color": "#00ff88", "battery": {"Stocks": 95, "Bonds": 20, "Crypto": 90, "Commodities": 55, "RealEstate": 65}},
    "OPEX PINNING": {"color": "#f1c40f", "battery": {"Stocks": 50, "Bonds": 50, "Crypto": 48, "Commodities": 52, "RealEstate": 50}},
    "GEOPOLITICAL SHOCK": {"color": "#ff3333", "battery": {"Stocks": 25, "Bonds": 85, "Crypto": 35, "Commodities": 95, "RealEstate": 40}},
    "STAGFLATION / SUPPLY SUPER-CYCLE": {"color": "#e67e22", "battery": {"Stocks": 40, "Bonds": 15, "Crypto": 60, "Commodities": 98, "RealEstate": 75}},
    "FED HAWKISH PIVOT / LIQUIDITY CRUNCH": {"color": "#9b59b6", "battery": {"Stocks": 15, "Bonds": 90, "Crypto": 10, "Commodities": 35, "RealEstate": 25}}
}

# ==========================================
# 2. KURUMSAL HABER & OPEX MOTORU
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
        alerts.append(f"🚨 **OPEX DYNAMICS (Vadeye {days_to_opex} Gün):** Options expiration yaklaşıyor. Market Maker'lar long gamma pozisyonunda kilitli. Yapay bir sakinlik ve ağır **Strike Pinning** mekanizması devrede. Kanal kırılımları algoritmik tuzaklara (Whipsaw) aşırı duyarlıdır.")
    elif -3 <= days_to_opex < 0:
        alerts.append("💥 **GAMMA UNWIND & REBALANCE:** OpEx tamamlandı. Dealer hedge yükümlülükleri eriyor. Sert **Dealer Gamma Unwinds** ve kurumsal **Systematic Flow Rebalances** dalgasına hazırlıklı olun. Temel rasyoların bugün hiçbir önemi yoktur.")
    else:
        alerts.append(f"📊 **CLEAN FLOW:** OpEx gravitesi zayıf. Fiyat hareketleri tamamen Dark Pool emir blokları ve tematik **Basket Hedging** akışları üzerinden şekilleniyor.")

    if trigger == "GEOPOLITICAL SHOCK":
        alerts.extend(["🌍 **SUPPLY SHOCK:** Jeopolitik tansiyon zirvede. Algoritmik fonlar $HULL (Deniz Lojistiği) ve $GASZ (Doğalgaz) sepetlerine ağır sermaye park ediyor.", "🛢️ **CONTRARIAN FLOW:** Büyüme tezi rafa kalktı. Nakit, emtia ve sert varlıklara sığınıyor."])
    elif trigger == "GAMMA SQUEEZE":
        alerts.extend(["📈 **VOLATILITY ACCELERATION:** AI Altyapı ve Çip mimarilerinde kurumsal opsiyon talebi zirvede. Kurumsal emir akışları $JOUL ve $EUV kanallarındaki likiditeyi süpürüyor.", "🤖 **RE-RATING MATRIX:** Akıllı para otonom sistemler ve $CBOT (Robotik) katmanında hacim büyütüyor."])
    elif trigger == "STAGFLATION / SUPPLY SUPER-CYCLE":
        alerts.extend(["🌾 **HARD COMMODITIES BOOM:** Arz tedarik darboğazları kalıcı enflasyonu besliyor. Sermaye $COPX (Bakır), $URA (Uranyum) ve $REMX (Nadir Elementler) şebekelerine akıyor.", "💸 **BOND CAPITULATION:** Tahvillerden kaçan para emtia bazlı hisselerin nakit akışını fiyatlıyor."])
    elif trigger == "FED HAWKISH PIVOT / LIQUIDITY CRUNCH":
        alerts.extend(["🏛️ **REVERSE REPO DRAIN:** Fed likidite musluklarını sıkıyor. Riskli varlıklardan muazzam bir çıkış var. $IBIT ve yüksek çarpanlı teknoloji hisselerinde margin call riskleri tetikleniyor.", "💵 **CASH IS KING:** Kısa vadeli tahviller ve nakit dışındaki tüm piller deşarj moduna geçti."])
    else:
        alerts.extend(["⚖️ **EQUITY NEUTRAL:** Piyasa makro kararları konsolide ediyor. Kantitatif fonlar pariteler arası istatistiksel arbitraj (Statistical Arbitrage) çalıştırıyor."])
        
    return alerts

def draw_battery(label, current, color, delta_1d=0.0, delta_1w=0.0):
    d1_icon = f"🔺+{delta_1d:.1f}" if delta_1d > 0 else f"🔻{delta_1d:.1f}" if delta_1d < 0 else "➖ 0.0"
    d1_color = "#00ff88" if delta_1d > 0 else "#ff3333" if delta_1d < 0 else "#888888"
    
    st.markdown(f"""
        <div style="margin-bottom: 2px; font-size: 0.85rem; color: #ccc; display: flex; justify-content: space-between;">
            <span>{label}</span>
            <span style="color: {d1_color}; font-weight: bold; font-size: 0.75rem;">1D Değişim: {d1_icon}</span>
        </div>
        <div class="battery-container" style="height: 20px;">
            <div class="battery-fill" style="width: {min(max(current,0), 100)}%; background-color: {color}; font-size: 0.8rem;">%{int(current)}</div>
        </div>
    """, unsafe_allow_html=True)

def draw_etf_battery(label, current, prev_1d, prev_1w, color, delta_icon, info=""):
    chg_1d = current - prev_1d
    c1_sign = f"+{chg_1d:.1f}" if chg_1d >= 0 else f"{chg_1d:.1f}"
    c1_col = "#00ff88" if chg_1d >= 0 else "#ff3333"
    
    st.markdown(f"""
        <div style="margin-bottom: 2px; font-size: 0.85rem; color: #e0e0e0;">
            <strong>{label}</strong> {info}
            <span style="font-size:0.75rem; float:right; color:{c1_col}; font-weight:bold;">(Δ 1D: %{c1_sign}) {delta_icon}</span>
        </div>
        <div class="battery-container" style="height: 22px; margin-bottom: 12px; border-radius: 6px;">
            <div class="battery-fill" style="width: {min(max(current, 0), 100)}%; background-color: {color}; font-size: 0.8rem;">%{int(current)}</div>
        </div>
    """, unsafe_allow_html=True)

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
# 3. YFINANCE MATEMATİK & OMNI FUSION MOTORU
# ==========================================
def get_rma(s, period): return s.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

def get_rsi(s, period):
    delta = s.diff()
    ma_up = get_rma(delta.clip(lower=0), period)
    ma_down = get_rma(-1 * delta.clip(upper=0), period)
    rs = ma_up / ma_down.replace(0, 0.001)
    return 100 - (100 / (1 + rs))

def get_wma(s, period):
    weights = np.arange(1, period + 1)
    return s.rolling(period).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

@st.cache_data
def fetch_matrix_data(bypass_stamp):
    all_etfs = list(set([etf for etfs in GLOBAL_MAP.values() for etf in etfs]))
    # Add raw tickers for mapping
    all_etfs.extend(list(MAIN_SECTORS.keys()))
    end_date = datetime.now()
    raw_data = yf.download(all_etfs, start=end_date - timedelta(days=90), end=end_date, interval="1d", group_by='ticker', progress=False)
    matrix_results = []
    for t in all_etfs:
        try:
            df = raw_data[t].dropna() if len(all_etfs) > 1 else raw_data.dropna()
            if len(df) < 25: continue
            close = df['Close']
            
            rsi_series = get_rsi(close, 14)
            r14_current = rsi_series.iloc[-1]
            r14_1d_ago = rsi_series.iloc[-2] if len(rsi_series) > 1 else r14_current
            r14_1w_ago = rsi_series.iloc[-6] if len(rsi_series) > 5 else r14_current
            
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            current_bbw = (((sma20 + 2*std20) - (sma20 - 2*std20)) / sma20 * 100).iloc[-1]
            cat = next((k for k, v in GLOBAL_MAP.items() if t in v), "Diğer")
            
            if r14_current > 70: state, color = "Aşırı Alım (Dağıtım)", "#ff3333"
            elif r14_current < 35: state, color = "Vakum (Contrarian Fırsat)", "#00ff88"
            else: state, color = "Sıkışma (VCP)", "#f1c40f"
            
            delta_icon = "⬆️" if r14_current > r14_1d_ago else "⬇️" if r14_current < r14_1d_ago else "➖"
            
            matrix_results.append({
                "Sektör": cat, "ETF": t, "RSI": r14_current, "RSI_1D": r14_1d_ago, "RSI_1W": r14_1w_ago, 
                "BBW": current_bbw, "Durum": state, "Renk": color, "Delta_Icon": delta_icon
            })
        except: continue
    return pd.DataFrame(matrix_results)

@st.cache_data
def calculate_signals(ticker_list, interval="1d", bypass_stamp=""):
    if not ticker_list: return pd.DataFrame()
    end_date = datetime.now()
    try:
        if interval == "1d":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=90), end=end_date, interval="1d", group_by='ticker', progress=False)
        elif interval == "4h":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=50), end=end_date, interval="1h", group_by='ticker', progress=False)
        elif interval == "1wk":
            raw_data = yf.download(ticker_list, start=end_date - timedelta(days=200), end=end_date, interval="1wk", group_by='ticker', progress=False)
    except: return pd.DataFrame()

    results = []
    for t in ticker_list:
        try:
            df = raw_data[t].copy().dropna() if len(ticker_list) > 1 else raw_data.copy().dropna()
            if len(df) < 30: continue

            if interval == "4h":
                df.index = pd.to_datetime(df.index)
                df = df.resample('4h').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}).dropna()

            close, high, low, open_p, vol = df['Close'], df['High'], df['Low'], df['Open'], df['Volume']
            pct_1d = (close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0
            pct_1w = (close.iloc[-1] / close.iloc[-6] - 1) * 100 if len(close) > 5 else 0

            r14 = get_rsi(close, 14)
            v150_v_avg = vol.rolling(20).mean()
            ema1_s3 = close.ewm(span=5, adjust=False).mean()
            tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
            atr14 = get_rma(tr, 14)

            i_vwm_len = 14
            wma_cv = get_wma(close * vol, i_vwm_len)
            wma_v = get_wma(vol, i_vwm_len).clip(lower=0.001)
            raw_effort = wma_cv / wma_v
            eff_price = get_wma(raw_effort, 3)

            price_cross_eff_up = (close > eff_price) & (close.shift(1) <= eff_price.shift(1))
            price_cross_eff_dn = (close < eff_price) & (close.shift(1) >= eff_price.shift(1))

            eff_status = pd.Series("➖ NÖTR", index=close.index)
            eff_status.loc[close > eff_price] = "🟢 POZ"
            eff_status.loc[close < eff_price] = "🔴 NEG"
            eff_status.loc[price_cross_eff_up] = "🚀 UP KIRILIM"
            eff_status.loc[price_cross_eff_dn] = "🩸 DOWN KIRILIM"

            c_range_q = (high - low).clip(lower=0.001)
            delta_q = ((close - low) - (high - close)) / c_range_q
            delta_vol_q = (delta_q * vol).rolling(20).mean() / vol.rolling(20).mean().clip(lower=0.001)
            rvol_q = (vol / vol.rolling(20).mean().clip(lower=1)).clip(upper=2.5)

            base_pwr_q = ((r14 - 50) + (delta_vol_q * 50)) * rvol_q * 1.5
            logic_pwr_q = np.log(1 + np.exp(base_pwr_q / 5)) * 5
            logic_pwr_q = np.where((low > high.shift(2)) & (close > open_p), logic_pwr_q + 35, logic_pwr_q)

            log_w_q = np.log10(1 + np.clip(logic_pwr_q, 0, None))
            pct_w_q = np.clip((log_w_q * 65)**0.8 * 1.8, 0, 100)
            w_pwr_q = get_wma(pd.Series(pct_w_q, index=close.index), 2)

            pct_pro_q = w_pwr_q.ewm(span=3, adjust=False).mean()
            yellow_rest = (w_pwr_q.shift(1) < pct_pro_q.shift(1)) & (w_pwr_q.shift(2) < pct_pro_q.shift(2))
            cross_now = (w_pwr_q > pct_pro_q) & (w_pwr_q.shift(1) <= pct_pro_q.shift(1))
            whale_re_entry = cross_now & yellow_rest

            typ = (high + low + close) / 3
            mf = typ * vol
            pos_mf = mf.where(typ > typ.shift(), 0).rolling(14).sum()
            neg_mf = mf.where(typ < typ.shift(), 0).rolling(14).sum().replace(0, 0.001)
            mfi_14 = 100 - (100 / (1 + (pos_mf / neg_mf)))
            energy_lvl = (r14 + mfi_14) / 2.0
            is_hyper_power = (w_pwr_q >= 70) & (energy_lvl >= 70)

            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            b_up = sma20 + 2 * std20
            b_low = sma20 - 2 * std20

            tr_sma20 = tr.rolling(20).mean()
            k_mid = sma20
            k_up = k_mid + 1.5 * tr_sma20
            k_low = k_mid - 1.5 * tr_sma20

            is_sqz = (b_low > k_low) & (b_up < k_up)
            kc_range_half = (k_up - k_mid) / 3.0
            vol_hole = is_sqz & (close <= (k_mid - kc_range_half))

            bear_trap = (low < ema1_s3) & (close > ema1_s3) & (vol > v150_v_avg * 1.8)
            bull_trap = (high > ema1_s3) & (close < ema1_s3) & (vol > v150_v_avg * 1.8)

            h_fast = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
            h_slow = get_wma(h_fast, 9)
            snip_bb_dev = 2.0 * std20
            snip_kc_dev = 1.5 * atr14.rolling(20).mean()
            in_squeeze = snip_bb_dev < snip_kc_dev
            exp_buy = (~in_squeeze) & in_squeeze.shift(1) & (h_fast > h_slow) & (h_fast > 0)
            exp_sel = (~in_squeeze) & in_squeeze.shift(1) & (h_fast < h_slow) & (h_fast < 0)

            _kin_b = ((vol > v150_v_avg * 1.2) & (close > open_p)).astype(int)
            _tre_b = (close > close.ewm(span=34).mean()).astype(int)
            _kur_b = ((r14 > 50) & (r14.shift(1) <= 50)).astype(int)
            _wyc_b = ((low < low.shift(1)) & (close > open_p) & (close > high.shift(1))).astype(int)

            _kin_s = ((vol > v150_v_avg * 1.2) & (close < open_p)).astype(int)
            _tre_s = (close < close.ewm(span=34).mean()).astype(int)
            _kur_s = ((r14 < 50) & (r14.shift(1) >= 50)).astype(int)
            _wyc_s = ((high > high.shift(1)) & (close < open_p) & (close < low.shift(1))).astype(int)

            total_score_b = _kin_b + _tre_b + _kur_b + _wyc_b
            total_score_s = _kin_s + _tre_s + _kur_s + _wyc_s
            any_buy = total_score_b >= 2
            any_sel = total_score_s >= 2

            sig = "⚪ WAIT"
            if interval == "1wk":
                prior_momentum = (low.shift(1) >= low.shift(2)) & (high.shift(1) >= high.shift(2)) & (close.shift(1) > sma20.shift(1))
                bull_gap = (open_p > high.shift(1)) & (close > open_p)
                if prior_momentum.iloc[-1] and bull_gap.iloc[-1]: sig = "🚀 MOMENTUM GAP (UP)"
                elif (w_pwr_q.iloc[-1] > 80): sig = "🐋 WHALE ACCUMULATION"
                elif (r14.iloc[-1] < 35): sig = "🕳️ DEEP VALUE (DCA)"
            else:
                if price_cross_eff_up.iloc[-1]: sig = "🚀 UP KIRILIM"
                elif price_cross_eff_dn.iloc[-1]: sig = "🩸 DOWN KIRILIM"
                elif (any_buy.iloc[-1] & is_hyper_power.iloc[-1]): sig = "☄️ HYPER BUY"
                elif (any_sel.iloc[-1] & is_hyper_power.iloc[-1]): sig = "☄️ HYPER SELL"
                elif whale_re_entry.iloc[-1]: sig = "🔄 WHALE RE-ENTRY"
                elif vol_hole.iloc[-1]: sig = "🕳️ VOLA HOLE"
                elif bull_trap.iloc[-1]: sig = "⛔"
                elif bear_trap.iloc[-1]: sig = "✅"
                elif exp_buy.iloc[-1]: sig = "💥 EXP BUY"
                elif exp_sel.iloc[-1]: sig = "💥 EXP SELL"
                elif w_pwr_q.iloc[-1] >= 85: sig = "🐋 WHALE IN"
                elif any_buy.iloc[-1]: sig = "✅ BUY"
                elif any_sel.iloc[-1]: sig = "🔴 SELL"

            results.append({
                "Ticker": t, "Sinyal": sig, "Efor": eff_status.iloc[-1], "Fiyat": f"${close.iloc[-1]:.2f}",
                "Whale Power": float(f"{w_pwr_q.iloc[-1]:.1f}"), "Fusion": int(total_score_b.iloc[-1]),
                "1 Gün (%)": round(pct_1d, 2), "1 Hafta (%)": round(pct_1w, 2)
            })
        except Exception: 
            continue
    if results: return pd.DataFrame(results).sort_values(by="Fusion", ascending=False)
    return pd.DataFrame()

@st.cache_data
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
            funds.append({"Ticker": t, "Fair Value": fv, "Bilanço": earn_date, "DaysToEarn": days_to_earn})
        except: funds.append({"Ticker": t, "Fair Value": "N/A", "Bilanço": "N/A", "DaysToEarn": 999})
    return pd.DataFrame(funds)

# --- STYLER YARDIMCILARI ---
def style_signals(val):
    if isinstance(val, str):
        if 'GAP' in val: return 'background-color: #00e676; color: black; font-weight: bold;'
        if 'DEEP' in val: return 'background-color: #00b0ff; color: black; font-weight: bold;'
        if 'HYPER BUY' in val: return 'background-color: #827717; color: white; font-weight: bold;'
        if 'HYPER SELL' in val: return 'background-color: #4a0000; color: white; font-weight: bold;'
        if 'WHALE RE-ENTRY' in val: return 'background-color: #006064; color: white; font-weight: bold;'
        if 'WHALE IN' in val: return 'background-color: #01579b; color: white;'
        if 'VOLA HOLE' in val: return 'background-color: #4a148c; color: white;'
        if 'EXP BUY' in val: return 'background-color: #1b5e20; color: white; font-weight: bold;'
        if 'EXP SELL' in val: return 'background-color: #bf360c; color: white; font-weight: bold;'
        if 'BUY' in val: return 'background-color: #004d40; color: white; font-weight: bold;'
        if 'SELL' in val: return 'background-color: #3e2723; color: white; font-weight: bold;'
        if 'UP KIRILIM' in val: return 'background-color: #00FF88; color: black; font-weight: bold;'
        if 'DOWN KIRILIM' in val: return 'background-color: #FF1744; color: white; font-weight: bold;'
        if val == '⛔': return 'background-color: #b71c1c; color: white; font-size: 1.2rem; text-align: center;'
        if val == '✅': return 'background-color: #004d40; color: white; font-size: 1.2rem; text-align: center;'
    return 'background-color: #111111; color: white;'

def style_efor(val):
    if isinstance(val, str):
        if '🚀' in val: return 'background-color: #00FF88; color: black; font-weight: bold;'
        if '🩸' in val: return 'background-color: #FF1744; color: white; font-weight: bold;'
        if '🟢' in val: return 'color: #00FF88; font-weight: bold;'
        if '🔴' in val: return 'color: #FF1744; font-weight: bold;'
    return 'color: #888;'

def style_percentages(val):
    if isinstance(val, (float, int)): return f"color: {'#00ff88' if val > 0 else '#ff3333'}; font-weight: bold;"
    return ''

def render_heatmap(df, val_col, title):
    df_h = df.dropna(subset=[val_col]).sort_values(by=val_col, ascending=False)
    html = f"<div style='background:#111; padding:15px; border-radius:12px; border: 1px solid #333;'><h4 style='color:#00ff88; text-align:center; margin-bottom:15px; font-family: sans-serif;'>{title}</h4><div style='display: grid; grid-template-columns: repeat(auto-fill, minmax(75px, 1fr)); gap: 6px;'>"
    for _, row in df_h.iterrows():
        val = row[val_col]
        t = row['Ticker']
        if val > 0: bg, text_col = "#00b800" if val > 2 else "#006400", "#ffffff"
        elif val < 0: bg, text_col = "#b80000" if val < -2 else "#8b0000", "#ffffff"
        else: bg, text_col = "#ffffff", "#000000"
        html += f"<div style='background-color: {bg}; color: {text_col}; padding: 10px 2px; border-radius: 6px; text-align: center; display: flex; flex-direction: column; justify-content: center; height: 60px; box-shadow: 0 2px 4px rgba(0,0,0,0.3);'>"
        html += f"<div style='font-size: 0.85rem; font-weight: 800; font-family: monospace;'>{t}</div>"
        html += f"<div style='font-size: 0.75rem; font-weight: bold;'>{val:.2f}%</div>"
        html += "</div>"
    html += "</div></div>"
    return html

# ==========================================
# 5. KOKPİT ARAYÜZÜ ATEŞLEME
# ==========================================
all_etfs_to_scan = list(MAIN_SECTORS.keys()) + list(ETF_INFO.keys())
raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]
# ETF bileşenlerini de ana portföye dahil et (Dinamik Tarama İçin)
for k, v in ETF_INFO.items():
    raw_tickers.extend(v['stocks'])
portfolio_tickers = sorted(list(set(raw_tickers)))

etf_name_map = {k: v for k, v in MAIN_SECTORS.items()}
for k, v in ETF_INFO.items(): etf_name_map[k] = f"Alt Sektör: {v['area']}"

with st.spinner("Piyasa Radar Kontrolü (Bilanço & Değer)..."):
    df_alerts = fetch_fundamental_data(portfolio_tickers)
    urgent_earn = df_alerts[(df_alerts['DaysToEarn'] >= 0) & (df_alerts['DaysToEarn'] <= 7)]
    if not urgent_earn.empty:
        st.warning(f"🔔 **YAKLAŞAN BİLANÇO DİKKAT:** {', '.join(urgent_earn['Ticker'].tolist())} hisselerinin bilançosuna 7 günden az kaldı!")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🌐 MAKRO & OPEX", 
    "🔋 OMNI-MATRIX (Piller)",
    "🦅 KUŞBAKIŞI (Sektör Sinyalleri)",
    "🦈 HAFTALIK MOMENTUM-GAP",
    "🚨 4H & OMNI RADAR",
    "📋 MÜKEMMEL PORTFÖY",
    "🚀 FUTURE THEMES"
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
            <p style="font-size: 0.85rem; color: #00ff88;">
                <em>Strategic Implication:</em> Momentum tavan yapar, hacim ortalamaları katlanır. Teknikte 1 periyot teyitli EMA kırılımları ve Whale Power indikatörünün %85 üzerine fırlaması bu akışı doğrular. Kapanış odaklı (Close-only) zirve kırılımları izlenmelidir.
            </p>
            <hr style="border-color: #222; margin-top: 15px;">
            <p><strong>2. OPEX PINNING MEKANİĞİ</strong></p>
            <p style="font-size: 0.85rem; color: #b0b0b0;">
                Her ayın 3. Cuma günü gerçekleşen opsiyon vadelerinin (OpEx) yaklaşmasıyla oluşur. Yoğun açık pozisyon (Open Interest) bulunan büyük strike (kullanım) fiyatlarında, piyasa yapıcıların 'Long Gamma' profilinde olması fiyatı o seviyeye doğru çeker ve hapseder. Piyasa yapıcı fiyat yükselirken satıp düşerken alarak volatiliteyi yapay olarak baskılar (Gravity Effect).
            </p>
            <p style="font-size: 0.85rem; color: #f1c40f;">
                <em>Strategic Implication:</em> Vadeye 10 gün kala hacim düşer, endeksler sıkışır (VCP yapısı). Kırılım yönlü sinyaller genellikle sahtedir (Whipsaw tuzu). Gerçek trend vade sonrasındaki kurumsal portföy dengelenmeleriyle (Gamma Unwind) başlar.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: DELTA ENTEGRELİ OMNI-MATRIX (PİLLER)
# ---------------------------------------------------------
with tab2:
    st.subheader("🔋 Tüm Sektörler Pil Enerjisi & Contrarian Değişim Matrisi")
    
    col_ref2, col_emp2 = st.columns([1, 4])
    if col_ref2.button("🔄 Pil Enerji Matrisini Sıfırla ve Güncelle", use_container_width=True):
        st.session_state.battery_nonce = str(time.time())
        st.success("Tüm piller ve matris verileri yfinance'tan yeniden çekildi!")
        
    with st.spinner("Tüm Matrix ve Dönemsel Pil Değişimleri Hesaplanıyor..."):
        df_m = fetch_matrix_data(st.session_state.battery_nonce)
        if not df_m.empty:
            theme_avg = df_m.groupby('Sektör')[['RSI', 'RSI_1D', 'RSI_1W']].mean().reset_index()
            cols = st.columns(4)
            for i, row in theme_avg.iterrows():
                with cols[i % 4]:
                    delta_1d_calc = row['RSI'] - row['RSI_1D']
                    col = "#00ff88" if row['RSI'] > 60 else "#ff3333" if row['RSI'] < 40 else "#f1c40f"
                    draw_battery(row['Sektör'], row['RSI'], col, delta_1d=delta_1d_calc)
            
            st.divider()
            
            fig = go.Figure()
            for state in ["Aşırı Alım (Dağıtım)", "Sıkışma (VCP)", "Vakum (Contrarian Fırsat)"]:
                df_s = df_m[df_m["Durum"] == state]
                fig.add_trace(go.Scatter(
                    x=df_s["BBW"], y=df_s["RSI"], mode='markers+text',
                    marker=dict(size=14, color=df_s["Renk"], line=dict(width=1, color='white'), opacity=0.9),
                    text=df_s["ETF"], textposition="top center", name=state,
                    hovertemplate="<b>%{text}</b><br>Tema: " + df_s["Sektör"] + "<br>Enerji (Flow): %{y:.1f}<br>Sıkışma: %{x:.1f}%<extra></extra>"
                ))
            fig.add_hline(y=70, line_dash="dash", line_color="#ff3333", annotation_text="Aşırı Isınma (Dağıtım)")
            fig.add_hline(y=35, line_dash="dash", line_color="#00ff88", annotation_text="Yükselen Vakum (DCA)")
            fig.update_layout(title="Dinamik Kurumsal Enerji Matrisi", xaxis_title="Bollinger Bant Genişliği (Sıkışma Katsayısı)", yaxis_title="RSI (Hacimsel Enerji Oranı)", height=500, paper_bgcolor="#050505", plot_bgcolor="#111", font=dict(color="#e0e0e0"))
            st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.subheader("🔋 Alt Sektör & ETF Pil Derinliği (Canlı 1D Değişim Deltası ile)")
            for theme, etfs in GLOBAL_MAP.items():
                theme_df = df_m[df_m['ETF'].isin(etfs)]
                if not theme_df.empty:
                    with st.expander(f"📂 {theme} Detay Grubu", expanded=False):
                        cols = st.columns(3)
                        for idx, row in theme_df.reset_index(drop=True).iterrows():
                            with cols[idx % 3]:
                                area_desc = ETF_INFO.get(row['ETF'], {}).get('area', '')
                                info_str = f"<span style='color:#888; font-size:0.75rem;'>- {area_desc}</span>" if area_desc else ""
                                draw_etf_battery(row['ETF'], row['RSI'], row['RSI_1D'], row['RSI_1W'], row['Renk'], row['Delta_Icon'], info_str)

# ---------------------------------------------------------
# TAB 3: KUŞBAKIŞI PARA AKIŞI LİSTESİ
# ---------------------------------------------------------
with tab3:
    st.subheader("🦅 Sektör & Alt Sektör Günlük Para Akışı Radar Tablosu")
    with st.spinner("Kuşbakışı Sektörler Taranıyor..."):
        df_bird = calculate_signals(all_etfs_to_scan, interval="1d", bypass_stamp=st.session_state.battery_nonce)
        if not df_bird.empty:
            df_bird['1 Gün (%)'] = pd.to_numeric(df_bird['1 Gün (%)'], errors='coerce')
            df_bird['1 Hafta (%)'] = pd.to_numeric(df_bird['1 Hafta (%)'], errors='coerce')
            df_bird['Kapsam'] = df_bird['Ticker'].map(etf_name_map)
            df_bird_disp = df_bird[['Kapsam', 'Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', '1 Hafta (%)', 'Whale Power']]
            st.dataframe(
                df_bird_disp.style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']).map(style_efor, subset=['Efor']),
                use_container_width=True, height=400, hide_index=True
            )
            
            st.divider()
            c_heat1, c_heat2 = st.columns(2)
            with c_heat1: st.markdown(render_heatmap(df_bird, '1 Gün (%)', "Günlük (1D) Isı Haritası"), unsafe_allow_html=True)
            with c_heat2: st.markdown(render_heatmap(df_bird, '1 Hafta (%)', "Haftalık (1W) Isı Haritası"), unsafe_allow_html=True)

    st.divider()
    selected_etf = st.selectbox("İçeriğini görmek istediğiniz tematik ETF'i seçin:", sorted(list(ETF_INFO.keys())))
    if selected_etf:
        etf_stocks = ETF_INFO[selected_etf]['stocks']
        with st.spinner(f"{selected_etf} bileşenleri taranıyor..."):
            df_etf_components = calculate_signals(etf_stocks, interval="1d", bypass_stamp=st.session_state.battery_nonce)
            if not df_etf_components.empty:
                st.dataframe(
                    df_etf_components[['Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', '1 Hafta (%)', 'Whale Power', 'Fusion']]
                    .style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']).map(style_efor, subset=['Efor']),
                    use_container_width=True, hide_index=True
                )

# ---------------------------------------------------------
# TAB 4: HAFTALIK MOMENTUM-GAP
# ---------------------------------------------------------
with tab4:
    st.subheader("🦈 Haftalık Momentum-Gap Avcısı (VCP & Lunge)")
    with st.spinner("1W Kinetik Boşluklar aranıyor..."):
        all_universe = list(set(all_etfs_to_scan + portfolio_tickers))
        df_wk = calculate_signals(all_universe, interval="1wk", bypass_stamp=st.session_state.battery_nonce)
        if not df_wk.empty:
            df_wk['Kapsam'] = df_wk['Ticker'].map(etf_name_map).fillna("Hisse (Portföy)")
            df_wk['Sort_Priority'] = df_wk['Sinyal'].apply(lambda x: 0 if 'GAP' in x else (1 if 'ACCUMULATION' in x else (2 if 'DEEP' in x else 3)))
            df_wk = df_wk.sort_values(by=['Sort_Priority', 'Fusion'], ascending=[True, False]).drop(columns=['Sort_Priority'])
            st.dataframe(
                df_wk[['Kapsam', 'Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', '1 Hafta (%)', 'Whale Power']]
                .style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']).map(style_efor, subset=['Efor']),
                use_container_width=True, height=600, hide_index=True
            )

# ---------------------------------------------------------
# TAB 5: 4H & OMNI RADAR
# ---------------------------------------------------------
with tab5:
    st.subheader("🌐 4H SEKTÖR & ALT SEKTÖR RADARI (WHALE & HOLE)")
    with st.spinner("Sektör ETF'leri 4H taranıyor..."):
        df_4h_etfs = calculate_signals(all_etfs_to_scan, interval="4h", bypass_stamp=st.session_state.battery_nonce)
        if not df_4h_etfs.empty:
            df_4h_etfs['Sektör Adı'] = df_4h_etfs['Ticker'].map(etf_name_map)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<h4 style='color: #00bcd4;'>🔄 4H Whale Re-Entry</h4>", unsafe_allow_html=True)
                st.dataframe(df_4h_etfs[df_4h_etfs['Sinyal'] == '🔄 WHALE RE-ENTRY'][['Sektör Adı', 'Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', 'Fusion']].style.map(style_signals, subset=['Sinyal']).map(style_efor, subset=['Efor']), use_container_width=True, hide_index=True)
            with c2:
                st.markdown("<h4 style='color: #9c27b0;'>🕳️ 4H Volatility Hole</h4>", unsafe_allow_html=True)
                st.dataframe(df_4h_etfs[df_4h_etfs['Sinyal'] == '🕳️ VOLA HOLE'][['Sektör Adı', 'Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', 'Fusion']].style.map(style_signals, subset=['Sinyal']).map(style_efor, subset=['Efor']), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🚨 OMNI RADAR: Tüm Hisseler Günlük Tarama")
    all_market_stocks = list(set([s for data in ETF_INFO.values() for s in data["stocks"]]))
    with st.spinner("Tüm piyasa günlük taranıyor..."):
        df_radar = calculate_signals(all_market_stocks, interval="1d", bypass_stamp=st.session_state.battery_nonce)
        if not df_radar.empty:
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("<h4 style='color: #00bcd4;'>🔄 Günlük Whale Re-Entry</h4>", unsafe_allow_html=True)
                st.dataframe(df_radar[df_radar['Sinyal'] == '🔄 WHALE RE-ENTRY'][['Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', 'Whale Power', 'Fusion']].style.map(style_signals, subset=['Sinyal']).map(style_efor, subset=['Efor']), use_container_width=True, hide_index=True)
            with col_r2:
                st.markdown("<h4 style='color: #9c27b0;'>🕳️ Günlük Volatility Hole</h4>", unsafe_allow_html=True)
                st.dataframe(df_radar[df_radar['Sinyal'] == '🕳️ VOLA HOLE'][['Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', 'Whale Power', 'Fusion']].style.map(style_signals, subset=['Sinyal']).map(style_efor, subset=['Efor']), use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# TAB 6: MÜKEMMEL PORTFÖY CONTROLS
# ---------------------------------------------------------
with tab6:
    st.subheader("📋 Genel Portföy & OMNI Radar İzleme Listesi (Fair Value Analizi)")
    with st.spinner("Portföy simülasyonu hesaplanıyor..."):
        df_port = calculate_signals(portfolio_tickers, interval="1d", bypass_stamp=st.session_state.battery_nonce)
        if not df_port.empty:
            df_port_final = pd.merge(df_port, df_alerts[['Ticker', 'Fair Value', 'Bilanço']], on="Ticker", how="left")
            st.dataframe(
                df_port_final[['Ticker', 'Sinyal', 'Efor', 'Fiyat', 'Fair Value', 'Bilanço', '1 Gün (%)', '1 Hafta (%)', 'Whale Power', 'Fusion']]
                .style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']).map(style_efor, subset=['Efor']),
                use_container_width=True, height=600, hide_index=True
            )

# ---------------------------------------------------------
# TAB 7: FUTURE THEMES
# ---------------------------------------------------------
with tab7:
    st.subheader("🚀 FUTURE THEMES: Geleceğin Teknolojileri & Chokepoint Şirketleri")
    future_ticker_to_cat = {t: cat for cat, tkrs in FUTURE_THEMES_MAP.items() for t in tkrs}
    with st.spinner("Future Themes evreni taranıyor..."):
        df_future = calculate_signals(list(future_ticker_to_cat.keys()), interval="1d", bypass_stamp=st.session_state.battery_nonce)
        if not df_future.empty:
            df_future['Tema / Katman'] = df_future['Ticker'].map(future_ticker_to_cat)
            df_future['Sort_Priority'] = df_future['Sinyal'].apply(lambda x: 0 if 'WHALE' in x else (1 if 'HYPER' in x else (2 if 'HOLE' in x else 3)))
            df_future = df_future.sort_values(by=['Sort_Priority', 'Fusion'], ascending=[True, False]).drop(columns=['Sort_Priority'])
            st.dataframe(
                df_future[['Tema / Katman', 'Ticker', 'Sinyal', 'Efor', 'Fiyat', '1 Gün (%)', '1 Hafta (%)', 'Whale Power', 'Fusion']]
                .style.map(style_signals, subset=['Sinyal']).map(style_percentages, subset=['1 Gün (%)', '1 Hafta (%)']).map(style_efor, subset=['Efor']),
                use_container_width=True, height=600, hide_index=True
            )
