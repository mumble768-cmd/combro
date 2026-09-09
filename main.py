import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mine KPI Dashboard", page_icon="⛏️", layout="wide")
st.title("⛏️ MINE KPI DASHBOARD - PRO LEVEL")

@st.cache_data
def load_data(file):
    # Auto cari header
    df_raw = pd.read_excel(file, header=None)
    header_row = 0
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains('UNIT OWNER', case=False, na=False).any():
            header_row = i
            break

    df = pd.read_excel(file, header=header_row)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['UNIT NO']) # hapus baris kosong

    # Convert semua yg bisa jadi angka
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # HITUNG KPI OTOMATIS KALAU GAK ADA DI EXCEL
    if 'PA' not in df.columns and 'MOHH' in df.columns and 'WH' in df.columns:
        df['PA'] = (df['WH'] / df['MOHH']) * 100

    if 'UA' not in df.columns and 'WH' in df.columns and 'TOTAL BD' in df.columns:
        df['UA'] = ((df['WH'] - df['TOTAL BD']) / df['WH']) * 100

    if 'MA' not in df.columns and 'WH' in df.columns and 'TOTAL BD' in df.columns:
        df['MA'] = ((df['WH'] - df['TOTAL BD']) / df['WH']) * 100 # Rumus umum MA

    if 'MTTR' not in df.columns and 'TOTAL BD' in df.columns and 'REPAIR TOTAL' in df.columns:
        df['MTTR'] = df['TOTAL BD'] / df['REPAIR TOTAL']

    if 'MTBF' not in df.columns and 'WH' in df.columns and 'REPAIR TOTAL' in df.columns:
        df['MTBF'] = df['WH'] / df['REPAIR TOTAL']

    return df

with st.sidebar:
    st.header("📁 Upload")
    file = st.file_uploader("Upload Excel KPI", type=["xlsx"])

if file:
    df = load_data(file)
    st.success(f"✅ Data ke-load: {df.shape[0]} Unit")

    # FILTER
    st.sidebar.header("📅 Filter")
    owners = st.sidebar.multiselect("Owner", df['UNIT OWNER'].unique(), default=df['UNIT OWNER'].unique())
    types = st.sidebar.multiselect("Type", df['UNIT TYPE'].unique(), default=df['UNIT TYPE'].unique())
    units = st.sidebar.multiselect("Unit No", df['UNIT NO'].unique(), default=df['UNIT NO'].unique())

    df_f = df[
        (df['UNIT OWNER'].isin(owners)) &
        (df['UNIT TYPE'].isin(types)) &
        (df['UNIT NO'].isin(units))
    ]

    # KPI CARDS DEWA
    st.header("📊 KPI RINGKASAN")
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Rata2 PA", f"{df_f['PA'].mean():.2f}%" if 'PA' in df_f else "-")
    k2.metric("Rata2 MA", f"{df_f['MA'].mean():.2f}%" if 'MA' in df_f else "-")
    k3.metric("Rata2 UA", f"{df_f['UA'].mean():.2f}%" if 'UA' in df_f else "-")
    k4.metric("Total BD", f"{df_f['TOTAL BD'].sum():.1f} jam" if 'TOTAL BD' in df_f else "-")
    k5.metric("Total MOHH", f"{df_f['MOHH'].sum():.0f} jam" if 'MOHH' in df_f else "-")

    # TABEL INTERAKTIF DEWA
    st.header("📋 TABEL KPI DETAIL")

    # Kolom yg mau ditampilin
    show_cols = ['UNIT OWNER', 'UNIT NO', 'UNIT TYPE', 'PA', 'MA', 'UA', 'MOHH', 'WH', 'TOTAL BD', 'MTTR', 'MTBF']
    show_cols = [c for c in show_cols if c in df_f.columns] # cuma tampil yg ada

    def color_bad(val):
        if isinstance(val, (int, float)):
            if val < 80: return 'background-color: #FF4B4B; color: white' # Merah
            if val < 90: return 'background-color: #FFA500; color: white' # Kuning
        return ''

    st.dataframe(
        df_f[show_cols].style.format("{:.2f}").applymap(color_bad, subset=['PA','MA','UA']),
        use_container_width=True,
        height=500
    )

    # GRAFIK
    st.header("📉 Grafik")
    tab1, tab2 = st.tabs(["Top 10 BD", "UA vs MA"])
    with tab1:
        top_bd = df_f.nlargest(10, 'TOTAL BD')[['UNIT NO', 'TOTAL BD']]
        fig1 = px.bar(top_bd, x='UNIT NO', y='TOTAL BD', text='TOTAL BD')
        st.plotly_chart(fig1, use_container_width=True)
    with tab2:
        fig2 = px.scatter(df_f, x='UA', y='MA', hover_data=['UNIT NO'], title="UA vs MA")
        st.plotly_chart(fig2, use_container_width=True)

    st.download_button("📥 Download Laporan", df_f[show_cols].to_csv(index=False), "Laporan_KPI.csv")

else:
    st.info("👆 Upload file Excel KPI lu di sidebar")
