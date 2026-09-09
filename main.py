import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Mine KPI Dashboard", layout="wide")
st.title("MINE KPI DASHBOARD - VERSI BARBAR")

@st.cache_data
def load_data(file):
    # Coba baca header di baris 0 sampe 5
    for i in range(6):
        try:
            df = pd.read_excel(file, header=i)
            if 'UNIT' in str(df.columns).upper():
                break
        except:
            continue

    df.columns = df.columns.str.strip()
    df = df.dropna(how='all')

    # Convert semua ke angka kalau bisa
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')

    # HITUNG KPI BARBAR
    try:
        if 'PA' not in df.columns:
            df['PA'] = (df['WH'] / df['MOHH']) * 100
    except: pass
    try:
        if 'UA' not in df.columns:
            df['UA'] = ((df['WH'] - df['TOTAL BD']) / df['WH']) * 100
    except: pass
    try:
        if 'MA' not in df.columns:
            df['MA'] = ((df['WH'] - df['TOTAL BD']) / df['WH']) * 100
    except: pass
    try:
        if 'MTTR' not in df.columns:
            df['MTTR'] = df['TOTAL BD'] / df['REPAIR TOTAL']
    except: pass
    try:
        if 'MTBF' not in df.columns:
            df['MTBF'] = df['WH'] / df['REPAIR TOTAL']
    except: pass

    return df

with st.sidebar:
    st.header("Upload")
    file = st.file_uploader("Upload Excel KPI", type=["xlsx"])

if file:
    df = load_data(file)
    st.success(f"Data ke-load: {df.shape[0]} baris, {df.shape[1]} kolom")

    st.header("SEMUA DATA")
    st.dataframe(df, use_container_width=True, height=600)

    st.header("KOLOM YANG TERDETEKSI")
    st.write(df.columns.tolist())

    st.download_button("Download CSV", df.to_csv(index=False), "Laporan.csv")

else:
    st.info("Upload file Excel lu")
