import streamlit as st
import pandas as pd
import math

# --------------------------------------------------
# SAYFA AYARLARI
# --------------------------------------------------
st.set_page_config(
    page_title="Tahmin Doğruluğu Dashboard",
    layout="wide"
)

st.title("Tahmin Doğruluğu Dashboard")
st.caption("Siparişe Göre vs Sevke Göre")

# --------------------------------------------------
# DOSYA YÜKLEME
# --------------------------------------------------
uploaded_file = st.file_uploader(
    "Excel dosyasını yükle (.xlsx)",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Devam etmek için lütfen Excel dosyasını yükleyin.")
    st.stop()

# --------------------------------------------------
# GÜVENLİ TD FONKSİYONU (BULLET-PROOF)
# --------------------------------------------------
def td(actual, forecast):
    try:
        actual = float(actual)
        forecast = float(forecast)

        if math.isnan(actual) or math.isnan(forecast):
            return None
        if actual == 0 and forecast == 0:
            return None

        return min(actual, forecast) / max(actual, forecast)

    except Exception:
        return None

# --------------------------------------------------
# KOLON HARF TANIMLARI (GLOBAL)
# --------------------------------------------------
COL_AY = "A"
COL_KAPAK = "B"
COL_BAZ = "AI"          # <-- Baz (KI / ADT)
COL_MARKA = "AL"        # <-- Marka
COL_SATIS_ORG = "E"    # <-- Satış Organizasyonu

COL_TAHMIN = "O"
COL_SIPARIS = "N"
COL_SEVK = "T"

# --------------------------------------------------
# KATEGORİ BELİRLEME
# --------------------------------------------------
def kategori_belirle(row):
    baz = str(row[COL_BAZ]).strip()
    marka = str(row[COL_MARKA]).strip().upper()
    satis_org = row[COL_SATIS_ORG]

    if baz == "KI":
        if satis_org == 1000:
            return "Kağıt Yurtiçi"
        elif satis_org == 2000:
            return "Profesyonel Kağıt"
        else:
            return "Yurtdışı Kağıt"
    else:
        if marka in ["OKEY", "DETAN", "SELIN", "EGOS"]:
            return "KBEB"
        elif marka in ["JOHN FRIEDA", "FROSCH"]:
            return "Dağıtım"
        else:
            return "Bebek"

# --------------------------------------------------
# HEDEFLER
# --------------------------------------------------
HEDEFLER = {
    "Kağıt Yurtiçi": 0.75,
    "Profesyonel Kağıt": 0.70,
    "Yurtdışı Kağıt": 0.70,
    "Bebek": 0.70,
    "KBEB": 0.75,
    "Dağıtım": 0.75
}

# --------------------------------------------------
# ANA BLOK
# --------------------------------------------------
try:
    df = pd.read_excel(uploaded_file, header=None)

    # En az T sütunu olmalı
    if df.shape[1] < 21:
        st.error("Excel beklenen kolon sayısından az.")
        st.stop()

    # Kolonları A, B, C... yap
    df.columns = [chr(65 + i) for i in range(len(df.columns))]

    # KOLON TANIMLARI
    COL_AY = "A"
    COL_KAPAK = "B"
    COL_TAHMIN = "O"
    COL_SIPARIS = "N"
    COL_SEVK = "T"
    COL_BAZ = "AI"
    COL_MARKA = "AL"
    COL_SATIS_ORG = "E"
    
    # Sayıya zorlama (kritik)
    for col in [COL_TAHMIN, COL_SIPARIS, COL_SEVK]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --------------------------------------------------
    # AY SEÇİMİ
    # --------------------------------------------------
    st.subheader("Dönem Seçimi")
    
    # Ay kolonu güvenli hale getir
    df[COL_AY] = df[COL_AY].astype(str).str.strip()

    ay_listesi = sorted(
    [ay for ay in df[COL_AY].unique() if ay not in ["nan", "None", ""]]
    )

    if len(ay_listesi) == 0:
        st.error("Ay bilgisi bulunamadı. Lütfen Excel'de A sütununu kontrol edin.")
        st.stop()

    secili_ay = st.selectbox("Ay", ay_listesi)

    df = df[df[COL_AY] == secili_ay]


    # --------------------------------------------------
    # HESAPLAR
    # --------------------------------------------------
    df["TD_Siparis"] = df.apply(
        lambda x: td(x[COL_SIPARIS], x[COL_TAHMIN]), axis=1
    )
    df["TD_Sevk"] = df.apply(
        lambda x: td(x[COL_SEVK], x[COL_TAHMIN]), axis=1
    )

    df["Kategori"] = df.apply(kategori_belirle, axis=1)

    # --------------------------------------------------
    # KPI KARTLARI
    # --------------------------------------------------
    k1, k2 = st.columns(2)

    k1.metric(
        "Siparişe Göre Tahmin Doğruluğu",
        f"{df['TD_Siparis'].mean() * 100:.0f}%"
    )

    k2.metric(
        "Sevke Göre Tahmin Doğruluğu",
        f"{df['TD_Sevk'].mean() * 100:.0f}%"
    )

    # --------------------------------------------------
    # TOPLAM KATEGORİ ANALİZİ
    # --------------------------------------------------
    st.subheader(f"Toplam Kategori Analizi – {secili_ay}")

    ozet = (
        df.groupby("Kategori")
        .agg(
            Tahmin=(COL_TAHMIN, "sum"),
            Siparis=(COL_SIPARIS, "sum"),
            Sevk=(COL_SEVK, "sum"),
            TD_Sevk=("TD_Sevk", "mean"),
            TD_Siparis=("TD_Siparis", "mean")
        )
        .reset_index()
    )

    ozet["Hedef"] = ozet["Kategori"].map(HEDEFLER)
    ozet["Taraflılık"] = ozet["TD_Siparis"] - ozet["Hedef"]

    # --------------------------------------------------
    # RENKLENDİRME
    # --------------------------------------------------
    def renk_td(val, hedef):
        if pd.isna(val):
            return ""
        if val >= hedef:
            return "background-color: #e6f4ea; color: #137333"
        elif val >= hedef - 0.05:
            return "background-color: #fff4e5; color: #b45309"
        else:
            return "background-color: #fdecea; color: #b91c1c"

    styled = ozet.style.apply(
        lambda row: [
            "",
            "",
            "",
            "",
            renk_td(row["TD_Sevk"], row["Hedef"]),
            renk_td(row["TD_Siparis"], row["Hedef"]),
            "",
            ""
        ],
        axis=1
    ).format({
        "TD_Sevk": "{:.0%}",
        "TD_Siparis": "{:.0%}",
        "Hedef": "{:.0%}",
        "Taraflılık": "{:+.0%}"
    })

    st.dataframe(styled, use_container_width=True)

except Exception as e:
    st.error("Uygulama çalışırken hata oluştu:")
    st.exception(e)
