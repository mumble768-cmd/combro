import streamlit as st
import pandas as pd

st.set_page_config(page_title="Mine KPI Dashboard", layout="wide")
st.title("MINE KPI DASHBOARD")

st.sidebar.header("1. Upload File Excel")
file = st.file_uploader("Upload file KPI", type=["xlsx"])

if file:
    df = pd.read_excel(file, header=0, dtype=str) # BACA DULU JADI TEKS SEMUA
    df.columns = df.columns.str.strip()
    df = df.dropna(how='all')

    st.success(f"Berhasil load: {df.shape[0]} baris")

    st.sidebar.header("2. Pilih Kolom KPI")
    cols = df.columns.tolist()

    col_pa = st.sidebar.selectbox("Pilih Kolom PA%", ["-"] + cols)
    col_ma = st.sidebar.selectbox("Pilih Kolom MA%", ["-"] + cols)
    col_ua = st.sidebar.selectbox("Pilih Kolom UA%", ["-"] + cols)
    col_plan = st.sidebar.selectbox("Pilih Kolom PLAN PA%", ["-"] + cols)

    # FUNGSI BUAT BERSIHIN KOMA + %
    def clean_number(col):
        if col == "-": return None
        return pd.to_numeric(df[col].astype(str).str.replace('%','').str.replace(',','.'), errors='coerce')

    df['PA_clean'] = clean_number(col_pa)
    df['MA_clean'] = clean_number(col_ma)
    df['UA_clean'] = clean_number(col_ua)
    df['PLAN_clean'] = clean_number(col_plan)

    st.header("3. TABEL DATA")
    show_cols = []
    format_dict = {}

    if col_pa!= "-":
        show_cols.append('PA_clean')
        format_dict['PA_clean'] = "{:.2f}%"
    if col_ma!= "-":
        show_cols.append('MA_clean')
        format_dict['MA_clean'] = "{:.2f}%"
    if col_ua!= "-":
        show_cols.append('UA_clean')
        format_dict['UA_clean'] = "{:.2f}%"
    if col_plan!= "-":
        show_cols.append('PLAN_clean')
        format_dict['PLAN_clean'] = "{:.2f}%"

    if show_cols:
        st.dataframe(df[show_cols].rename(columns={
            'PA_clean':'PA%', 'MA_clean':'MA%', 'UA_clean':'UA%', 'PLAN_clean':'PLAN PA%'
        }).style.format(format_dict), use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    st.header("4. RINGKASAN")
    k1,k2,k3,k4 = st.columns(4)
    if col_pa!= "-": k1.metric("Rata2 PA", f"{df['PA_clean'].mean():.2f}%")
    if col_ma!= "-": k2.metric("Rata2 MA", f"{df['MA_clean'].mean():.2f}%")
    if col_ua!= "-": k3.metric("Rata2 UA", f"{df['UA_clean'].mean():.2f}%")
    if col_plan!= "-": k4.metric("Rata2 PLAN PA", f"{df['PLAN_clean'].mean():.2f}%")

else:
    st.info("Silahkan upload file Excel KPI di sidebar")
