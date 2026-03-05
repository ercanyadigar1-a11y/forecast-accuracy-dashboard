import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Tahmin Doğruluğu Sonuçları",
    layout="wide"
)

st.title("Tahmin Doğruluğu Sonuçları")
st.caption("Siparişe Göre vs Sevke Göre")

uploaded_file = st.file_uploader(
    "Excel dosyasını yükle (.xlsx)",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Devam etmek için lütfen Excel dosyasını yükleyin.")
    st.stop()

try:
    df = pd.read_excel(uploaded_file, header=None)

    if df.shape[1] < 21:
        st.error("Excel beklenen kolon sayısından az. Lütfen doğru dosyayı yükleyin.")
        st.stop()

    df.columns = [chr(65 + i) for i in range(len(df.columns))]

    COL_KAPAK = "B"
    COL_TAHMIN = "O"
    COL_SIPARIS = "N"
    COL_SEVK = "T"

    def td(actual, forecast):
        if pd.isna(actual) or pd.isna(forecast):
            return None
        if actual == 0 and forecast == 0:
            return None
        return min(actual, forecast) / max(actual, forecast)

    df["TD_Siparis"] = df.apply(
        lambda x: td(x[COL_SIPARIS], x[COL_TAHMIN]), axis=1
    )
    df["TD_Sevk"] = df.apply(
        lambda x: td(x[COL_SEVK], x[COL_TAHMIN]), axis=1
    )

    c1, c2 = st.columns(2)
    c1.metric(
        "Siparişe Göre Tahmin Doğruluğu",
        f"{df['TD_Siparis'].mean()*100:.1f}%"
    )
    c2.metric(
        "Sevke Göre Tahmin Doğruluğu",
        f"{df['TD_Sevk'].mean()*100:.1f}%"
    )

    st.subheader("Kapak Bölüm Bazlı Sonuçlar")

    table = (
        df.groupby(COL_KAPAK)[["TD_Siparis", "TD_Sevk"]]
        .mean()
        .reset_index()
    )

    table["Sipariş TD %"] = table["TD_Siparis"] * 100
    table["Sevk TD %"] = table["TD_Sevk"] * 100

    st.dataframe(
        table[[COL_KAPAK, "Sipariş TD %", "Sevk TD %"]],
        use_container_width=True
    )

except Exception as e:
    st.error("Uygulama çalışırken hata oluştu:")
    st.exception(e)
