import pandas as pd
import plotly.express as px
import numpy as np
import re

st.set_page_config(page_title="Mine KPI Dashboard", page_icon="⛏️", layout="wide")
st.title("⛏️ MINE KPI DASHBOARD - AUTO DETECT")

def find_col(df, keywords):
    for col in df.columns:
        c = re.sub(r'[^a-z0-9]', '', str(col).lower())
        for k in keywords:
            if k in c: return col
    return None

@st.cache_data
def load_data(file):
    df_raw = pd.read_excel(file, header=None)
    header_row = 0
    for i, row in df_raw.iterrows():
        if row.astype(str).str.contains('UNIT', case=False, na=False).any():
            header_row = i
            break

    df = pd.read_excel(file, header=header_row)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=[df.columns[1]]) # hapus baris kosong

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # AUTO CARI NAMA KOLOM
    col_owner = find_col(df, ['unitowner', 'owner'])
    col_unit = find_col(df, ['unitno', 'unit'])
    col_type = find_col(df, ['unittype', 'type'])
    col_mohh = find_col(df, ['mohh', 'scheduled'])
    col_wh = find_col(df, ['wh', 'workhour'])
    col_bd = find_col(df, ['bd', 'breakdown', 'downtime'])
    col_repair = find_col(df, ['repair', 'totalrepair'])

    col_pa = find_col(df, ['pa'])
    col_ma = find_col(df, ['ma'])
    col_ua = find_col(df, ['ua'])

    # HITUNG KPI KALAU GAK ADA
    if col_pa is None and col_wh and col_mohh:
        df['PA'] = np.where(df[col_mohh]>0, (df[col_wh] / df[col_mohh]) * 100, 0)
        col_pa = 'PA'
    if col_ua is None and col_wh and col_bd:
        df['UA'] = np.where(df[col_wh]>0, ((df[col_wh] - df[col_bd]) / df[col_wh]) * 100, 0)
        col_ua = 'UA'
    if col_ma is None and col_wh and col_bd:
        df['MA'] = np.where(df[col_wh]>0, ((df[col_wh] - df[col_bd]) / df[col_wh]) * 100, 0)
        col_ma = 'MA'
    if 'MTTR' not in df.columns and col_bd and col_repair:
        df['MTTR'] = np.where(df[col_repair]>0, df[col_bd] / df[col_repair], 0)
    if 'MTBF' not in df.columns and col_wh and col_repair:
        df['MTBF'] = np.where(df[col_repair]>0, df[col_wh] / df[col_repair], 0)

    return df, col_owner, col_unit, col_type, col_pa, col_ma, col_ua, col_mohh, col_wh, col_bd

with st.sidebar:
    st.header("📁 Upload")
    file = st.file_uploader("Upload Excel KPI", type=["xlsx"])

if file:
    df, col_owner, col_unit, col_type, col_pa, col_ma, col_ua, col_mohh, col_wh, col_bd = load_data(file)
    st.success(f"✅ Data ke-load: {df.shape[0]} Unit")

    st.sidebar.header("📅 Filter")
    owners = st.sidebar.multiselect("Owner", df[col_owner].dropna().unique().tolist(), default=df[col_owner].dropna().unique().tolist())
    types = st.sidebar.multiselect("Type", df[col_type].dropna().unique().tolist(), default=df[col_type].dropna().unique().tolist())
    units = st.sidebar.multiselect("Unit No", df[col_unit].dropna().unique().tolist(), default=df[col_unit].dropna().unique().tolist())

    df_f = df[
        (df[col_owner].isin(owners)) &
        (df[col_type].isin(types)) &
        (df[col_unit].isin(units))
    ]

    st.header("📊 KPI RINGKASAN")
    k1, k2, k3, k4, k5 = st.columns(5)
    if col_pa: k1.metric("Rata2 PA", f"{df_f[col_pa].mean():.2f}%")
    if col_ma: k2.metric("Rata2 MA", f"{df_f[col_ma].mean():.2f}%")
    if col_ua: k3.metric("Rata2 UA", f"{df_f[col_ua].mean():.2f}%")
    if col_bd: k4.metric("Total BD", f"{df_f[col_bd].sum():.1f} jam")
    if col_mohh: k5.metric("Total MOHH", f"{df_f[col_mohh].sum():.0f} jam")

    st.header("📋 TABEL KPI DETAIL")
    show_cols = [col_owner, col_unit, col_type, col_pa, col_ma, col_ua, col_mohh, col_wh, col_bd, 'MTTR', 'MTBF']
    show_cols = [c for c in show_cols if c and c in df_f.columns]

    def color_bad(val):
        if isinstance(val, (int, float)) and not pd.isna(val):
            if val < 80: return 'background-color: #FF4B4B; color: white'
            if val < 90: return 'background-color: #FFA500; color: white'
        return ''

    st.dataframe(df_f[show_cols].style.format("{:.2f}").map(color_bad, subset=[c for c in [col_pa,col_ma,col_ua] if c]), use_container_width=True, height=500)

else:
    st.info("👆 Upload file Excel KPI lu di sidebar")
