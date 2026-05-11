import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import graphviz
import random
from datetime import datetime

# ==========================================
# 0. AYARLAR & CSS (DARK MODE & KONTRAST)
# ==========================================
st.set_page_config(layout="wide", page_title="AETHER QUANTUM FUSION V127", page_icon="🏛️")

st.markdown("""
    <style>
    .stApp { background-color: #050505 !important; color: #e0e0e0 !important; }
    [data-testid="stTable"], [data-testid="stDataFrame"] { background-color: #111111 !important; color: #e0e0e0 !important; }
    th { background-color: #222222 !important; color: #00ff88 !important; border-bottom: 1px solid #444 !important; }
    td { border-bottom: 1px solid #333 !important; }
    div.stButton > button { background-color: #222222 !important; color: #ffffff !important; border: 1px solid #444 !important; }
    div.stButton > button:hover { border-color: #00ff88 !important; color: #00ff88 !important; }
    .news-box { background-color: #111; border-left: 4px solid; padding: 15px; margin: 10px 0; border-radius: 4px; }
    .news-pos { border-left-color: #00ff88; color: #e0e0e0; }
    .news-neg { border-left-color: #ff3333; color: #e0e0e0; }
    .news-neu { border-left-color: #f1c40f; color: #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

if 'macro_state' not in st.session_state: st.session_state.macro_state = "neutral"
if 'macro_impact' not in st.session_state: st.session_state.macro_impact = "neutral"
if 'active_asset' not in st.session_state: st.session_state.active_asset = None

# ==========================================
# 1. VERİ HARİTASI & HABER KÜTÜPHANESİ
# ==========================================
ASSET_GROUPS = ["Hisse Senedi", "Tahvil", "Emtia", "Kripto", "Forex", "Gayrimenkul"]

MACRO_INFO = {
    "LEADING": {
        "score": 75, "color": "#00ff88", "impact": "positive",
        "desc": "Öncü Göstergeler: Ekonominin gelecekteki yönünü (3-6 ay) tahmin eder. İmalat siparişleri ve tüketici güvenini kapsar.",
        "news": "Küresel tedarik zinciri verileri ve yeni imalat siparişleri son çeyrekte %4.2 oranında beklenmedik bir artış gösterdi. Bu durum, önümüzdeki altı ay için sanayi üretiminde güçlü bir toparlanmaya ve risk iştahının artmasına işaret ediyor."
    },
    "COINCIDENT": {
        "score": 45, "color": "#ff3333", "impact": "negative",
        "desc": "Eşzamanlı Göstergeler: Ekonominin anlık durumunu gösterir. Mevcut GSYİH, sanayi üretimi ve perakende satışları yansıtır.",
        "news": "Artan kredi faizleri ve daralan hanehalkı bütçeleri nedeniyle perakende satış verilerinde belirgin bir yavaşlama kaydedildi. Tüketici harcamalarındaki bu reel düşüş, anlık ekonomik aktivitenin baskı altında olduğunu doğruluyor."
    },
    "LAGGING": {
        "score": 55, "color": "#f1c40f", "impact": "neutral",
        "desc": "Gecikmeli Göstergeler: Ekonomik trendlerin teyidi için kullanılır. İşsizlik oranları ve enflasyon verilerini içerir.",
        "news": "Geçmiş döneme ait çekirdek enflasyon verileri ve işgücü piyasası raporları, merkez bankasının sıkılaşma politikalarının gecikmeli etkilerini dengeli bir şekilde yansıtmaya başladı."
    }
}

SECTORS_INFO = {
    "Teknoloji & Yapay Zeka": {
        "tickers": ["NVDA", "AVGO", "MSFT", "AMD", "SMCI"],
        "news": "Yapay zeka altyapısına ve veri merkezlerine yönelik artan donanım talebi, lider çip üreticilerinin önümüzdeki iki çeyrek için gelir beklentilerini yukarı yönlü revize etmesine neden oldu. Ancak tedarik zinciri kısıtlamaları bazı alt üreticilerde gecikmelere yol açıyor.",
        "trend": "Pozitif"
    },
    "Enerji & Altyapı": {
        "tickers": ["SMR", "CEG", "VST", "XOM", "CVX"],
        "news": "Veri merkezlerinin yarattığı devasa elektrik ihtiyacını karşılamak için yeni nesil nükleer reaktör projelerine sağlanan teşvikler onaylandı. Fosil yakıt talebinde ise jeopolitik arz endişelerine rağmen kısmi bir durgunluk gözlemleniyor.",
        "trend": "Pozitif"
    },
    "Savunma & Uzay": {
        "tickers": ["RTX", "LMT", "RKLB", "SPCE", "KTOS"],
        "news": "Küresel savunma bütçelerindeki artışlar ve yeni nesil uydu ağlarına yapılan yatırımlar hız kazandı. Büyük ihalelerin dağıtımı, özellikle uzay taşımacılığı yapan şirketlerin sipariş defterlerini tarihi zirvelere taşıdı.",
        "trend": "Nötr"
    },
    "Finans & Ödeme Sist.": {
        "tickers": ["JPM", "GS", "PYPL", "MA", "SQ"],
        "news": "Geleneksel bankacılık sektörü yüksek faiz ortamında kar marjlarını korumaya çalışırken, tüketici kredilerindeki temerrüt oranlarının hafifçe artması bölgesel bankalar üzerinde baskı yaratmaya başladı.",
        "trend": "Negatif"
    }
}

# ==========================================
# 2. QUANTUM ENGINE (V127.0 - 3 Mum Kuralı Yok)
# ==========================================
def calculate_signals(ticker_list):
    results = []
    for t in ticker_list:
        price = np.random.uniform(15, 800)
        fusion_score = random.randint(1, 5)
        whale_pwr = random.uniform(20, 95)
        is_bull_trap = random.choice([True, False]) if whale_pwr < 40 else False
        
        if is_bull_trap: signal = "SELL ⛔"
        elif fusion_score >= 4: signal = "BUY ✅"
        elif whale_pwr > 70: signal = "BUY ✅"
        else: signal = "WAIT ⚪"
        
        results.append({
            "Hisse": t,
            "Sinyal": signal,
            "Fiyat": f"${price:.2f}",
            "Whale Power": f"%{whale_pwr:.1f}",
            "Fusion": f"{fusion_score}/5"
        })
    return pd.DataFrame(results)

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
    
    # Kök Düğüm (Makro Durum)
    dot.node("MACRO", "🌍 MAKRO GÜÇ", shape='ellipse', style='filled', fillcolor='#222', fontcolor='white', color=link_color, penwidth='3')

    # Varlık Sınıfları Düğümleri
    for i in range(0, len(ASSET_GROUPS), 3):
        with dot.subgraph() as s:
            s.attr(rank='same')
            for asset in ASSET_GROUPS[i:i+3]:
                fill = '#333333' if asset == st.session_state.active_asset else '#111111'
                dot.node(asset, asset, shape='box', style='filled,rounded', fillcolor=fill, fontcolor='white', color='#444')
                # Makrodan varlıklara bağlantı ve üzerine etki yazısı
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

st.write("**Detaylı tarama için ağ üzerinden etkilenen varlık sınıfını seçin:**")
asset_cols = st.columns(3)
for i, asset in enumerate(ASSET_GROUPS):
    with asset_cols[i % 3]:
        if st.button(asset, use_container_width=True):
            st.session_state.active_asset = asset
            st.rerun()

# --- SEKTÖR VE HİSSE TARAMASI (YENİ DATAFRAME ON_SELECT YAPISI) ---
if st.session_state.active_asset == "Hisse Senedi":
    st.divider()
    st.subheader("📊 Sektör Bazlı Radar Taraması")
    st.caption("Ayrıntılı haberleri ve hisse listesini görmek için aşağıdaki tablodan bir sektöre tıklayın.")

    # Sektörleri DataFrame'e dönüştür
    sec_df_data = []
    for sec_name, sec_data in SECTORS_INFO.items():
        sec_df_data.append({
            "Sektör": sec_name,
            "Genel Trend": sec_data["trend"],
            "İzlenen Hisse Sayısı": len(sec_data["tickers"])
        })
    df_sectors = pd.DataFrame(sec_df_data)

    def color_trend(val):
        if val == 'Pozitif': return 'color: #00ff88; font-weight: bold;'
        elif val == 'Negatif': return 'color: #ff3333; font-weight: bold;'
        return 'color: #f1c40f; font-weight: bold;'

    # Interactive DataFrame
    sec_selection = st.dataframe(
        df_sectors.style.map(color_trend, subset=['Genel Trend']),
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="sector_table",
        hide_index=True
    )

    # Bir Sektör Seçildiğinde...
    if sec_selection.selection.rows:
        selected_row_idx = sec_selection.selection.rows[0]
        selected_sector_name = df_sectors.iloc[selected_row_idx]["Sektör"]
        sec_details = SECTORS_INFO[selected_sector_name]

        st.success(f"🎯 **Odaklanılan Sektör:** {selected_sector_name}")
        
        # Kesintisiz Tam Cümle Sektör Haberi
        trend_class = "news-pos" if sec_details['trend'] == "Pozitif" else "news-neg" if sec_details['trend'] == "Negatif" else "news-neu"
        st.markdown(f"""
            <div class="news-box {trend_class}">
                <strong>Sektörel Dinamikleri Değiştiren Son Gelişmeler:</strong><br>
                {sec_details['news']}
            </div>
        """, unsafe_allow_html=True)

        # Seçili Sektörün Hisselerini Hesapla ve Göster
        st.write(f"**{selected_sector_name} İçindeki Aktif Sinyaller:**")
        df_sector_stocks = calculate_signals(sec_details['tickers'])
        
        def color_signals(val):
            if 'BUY' in val: return 'background-color: #004400; color: #00ff88;'
            elif 'SELL' in val: return 'background-color: #440000; color: #ff3333;'
            return 'background-color: #222; color: white;'
            
        st.dataframe(
            df_sector_stocks.style.map(color_signals, subset=['Sinyal']),
            use_container_width=True,
            hide_index=True
        )

# --- PORTFÖY BÖLÜMÜ ---
st.divider()
st.subheader("📋 Genel Portföy (Tüm İzleme Listesi)")
raw_tickers = ["NVDA", "AMD", "TSM", "ASML", "AVGO", "ARM", "AXTI", "SMCI", "AI", "GOOG", "META", "IONQ", "NBIS", "ADBE", "DT", "S", "EXTR", "OUST", "ONDS", "RKLB", "SIDU", "SPIR", "BKSY", "SATL", "SPCE", "RTX", "KTOS", "SMR", "NNE", "CEG", "TLN", "BKR", "ASTI", "IREN", "WULF", "SLNH", "HIMS", "TDOC", "OSCR", "AMGN", "PFE", "GMAB", "CLPT", "IINN", "QCLS", "PYPL", "MA", "PGY", "OPEN", "CRML", "ATLX", "BMNR", "STLA", "CARR", "CPRT", "GRAB", "SFM", "HITI", "TRUG", "SBET", "T", "P", "SILJ", "PPLT", "PALL", "COPX", "GDXJ", "UFO", "BULL", "CRM", "SNOW", "NOW", "LMT", "CIFR", "VST", "DGXX"]
portfolio_tickers = sorted(list(set(raw_tickers)))

df_port_full = calculate_signals(portfolio_tickers)

def style_full_port(val):
    if isinstance(val, str):
        if 'BUY' in val: return 'color: #00ff88; font-weight: bold;'
        if 'SELL' in val: return 'color: #ff3333; font-weight: bold;'
    return ''

st.dataframe(
    df_port_full.style.map(style_full_port, subset=['Sinyal']),
    use_container_width=True, height=400, hide_index=True
)
