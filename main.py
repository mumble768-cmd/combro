import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Mine KPI Dashboard", page_icon="⛏️", layout="wide")
st.title("⛏️ MINE KPI DASHBOARD - GOD TIER")

@st.cache_data
def load_data(file):
    df_raw = pd.read_excel(file, header=None)
    header_row = 0
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains('UNIT OWNER', case=False, na=False).any():
            header_row = i
            break

    df = pd.read_excel(file, header=header_row)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['UNIT NO'])

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Auto hitung KPI biar lengkap
    if 'PA' not in df.columns and 'MOHH' in df.columns and 'WH' in df.columns:
        df['PA'] = np.where(df['MOHH']>0, (df['WH'] / df['MOHH']) * 100, 0)
    if 'UA' not in df.columns and 'WH' in df.columns and 'TOTAL BD' in df.columns:
        df['UA'] = np.where(df['WH']>0, ((df['WH'] - df['TOTAL BD']) / df['WH']) * 100, 0)
    if 'MA' not in df.columns and 'WH' in df.columns and 'TOTAL BD' in df.columns:
        df['MA'] = np.where(df['WH']>0, ((df['WH'] - df['TOTAL BD']) / df['WH']) * 100, 0)
    if 'MTTR' not in df.columns and 'TOTAL BD' in df.columns and 'REPAIR TOTAL' in df.columns:
        df['MTTR'] = np.where(df['REPAIR TOTAL']>0, df['TOTAL BD'] / df['REPAIR TOTAL'], 0)
    if 'MTBF' not in df.columns and 'WH' in df.columns and 'REPAIR TOTAL' in df.columns:
        df['MTBF'] = np.where(df['REPAIR TOTAL']>0, df['WH'] / df['REPAIR TOTAL'], 0)
    return df

with st.sidebar:
    st.header("📁 Upload")
    file = st.file_uploader("Upload Excel KPI", type=["xlsx"])

if file:
    df = load_data(file)
    st.success(f"✅ Data ke-load: {df.shape[0]} Unit")

    st.sidebar.header("📅 Filter")
    owners = st.sidebar.multiselect("Owner", df['UNIT OWNER'].dropna().unique().tolist(), default=df['UNIT OWNER'].dropna().unique().tolist())
    types = st.sidebar.multiselect("Type", df['UNIT TYPE'].dropna().unique().tolist(), default=df['UNIT TYPE'].dropna().unique().tolist())
    units = st.sidebar.multiselect("Unit No", df['UNIT NO'].dropna().unique().tolist(), default=df['UNIT NO'].dropna().unique().tolist())

    df_f = df[
        (df['UNIT OWNER'].isin(owners)) &
        (df['UNIT TYPE'].isin(types)) &
        (df['UNIT NO'].isin(units))
    ]

    st.header("📊 KPI RINGKASAN")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Rata2 PA", f"{df_f['PA'].mean():.2f}%" if 'PA' in df_f else "-")
    k2.metric("Rata2 MA", f"{df_f['MA'].mean():.2f}%" if 'MA' in df_f else "-")
    k3.metric("Rata2 UA", f"{df_f['UA'].mean():.2f}%" if 'UA' in df_f else "-")
    k4.metric("Total BD", f"{df_f['TOTAL BD'].sum():.1f} jam" if 'TOTAL BD' in df_f else "-")
    k5.metric("Total MOHH", f"{df_f['MOHH'].sum():.0f} jam" if 'MOHH' in df_f else "-")

    st.header("📋 TABEL KPI DETAIL")
    show_cols = ['UNIT OWNER', 'UNIT NO', 'UNIT TYPE', 'PA', 'MA', 'UA', 'MOHH', 'WH', 'TOTAL BD', 'MTTR', 'MTBF']
    show_cols = [c for c in show_cols if c in df_f.columns]

    def color_bad(val):
        if isinstance(val, (int, float)) and not pd.isna(val):
            if val < 80: return 'background-color: #FF4B4B; color: white'
            if val < 90: return 'background-color: #FFA500; color: white'
        return ''

    # UDAH DIBENERIN PAKE.map()
    st.dataframe(df_f[show_cols].style.format("{:.2f}").map(color_bad, subset=[c for c in ['PA','MA','UA'] if c in show_cols]), use_container_width=True, height=500)

    st.download_button("📥 Download Laporan", df_f[show_cols].to_csv(index=False), "Laporan_KPI.csv")

else:
    st.info("👆 Upload file Excel KPI lu di sidebar")
