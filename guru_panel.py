import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. AYARLAR ---
st.set_page_config(page_title="GURU V3: ŞAHANE", layout="wide")

# --- 2. SEKTÖREL LİSTE (7 HİSSE) ---
sektorler = {
    "Havacılık": ["THYAO.IS", "PGSUS.IS", "TAVHL.IS", "DOCO.IS", "CLEBI.IS", "GSDHO.IS", "AYGAZ.IS"],
    "Bankacılık": ["ISCTR.IS", "AKBNK.IS", "GARAN.IS", "YKBNK.IS", "HALKB.IS", "VAKBN.IS", "TSKB.IS"],
    "Enerji": ["EUPWR.IS", "ASTOR.IS", "SMRTG.IS", "KONTR.IS", "ENJSA.IS", "ALARK.IS", "ODAS.IS"],
    "Perakende": ["BIMAS.IS", "MGROS.IS", "SOKM.IS", "AEFES.IS", "CCOLA.IS", "MAVI.IS", "VAKKO.IS"],
    "Otomotiv": ["FROTO.IS", "TOASO.IS", "DOAS.IS", "TTRAK.IS", "OTKAR.IS", "TMSN.IS", "ASUZU.IS"],
    "Sanayi": ["EREGL.IS", "KRDMD.IS", "SAHOL.IS", "KCHOL.IS", "SISE.IS", "TUPRS.IS", "ARCLK.IS"]
}

# --- 3. SIDEBAR: KOMUTA MERKEZİ ---
st.sidebar.title("🏹 ŞAHANE")
secilen_sektor = st.sidebar.selectbox("Sektör Seç", list(sektorler.keys()))
secilen_hisse = st.sidebar.selectbox("Hisse Seç", sektorler[secilen_sektor])

st.sidebar.divider()
use_manual = st.sidebar.toggle("MANUEL OVERRIDE")

if use_manual:
    m_price = st.sidebar.number_input("Güncel Fiyat", value=100.0)
    m_eps = st.sidebar.number_input("Hisse Başı Kar (EPS)", value=5.0)
    m_bvps = st.sidebar.number_input("Defter Değeri (BVPS)", value=40.0)
    m_fcf_ps = st.sidebar.number_input("Hisse Başı Nakit (FCF PS)", value=8.0)
    m_favok_ps = st.sidebar.number_input("Hisse Başı FAVÖK (EBITDA PS)", value=12.0)

# --- 4. VERİ ÇEKME ---
def get_full_info():
    try:
        t = yf.Ticker(secilen_hisse)
        i = t.info
        if use_manual:
            return m_price, m_eps, m_bvps, m_fcf_ps, m_favok_ps, 0, 0
        
        p = i.get('currentPrice', 0.01)
        eps = i.get('trailingEps', 0)
        bvps = i.get('bookValue', 0)
        fk = i.get('trailingPE', 0)
        pddd = i.get('priceToBook', 0)
        sh = i.get('sharesOutstanding', 1)
        fcf_ps = i.get('freeCashflow', 0) / sh if sh > 0 else 0
        fav_ps = i.get('ebitda', 0) / sh if sh > 0 else 0
        return p, eps, bvps, fcf_ps, fav_ps, fk, pddd
    except:
        return 0.01, 0, 0, 0, 0, 0, 0

p, eps, bvps, fcf_ps, fav_ps, fk, pddd = get_full_info()

# --- 5. HESAPLAMALAR ---
graham = np.sqrt(22.5 * eps * bvps) if (eps > 0 and bvps > 0) else 0
fcf_target = fcf_ps * 15
favok_target = fav_ps * 8
avg_fair = (graham + fcf_target + favok_target) / 3 if graham > 0 else (fcf_target + favok_target) / 2

# --- 6. EKRAN ÇIKTISI ---
st.title(f"📊 {secilen_hisse} Analiz Paneli")

# Mevcut Piyasa Verileri (Eksik kalan kısımlar)
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Güncel Fiyat", f"{p:.2f} TL")
col_b.metric("F/K Oranı", f"{fk:.2f}" if not use_manual else "MANUEL")
col_c.metric("PD/DD Oranı", f"{pddd:.2f}" if not use_manual else "MANUEL")
col_d.metric("EPS (Kâr)", f"{eps:.2f}")

st.divider()

# Değerleme Hedefleri
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("1. GRAHAM")
    st.title(f"{graham:.2f}")

with col2:
    st.subheader("2. FCF (15x)")
    st.title(f"{fcf_target:.2f}")

with col3:
    st.subheader("3. FD/FAVÖK (8x)")
    st.title(f"{favok_target:.2f}")

st.divider()

# Stratejik Sinyal (Sadece Sembol)
c1, c2 = st.columns(2)
with c1:
    st.subheader("ORTALAMA HEDEF")
    st.header(f"{avg_fair:.2f} TL")

with c2:
    st.subheader("SİNYAL")
    if p < avg_fair:
        st.title("✅")
    else:
        st.title("⛔")

st.caption("GURU V3 'ŞAHANE' - Graham, FCF ve FAVÖK temelli tam hesaplama.")
