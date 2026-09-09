import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import re

st.set_page_config(page_title="Mine KPI Dashboard", page_icon="⛏️", layout="wide")
st.title("⛏️ Mine KPI Dashboard - God Tier Auto")

def find_col(df, keywords):
    """Cari kolom yg mirip keyword, gak peduli gede kecil/spasi"""
    for col in df.columns:
        for key in keywords:
            if re.search(key, col, re.IGNORECASE):
                return col
    return None

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip() # hapus spasi depan belakang

    # Auto cari kolom penting
    col_map = {
        'Unit': find_col(df, ['UNIT NO', 'UNIT', 'NO UNIT']),
        'Owner': find_col(df, ['OWNER', 'UNIT OWNER', 'PIC']),
        'Type': find_col(df, ['TYPE', 'UNIT TYPE', 'JENIS']),
        'UA': find_col(df, ['UA', 'UA%']),
        'MA': find_col(df, ['MA', 'MA%']),
        'BD Hours': find_col(df, ['BD', 'BREAKDOWN', 'TOTAL BD']),
        'MTTR': find_col(df, ['MTTR']),
        'MTBF': find_col(df, ['MTBF']),
        'WH': find_col(df, ['WH', 'WORK HOURS']),
        'MOHH': find_col(df, ['MOHH']),
        'Repair Freq': find_col(df, ['REPAIR', 'REPAIR TOTAL'])
    }

    # Ubah jadi angka kalau ada
    for k, v in col_map.items():
        if v and v in df.columns:
            df[v] = pd.to_numeric(df[v], errors='coerce').fillna(0)

    return df, col_map

def color_bad(val, threshold=85):
    return 'background-color: #FF4B4B; color: white' if isinstance(val, (int,float)) and val < threshold else ''

with st.sidebar:
    st.header("📁 Upload Data")
    file = st.file_uploader("Upload Excel Data Mateng", type="xlsx")

if file:
    df, cols = load_data(file)

    if not cols['Owner'] or not cols['Unit']:
        st.error("❌ Kolom 'Owner' atau 'Unit' gak ketemu di Excel lu. Cek lagi nama kolomnya ya")
        st.stop()

    with st.sidebar:
        st.header("📅 Filter")
        list_owner = st.multiselect("Owner", df[cols['Owner']].unique(), default=df[cols['Owner']].unique())
        df_temp = df[df[cols['Owner']].isin(list_owner)]

        list_type = []
        if cols['Type']:
            list_type = st.multiselect("Type Unit", df_temp[cols['Type']].unique(), default=df_temp[cols['Type']].unique())
            df_temp = df_temp[df_temp[cols['Type']].isin(list_type)]

        list_unit = st.multiselect("Unit No", df_temp[cols['Unit']].unique(), default=df_temp[cols['Unit']].unique())

    df_f = df[
        (df[cols['Owner']].isin(list_owner)) &
        (df[cols['Unit']].isin(list_unit))
    ]
    if cols['Type'] and list_type:
        df_f = df_f[df_f[cols['Type']].isin(list_type)]

    # KPI
    c1, c2, c3, c4 = st.columns(4)
    if cols['UA']: c1.metric("Avg UA", f"{df_f[cols['UA']].mean():.2f}%")
    if cols['MA']: c2.metric("Avg MA", f"{df_f[cols['MA']].mean():.2f}%")
    if cols['BD Hours']: c3.metric("Total BD", f"{df_f[cols['BD Hours']].sum():.2f} jam")
    c4.metric("Total Unit", f"{df_f[cols['Unit']].nunique()}")

    # Tabel
    highlight_cols = [cols['UA'], cols['MA']]
    highlight_cols = [c for c in highlight_cols if c]
    st.dataframe(df_f.style.applymap(color_bad, subset=highlight_cols), use_container_width=True)

    st.download_button("📥 Download CSV", df_f.to_csv(index=False), "laporan_kpi.csv")

else:
    st.info("👆 Upload file Excel untuk mulai")
