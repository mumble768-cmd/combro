import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(page_title="Mine KPI Dashboard", page_icon="⛏️", layout="wide")
st.title("⛏️ Mine KPI Dashboard - Auto Baca Excel")

st.markdown("Upload file Excel KPI lu. Otomatis jadi dashboard. Gak pake ribet")

def clean_col(name):
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, sheet_name=0) # ambil sheet pertama
    df.columns = df.columns.str.strip()

    # Auto convert kolom angka
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        except:
            pass
    df = df.dropna(how='all') # hapus baris kosong
    return df

def find_col(df, keys):
    for col in df.columns:
        c = clean_col(col)
        for k in keys:
            if k in c: return col
    return None

with st.sidebar:
    st.header("📁 1. Upload Data")
    file = st.file_uploader("Upload Excel KPI", type=["xlsx", "xls"])

if file:
    df, = load_data(file),

    st.success(f"✅ Data ke-load: {df.shape[0]} baris, {df.shape[1]} kolom")

    # AUTO DETEKSI KOLOM PENTING
    col_unit = find_col(df, ['unitno', 'unit', 'equipment'])
    col_owner = find_col(df, ['owner', 'pic', 'dept'])
    col_type = find_col(df, ['type', 'jenis', 'category'])
    col_ua = find_col(df, ['ua', 'availability'])
    col_ma = find_col(df, ['ma', 'mechanical'])
    col_bd = find_col(df, ['bd', 'breakdown', 'downtime'])
    col_mttr = find_col(df, ['mttr'])
    col_mtbf = find_col(df, ['mtbf'])

    # SIDEBAR FILTER OTOMATIS
    st.sidebar.header("📅 2. Filter")
    filters = {}
    for name, col in [('Owner', col_owner), ('Type', col_type), ('Unit', col_unit)]:
        if col:
            filters[name] = st.sidebar.multiselect(name, df[col].dropna().unique(), default=df[col].dropna().unique())

    df_f = df.copy()
    for name, col in [('Owner', col_owner), ('Type', col_type), ('Unit', col_unit)]:
        if col and name in filters:
            df_f = df_f[df_f[col].isin(filters[name])]

    # KPI CARDS OTOMATIS
    st.header("📊 KPI Utama")
    kpi_cols = st.columns(4)
    i = 0
    kpi_list = [('Avg UA', col_ua, '%'), ('Avg MA', col_ma, '%'), ('Total BD', col_bd, 'jam'), ('Total Unit', col_unit, '')]
    for label, col, unit in kpi_list:
        if col and col in df_f.columns:
            val = df_f[col].mean() if unit == '%' else df_f[col].sum() if label == 'Total BD' else df_f[col].nunique()
            kpi_cols[i%4].metric(label, f"{val:.2f}{unit}")
            i += 1

    # GRAFIK OTOMATIS TOP 10 BD
    if col_unit and col_bd:
        st.header("📉 Top 10 Unit Breakdown Tertinggi")
        top_bd = df_f.groupby(col_unit)[col_bd].sum().nlargest(10).reset_index()
        fig = px.bar(top_bd, x=col_unit, y=col_bd, text=col_bd, title="Top 10 BD Hours")
        st.plotly_chart(fig, use_container_width=True)

    # TABEL DENGAN HIGHLIGHT
    st.header("📋 Data Detail")
    def highlight(val):
        if isinstance(val, (int, float)) and val < 85 and ('ua' in str(val).lower() or 'ma' in str(val).lower()):
            return 'background-color: #FF4B4B; color: white'
        return ''

    st.dataframe(df_f, use_container_width=True)

    # DOWNLOAD
    st.download_button("📥 Download Hasil Filter", df_f.to_csv(index=False).encode('utf-8'), "laporan_filter.csv")

else:
    st.info("👆 Upload file Excel KPI lu di sidebar kiri")
    st.markdown("""
    **Fitur Auto:**
    1. Auto deteksi kolom Owner, Unit, Type, UA, MA, BD
    2. Filter otomatis muncul kalau kolomnya ada
    3. KPI Card otomatis kehitung
    4. Grafik Top 10 BD otomatis
    5. Tabel bisa di sort & download
    """)
