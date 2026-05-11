import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import graphviz
import random
from datetime import datetime

# ==========================================
# 0. AYARLAR & CSS (DARK MODE & KONTRAST)
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION V127.2", page_icon="🏛️")

st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; color: #e0e0e0 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; }
    div.stButton > button { background-color: #222222 !important; color: #ffffff !important; border: 1px solid #444 !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    .news-box { background-color: #111; border-left: 4px solid; padding: 15px; margin: 10px 0; border-radius: 4px; line-height: 1.5; }
    .news-pos { border-left-color: #00ff88; color: #e0e0e0; }
    .news-neg { border-left-color: #ff3333; color: #e0e0e0; }
    .news-neu { border-left-color: #f1c40f; color: #e0e0e0; }
    .fv-up { color: #00ff88; font-weight: bold; font-size: 1.2rem; }
    .fv-down { color: #ff3333; font-weight: bold; font-size: 1.2rem; }
    </style>
""", unsafe_allow_html=True)

# Oturum Değişkenleri
if 'macro_state' not in st.session_state: st.session_state.macro_state = "neutral"
if 'macro_impact' not in st.session_state: st.session_state.macro_impact = "neutral"
if 'active_asset' not in st.session_state: st.session_state.active_asset = None
if 'active_sector' not in st.session_state: st.session_state.active_sector = None

# ==========================================
# 1. VERİ HARİTASI & KÜTÜPHANELER
# ==========================================
ASSET_GROUPS = ["Hisse Senedi", "Tahvil", "Emtia", "Kripto", "Forex", "Gayrimenkul"]

MACRO_INFO = {
    "LEADING": {
        "score": 75, "color": "#00ff88", "impact": "positive",
        "desc": "Öncü Göstergeler (3-6 Aylık Projeksiyon)",
        "news": "Küresel tedarik zinciri verileri ve yeni imalat siparişleri son çeyrekte %4.2 oranında beklenmedik bir artış gösterdi. Bu durum, önümüzdeki altı ay için sanayi üretiminde güçlü bir toparlanmaya ve piyasalarda risk iştahının artmasına işaret ediyor."
    },
    "COINCIDENT": {
        "score": 45, "color": "#ff3333", "impact": "negative",
        "desc": "Eşzamanlı Göstergeler (Anlık Durum)",
        "news": "Artan kredi faizleri ve daralan hanehalkı bütçeleri nedeniyle perakende satış verilerinde belirgin bir yavaşlama kaydedildi. Tüketici harcamalarındaki bu reel düşüş, anlık ekonomik aktivitenin ciddi bir baskı altında olduğunu doğruluyor."
    },
    "LAGGING": {
        "score": 55, "color": "#f1c40f", "impact": "neutral",
        "desc": "Gecikmeli Göstergeler (Trend Teyidi)",
        "news": "Geçmiş döneme ait çekirdek enflasyon verileri ve işgücü piyasası raporları, merkez bankasının sıkılaşma politikalarının gecikmeli etkilerini dengeli bir şekilde yansıtmaya başladı. Şu an için piyasada yön tayini konusunda bekle-gör politikası hakim."
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
    "Temel Tüketim (XLP)": ["MOO", "PBJ"],
    "Kamu (XLU)": ["PHO"]
}

ETF_INFO = {
    "SMH": {"area": "Yarı İletken Devleri & Çip Üretimi", "stocks": ["NVDA", "TSM", "AVGO", "ASML", "AMD", "MU", "INTC", "KLAC", "LRCX", "ADI"]},
    "SOXX": {"area": "Global Çip Ekosistemi & Tasarım", "stocks": ["NVDA", "AVGO", "AMD", "TXN", "MU", "INTC", "AMAT", "QCOM", "ADI", "MCHP"]},
    "BOTZ": {"area": "Robotik Sistemler & Endüstriyel AI", "stocks": ["ISRG", "NVDA", "ABB", "KEYENCE", "FANUC", "TER", "YASKAWA", "PATH", "OMRON"]},
    "CIBR": {"area": "Siber Güvenlik & Veri Koruma Ağları", "stocks": ["PANW", "CRWD", "FTNT", "NET", "ZS", "OKTA", "CHKP", "AKAM"]},
    "IGV": {"area": "Bulut Yazılım & Kurumsal SaaS", "stocks": ["ADBE", "CRM", "INTU", "ORCL", "MSFT", "NOW", "SNOW", "MDB"]},
    "ARKF": {"area": "Finansal Teknoloji & Dijital Ödemeler", "stocks": ["COIN", "SHOP", "SQ", "MELI", "HOOD", "DKNG", "TOAST", "PYPL"]},
    "ITA": {"area": "Havacılık, Savunma & Ulusal Güvenlik", "stocks": ["RTX", "LMT", "BA", "GD", "NOC", "TDG", "HWM", "LHX", "TXT"]},
    "XAR": {"area": "Gelişmiş Uzay Teknolojileri & Donanım", "stocks": ["GE", "TDG", "HWM", "LMT", "RTX", "AXON", "NOC", "RKLB", "BKS"]},
    "IYT": {"area": "Ulaşım, Lojistik & Kargo Taşımacılığı", "stocks": ["UNP", "UPS", "UBER", "FDX", "CSX", "NSC", "ODFL", "DAL", "EXPD"]},
    "PAVE": {"area": "Altyapı, İnşaat & Endüstriyel Üretim", "stocks": ["TRNE", "ETN", "URI", "DE", "CAT", "VMC", "MLM", "EMR"]},
    "JETS": {"area": "Hava Yolu Taşımacılığı & Global Operatörler", "stocks": ["DAL", "UAL", "AAL", "LUV", "ALGT", "ALK", "JBLU", "SAVE"]},
    "XOP": {"area": "Petrol & Doğalgaz Arama/Çıkarma", "stocks": ["XOM", "CVX", "COP", "EOG", "PXD", "HES", "DVN", "OXY", "MRO"]},
    "OIH": {"area": "Petrol Servisleri & Sondaj Ekipmanları", "stocks": ["SLB", "HAL", "BKR", "FTI", "VLO", "MPC", "PSX", "HP"]},
    "URA": {"area": "Nükleer Enerji & Uranyum Madenciliği", "stocks": ["CCJ", "KAP", "UUUU", "NLR", "BWXT", "DNN", "NXE", "UEC"]},
    "ICLN": {"area": "Temiz Enerji & Karbonsuz Dönüşüm", "stocks": ["BE", "FSLR", "ENPH", "VWS", "ORSTED", "NEE", "EDPR", "PLUG", "DQ"]},
    "TAN": {"area": "Güneş Enerjisi & Panel Üretimi", "stocks": ["FSLR", "ENPH", "NXT", "SEDG", "RUN", "TPW", "SHLS", "SPWR"]},
    "LIT": {"area": "Lityum Döngüsü & Batarya Teknolojileri", "stocks": ["ALB", "SQM", "BYD", "TSLA", "CATL", "ALTM", "LAC", "PIL", "PMG"]},
    "XME": {"area": "Metaller, Madencilik & Çelik Sanayi", "stocks": ["FCX", "NUE", "STLD", "AA", "CLF", "RS", "MP"]},
    "GDX": {"area": "Altın Madencileri & Değerli Metaller", "stocks": ["NEM", "GOLD", "AEM", "WPM", "KGC", "PAAS"]},
    "REMX": {"area": "Nadir Toprak Elementleri & Stratejik Metaller", "stocks": ["ALB", "MP", "Lynas", "Ganfeng", "Tianqi"]},
    "XBI": {"area": "Biyoteknoloji & Genetik Araştırmalar", "stocks": ["MRNA", "VRTX", "AMGN", "GILD", "BIIB", "REGN", "SGEN", "BNTX"]},
    "IHI": {"area": "Tıbbi Cihazlar & Cerrahi Teknolojiler", "stocks": ["ABT", "MDT", "ISRG", "SYK", "BSX", "EW", "DXCM", "ZBH"]},
    "ARKG": {"area": "Genomik Devrim & Yaşam Bilimleri", "stocks": ["EXAS", "CRSP", "PACB", "NTLA", "EDIT", "NVTA", "BEAM"]},
    "BETZ": {"area": "Online Bahis & iGaming Teknolojileri", "stocks": ["DKNG", "FLUT", "EVO", "PENN", "MGM", "CZR", "WYNN", "GENI"]},
    "XRT": {"area": "Perakende Ticaret & Tüketici Harcamaları", "stocks": ["CVNA", "ANF", "AMZN", "COST", "WMT", "TGT", "TJX", "DLTR"]},
    "XHB": {"area": "Konut İnşaatı & Ev Geliştirme", "stocks": ["LEN", "DHI", "PHM", "LOW", "HD", "NVR", "TOL"]},
    "IBUY": {"area": "E-Ticaret & Dijital Pazaryerleri", "stocks": ["AMZN", "EBAY", "ETSY", "CHWY", "MELI", "QRTEA", "JD"]},
    "KRE": {"area": "ABD Bölgesel Bankacılık Sistemi", "stocks": ["NYCB", "WAL", "ZION", "CMA", "TFC", "HBAN", "RF", "FITB"]},
    "KIE": {"area": "Sigortacılık & Risk Yönetimi", "stocks": ["CB", "PGR", "ALL", "TRV", "MET", "PRU", "AFL"]},
    "IAI": {"area": "Yatırım Bankacılığı & Aracı Kurumlar", "stocks": ["MS", "GS", "IBKR", "SCHW", "RJF", "LPLA"]},
    "SOCL": {"area": "Sosyal Medya & İletişim Ağları", "stocks": ["META", "GOOGL", "Tencent", "SNAP", "PINS", "GRVY", "BIDU", "SPOT"]},
    "HERO": {"area": "Video Oyunları & Dijital Eğlence", "stocks": ["NVDA", "NTDOY", "SE", "EA", "TTWO", "RBLX", "U", "UBSFY"]},
    "SRVR": {"area": "Veri Merkezleri & Altyapı GYO", "stocks": ["EQIX", "AMT", "DLR", "CCI", "SBAC", "UNIT"]},
    "PHO": {"area": "Su Teknolojileri & Arıtma Sistemleri", "stocks": ["AWK", "XYL", "WTS", "AWR", "SBS", "TTEK"]},
    "MOO": {"area": "Tarım Teknolojileri & Gıda Üretimi", "stocks": ["DE", "ZTS", "TSCO", "CTVA", "ADM", "NTR", "FMC"]},
    "PBJ": {"area": "Temel Tüketim & Hazır Gıda", "stocks": ["MDLZ", "PEP", "KO", "KHC", "GIS", "HSY", "TSN"]}
}

# ==========================================
# 2. QUANTUM ENGINE (V127.0 - Simülasyon Motoru)
# ==========================================
def calculate_signals(ticker_list):
    results = []
    for t in ticker_list:
        price = np.random.uniform(15, 800)
        fusion_score = random.randint(1, 5)
        whale_pwr = random.uniform(20, 95)
        is_bull_trap = random.choice([True, False]) if whale_pwr < 40 else False
        
        if is_bull_trap: signal = "⛔ TRAP"
        elif fusion_score >= 4: signal = "💎 ANY BUY"
        elif whale_pwr > 75: signal = "🐋 WHALE IN"
        elif fusion_score >= 2: signal = "✅ BUY"
        else: signal = "⏳ WAIT"
        
        results.append({
            "Ticker": t,
            "Sinyal": signal,
            "Fiyat": f"${price:.2f}",
            "Whale Power": float(f"{whale_pwr:.1f}"),
            "Fusion": fusion_score
        })
    return pd.DataFrame(results).sort_values(by="Fusion", ascending=False)

# Haber Üretici Motor (Alanına göre mantıklı tam cümleler kurar)
def generate_news(area_name, is_positive):
    if is_positive:
        return f"🟢 {area_name} alanında tedarik zincirindeki rahatlama ve artan küresel talep, şirketlerin kar marjlarını tarihi zirvelere taşıdı. Gelen yeni büyük ölçekli siparişler, önümüzdeki iki çeyrek için büyüme beklentilerini garanti altına alıyor."
    else:
        return f"🔴 {area_name} sektöründe artan regülasyon baskıları ve hammadde maliyetlerindeki ani yükseliş, operasyonel karlılığı ciddi şekilde tehdit ediyor. Birçok şirket bu belirsizlik ortamında yatırımlarını askıya alma kararı aldı."

# ==========================================
# 3. GÖRSEL BİLEŞENLER
# ==========================================
def draw_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = value, 
        title = {'text': title, 'font': {'size': 14, 'color': 'white'}},
        number = {'font': {'color': 'white'}},
        gauge = {'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"}, 
                 'bar': {'color': color}, 'bgcolor': "#111111", 
                 'steps': [{'range': [0, 50], 'color': '#222222'}, {'range': [50, 100], 'color': '#333333'}]}
    ))
    fig.update_layout(height=180, margin=dict(l=10, r=10, t=30, b=10), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def draw_neuro_links():
    dot = graphviz.Digraph()
    dot.attr(bgcolor='#050505', rankdir='TB', size='10,6')
    
    impact = st.session_state.macro_impact
    link_color = "#00ff88" if impact == "positive" else "#ff3333" if impact == "negative" else "#f1c40f"
    edge_label = "POZİTİF ETKİ" if impact == "positive" else "NEGATİF ETKİ" if impact == "negative" else "NÖTR ETKİ"
    
    dot.node("MACRO", "🌍 MAKRO GÜÇ", shape='ellipse', style='filled', fillcolor='#222', fontcolor='white', color=link_color, penwidth='3')

    for i in range(0, len(ASSET_GROUPS), 3):
        with dot.subgraph() as s:
            s.attr(rank='same')
            for asset in ASSET_GROUPS[i:i+3]:
                fill = '#333333' if asset == st.session_state.active_asset else '#111111'
                dot.node(asset, asset, shape='box', style='filled,rounded', fillcolor=fill, fontcolor='white', color='#444')
                dot.edge("MACRO", asset, label=f" {edge_label} ", color=link_color, fontcolor=link_color, style='bold', fontsize='10')

    st.graphviz_chart(dot)

# ==========================================
# 4. ANA KOKPİT EKRANI
# ==========================================
st.title("🏛️ AETHER MACRO SYSTEM")

# --- MAKRO PANELLER ---
col1, col2, col3 = st.columns(3)

for i, (name, data) in enumerate(MACRO_INFO.items()):
    with [col1, col2, col3][i]:
        st.plotly_chart(draw_gauge(data['score'], name, data['color']), use_container_width=True)
        st.caption(data['desc'])
        
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button(f"🔗 Ağı Tetikle", key=f"net_{name}"):
            st.session_state.macro_state = name
            st.session_state.macro_impact = data['impact']
            st.session_state.active_asset = None
            st.session_state.active_sector = None
            st.rerun()
            
        if btn_c2.button(f"📰 Haber Detayı", key=f"news_{name}"):
            st.session_state.show_news_for = name
            st.rerun()

# Makro Haber Gösterimi
if 'show_news_for' in st.session_state and st.session_state.show_news_for in MACRO_INFO:
    sel_macro = MACRO_INFO[st.session_state.show_news_for]
    box_class = "news-pos" if sel_macro['impact'] == "positive" else "news-neg" if sel_macro['impact'] == "negative" else "news-neu"
    icon = "🟢" if sel_macro['impact'] == "positive" else "🔴" if sel_macro['impact'] == "negative" else "🟡"
    
    st.markdown(f"""
        <div class="news-box {box_class}">
            <strong>{icon} {st.session_state.show_news_for} Sinyalini Değiştiren Son Gelişme:</strong><br>
            {sel_macro['news']}
        </div>
    """, unsafe_allow_html=True)

# --- NÖRO AĞ BÖLÜMÜ ---
st.divider()
st.subheader("🔗 Varlık Nöro-Ağı Etkileşimi")
draw_neuro_links()

st.write("**Ağı yönlendirmek için etkilenecek varlık sınıfını seçin:**")
asset_cols = st.columns(3)
for i, asset in enumerate(ASSET_GROUPS):
    with asset_cols[i % 3]:
        if st.button(asset, use_container_width=True):
            st.session_state.active_asset = asset
            st.session_state.active_sector = None
            st.rerun()

# --- SEKTÖR VE ETF TARAMASI ---
if st.session_state.active_asset == "Hisse Senedi":
    st.divider()
    st.subheader("📊 Sektör Bazlı Radar Taraması (GLOBAL_MAP)")
    st.caption("Detayları görüntülemek için bir sektöre tıklayın.")
    
    # 1. Sektör Butonları (GLOBAL_MAP Keys)
    sec_cols = st.columns(4)
    for i, sector_name in enumerate(GLOBAL_MAP.keys()):
        with sec_cols[i % 4]:
            if st.button(sector_name, use_container_width=True):
                st.session_state.active_sector = sector_name
                st.rerun()

    # 2. Seçilen Sektörün ETF'leri
    if st.session_state.active_sector:
        st.divider()
        st.subheader(f"🎯 Odak: {st.session_state.active_sector}")
        st.write("Ayrıntılı haber ve içerik için **tablodaki bir ETF satırına tıklayın**.")
        
        etf_list = GLOBAL_MAP[st.session_state.active_sector]
        df_etfs = calculate_signals(etf_list)
        
        def color_signals(val):
            if 'ANY BUY' in val: return 'background-color: #004d40; color: white;'
            if 'WHALE' in val: return 'background-color: #01579b; color: white;'
            if 'TRAP' in val: return 'background-color: #4a148c; color: white;'
            if 'BUY' in val: return 'background-color: #1b5e20; color: white;'
            return 'background-color: #222; color: white;'

        # Etkileşimli Tablo (on_select)
        selection_event = st.dataframe(
            df_etfs.style.map(color_signals, subset=['Sinyal']),
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
            key="etf_table",
            hide_index=True
        )

        # 3. ETF Tıklandığında Açılan Detay Paneli (ETF_INFO)
        if selection_event.selection.rows:
            selected_idx = selection_event.selection.rows[0]
            selected_ticker = df_etfs.iloc[selected_idx]['Ticker']
            
            # Eğer ETF kütüphanede yoksa varsayılan döndür
            info = ETF_INFO.get(selected_ticker, {"area": "Sektörel Genel Endeks", "stocks": ["Sepet Verisi Mevcut Değil"]})
            
            st.success(f"🔍 **{selected_ticker} Analiz Paneli**")
            st.info(f"🌐 **Odak Alanı:** {info['area']}")
            
            # Fair Value ve Haber Simülasyonu
            fv = np.random.uniform(50, 400)
            prev_fv = fv + np.random.uniform(-20, 20)
            fv_class = "fv-up" if fv > prev_fv else "fv-down"
            arrow = "⬆️" if fv > prev_fv else "⬇️"
            st.markdown(f"**Güncel Fair Value:** <span class='{fv_class}'>${fv:.2f} {arrow}</span> (Önceki: ${prev_fv:.2f})", unsafe_allow_html=True)
            
            # Kesintisiz Tam Cümle Haberler
            is_pos = (df_etfs.iloc[selected_idx]['Fusion'] >= 3)
            box_class = "news-pos" if is_pos else "news-neg"
            st.markdown(f"""
                <div class="news-box {box_class}">
                    <strong>Son Çeyrek Etki Haberi:</strong><br>
                    {generate_news(info['area'], is_pos)}
                </div>
            """, unsafe_allow_html=True)
            
            st.write("**Bileşen Balinalar (Top Holdings):**")
            cols = st.columns(5)
            for i, stock in enumerate(info['stocks']):
                cols[i % 5].write(f"• {stock}")

# --- PORTFÖY BÖLÜMÜ (DEV LİSTE) ---
st.divider()
st.subheader("📋 Genel Portföy (Tüm İzleme Listesi)")
raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]
portfolio_tickers = sorted(list(set(raw_tickers)))

df_port_full = calculate_signals(portfolio_tickers)

def style_full_port(val):
    if isinstance(val, str):
        if 'BUY' in val: return 'color: #00ff88; font-weight: bold;'
        if 'SELL' in val or 'TRAP' in val: return 'color: #ff3333; font-weight: bold;'
    return ''

st.dataframe(
    df_port_full.style.map(style_full_port, subset=['Sinyal']),
    use_container_width=True, height=400, hide_index=True
)
