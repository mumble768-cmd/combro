import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mine KPI Dashboard", layout="wide")
st.title("MINE KPI DASHBOARD")

st.sidebar.header("1. Upload File Excel")
file = st.file_uploader("Upload file KPI", type=["xlsx"])

if file:
    df = pd.read_excel(file, header=0)
    df.columns = df.columns.str.strip()
    df = df.dropna(how='all')

    st.success(f"Berhasil load: {df.shape[0]} baris")

    st.sidebar.header("2. Pilih Kolom KPI")
    cols = df.columns.tolist()

    col_pa = st.sidebar.selectbox("Pilih Kolom PA", ["-"] + cols)
    col_ma = st.sidebar.selectbox("Pilih Kolom MA", ["-"] + cols)
    col_ua = st.sidebar.selectbox("Pilih Kolom UA", ["-"] + cols)
    col_mohh = st.sidebar.selectbox("Pilih Kolom MOHH", ["-"] + cols)
    col_wh = st.sidebar.selectbox("Pilih Kolom WH", ["-"] + cols)
    col_bd = st.sidebar.selectbox("Pilih Kolom BD/Downtime", ["-"] + cols)

    # Convert ke angka + AUTO KALIKAN 100 KALAU KOLOM PERSEN
    persen_cols = [col_pa, col_ma, col_ua]
    for c in [col_pa, col_ma, col_ua, col_mohh, col_wh, col_bd]:
        if c!= "-":
            df[c] = pd.to_numeric(df[c], errors='coerce')
            # Kalau namanya ada PA/MA/UA atau nilainya < 2, berarti desimal. Kalikan 100
            if c in persen_cols and df[c].max() < 2:
                df[c] = df[c] * 100

    st.header("3. TABEL DATA")
    show_cols = [c for c in [col_pa, col_ma, col_ua, col_mohh, col_wh, col_bd] if c!= "-"]

    if show_cols:
        # FORMAT JADI 2 DESIMAL + % BUAT PA MA UA
        format_dict = {}
        for c in persen_cols:
            if c in show_cols: format_dict[c] = "{:.2f}%"
        for c in [col_mohh, col_wh, col_bd]:
            if c in show_cols: format_dict[c] = "{:.1f}"

        st.dataframe(df[show_cols].style.format(format_dict), use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    st.header("4. RINGKASAN")
    k1,k2,k3 = st.columns(3)
    if col_pa!= "-": k1.metric("Rata2 PA", f"{df[col_pa].mean():.2f}%")
    if col_ma!= "-": k2.metric("Rata2 MA", f"{df[col_ma].mean():.2f}%")
    if col_ua!= "-": k3.metric("Rata2 UA", f"{df[col_ua].mean():.2f}%")

else:
    st.info("Silahkan upload file Excel KPI di sidebar")
