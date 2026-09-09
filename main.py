import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mine KPI Dashboard", page_icon="⛏️", layout="wide")
st.title("⛏️ Mine KPI Dashboard - Auto Header")

@st.cache_data
def load_data(file):
    # Baca dulu tanpa header buat cari baris header
    df_raw = pd.read_excel(file, header=None)

    # Cari baris yg ada kata "UNIT OWNER"
    header_row = 0
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains('UNIT OWNER', case=False, na=False).any():
            header_row = i
            break

    # Baca ulang pake header yg bener
    df = pd.read_excel(file, header=header_row)
    df.columns = df.columns.str.strip()
    df = df.dropna(how='all') # hapus baris kosong

    # Convert angka
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')

    return df

with st.sidebar:
    st.header("📁 Upload Data")
    file = st.file_uploader("Upload Excel KPI", type=["xlsx", "xls"])

if file:
    df = load_data(file)
    st.success(f"✅ Data ke-load: {df.shape[0]} baris, {df.shape[1]} kolom")

    # SIDEBAR FILTER
    st.sidebar.header("📅 Filter")
    col_owner = 'UNIT OWNER' if 'UNIT OWNER' in df.columns else df.columns[0]
    col_unit = 'UNIT NO' if 'UNIT NO' in df.columns else df.columns[1]
    col_type = 'UNIT TYPE' if 'UNIT TYPE' in df.columns else None
    col_ua = [c for c in df.columns if 'UA' in c.upper()]
    col_ma = [c for c in df.columns if 'MA' in c.upper()]
    col_bd = [c for c in df.columns if 'BD' in c.upper()]

    list_owner = st.sidebar.multiselect("Owner", df[col_owner].unique(), default=df[col_owner].unique())
    df_f = df[df[col_owner].isin(list_owner)]

    if col_type:
        list_type = st.sidebar.multiselect("Type", df_f[col_type].unique(), default=df_f[col_type].unique())
        df_f = df_f[df_f[col_type].isin(list_type)]

    list_unit = st.sidebar.multiselect("Unit", df_f[col_unit].unique(), default=df_f[col_unit].unique())
    df_f = df_f[df_f[col_unit].isin(list_unit)]

    # KPI
    st.header("📊 KPI Utama")
    c1, c2, c3, c4 = st.columns(4)
    if col_ua: c1.metric("Avg UA", f"{df_f[col_ua[0]].mean():.2f}%")
    if col_ma: c2.metric("Avg MA", f"{df_f[col_ma[0]].mean():.2f}%")
    if col_bd: c3.metric("Total BD", f"{df_f[col_bd[0]].sum():.2f} jam")
    c4.metric("Total Unit", f"{df_f[col_unit].nunique()}")

    # GRAFIK
    if col_bd:
        st.header("📉 Top 10 Unit Breakdown Tertinggi")
        top_bd = df_f.groupby(col_unit)[col_bd[0]].sum().nlargest(10).reset_index()
        fig = px.bar(top_bd, x=col_unit, y=col_bd[0], text=col_bd[0])
        st.plotly_chart(fig, use_container_width=True)

    # TABEL
    st.header("📋 Data Detail")
    st.dataframe(df_f, use_container_width=True)
    st.download_button("📥 Download CSV", df_f.to_csv(index=False), "laporan.csv")

else:
    st.info("👆 Upload file Excel KPI lu")
