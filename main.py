import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Mine Planner", page_icon="⛏️", layout="wide")
st.title("⛏️ Mine Planner God-Tier Dashboard")

with st.sidebar:
    st.header("📁 Data Input")
    
file_bd = st.file_uploader("1. Upload Daily BD Excel", type="xlsx", key='bd')
file_oh = st.file_uploader("2. Upload Timesheet Excel", type="xlsx", key='oh')

# ==================== DEBUG DAILY BD ====================
st.subheader("🔍 Setup Daily BD")
df_bd = pd.DataFrame()
if file_bd:
    xls_bd = pd.ExcelFile(file_bd)
    c1, c2 = st.columns(2)
    sheet_bd = c1.selectbox("Pilih Sheet BD", xls_bd.sheet_names, key='bd_sheet')
    df_preview_bd = pd.read_excel(file_bd, sheet_name=sheet_bd, header=None, nrows=10)
    st.write("10 Baris Pertama Daily BD:")
    st.dataframe(df_preview_bd)
    header_bd = c2.number_input("Header BD di baris ke?", min_value=0, max_value=9, value=9, help="0 = baris pertama", key='bd_h')
    
    if st.button("✅ Load Daily BD"):
        df_bd = pd.read_excel(file_bd, sheet_name=sheet_bd, header=header_bd)
        df_bd.columns = df_bd.columns.str.strip().str.upper()
        
        col_map_bd = {
            'UNIT NO':'Unit', 'UNIT':'Unit', 'NO UNIT':'Unit',
            'TOTAL BD':'Downtime', 'BD':'Downtime', 'JAM BD':'Downtime',
            'COMPONEN':'Komponen', 'COMPONENT':'Komponen', 'KOMPONEN':'Komponen',
            'DATE IN':'DateIn', 'TGL MASUK':'DateIn', 'TANGGAL MASUK':'DateIn',
            'TIME IN':'TimeIn', 'JAM MASUK':'TimeIn',
            'DATE OUT':'DateOut', 'TGL KELUAR':'DateOut', 'TANGGAL KELUAR':'DateOut',
            'TIME OUT':'TimeOut', 'JAM KELUAR':'TimeOut'
        }
        df_bd = df_bd.rename(columns=col_map_bd)
        
        wajib = ['DateIn', 'TimeIn', 'DateOut', 'TimeOut', 'Unit', 'Downtime']
        hilang = [k for k in wajib if k not in df_bd.columns]
        if hilang:
            st.error(f"Kolom wajib BD nggak ada: {hilang}")
            st.write("Kolom yg kebaca:", list(df_bd.columns))
        else:
            df_bd['Start Job'] = pd.to_datetime(df_bd['DateIn'].astype(str) + ' ' + df_bd['TimeIn'].astype(str), dayfirst=True, errors='coerce')
            df_bd['Finish Job'] = pd.to_datetime(df_bd['DateOut'].astype(str) + ' ' + df_bd['TimeOut'].astype(str), dayfirst=True, errors='coerce')
            df_bd['Downtime'] = pd.to_numeric(df_bd['Downtime'], errors='coerce').fillna(0)
            df_bd = df_bd.dropna(subset=['Unit', 'Start Job'])
            st.session_state['df_bd'] = df_bd
            st.success(f"Daily BD OK! {len(df_bd)} baris loaded")

st.divider()

# ==================== DEBUG TIMESHEET ====================
st.subheader("🔍 Setup Timesheet")
df_oh = pd.DataFrame()
if file_oh:
    xls_oh = pd.ExcelFile(file_oh)
    c1, c2 = st.columns(2)
    sheet_oh = c1.selectbox("Pilih Sheet Timesheet", xls_oh.sheet_names, key='oh_sheet')
    df_preview_oh = pd.read_excel(file_oh, sheet_name=sheet_oh, header=None, nrows=10)
    st.write("10 Baris Pertama Timesheet:")
    st.dataframe(df_preview_oh)
    header_oh = c2.number_input("Header Timesheet di baris ke?", min_value=0, max_value=9, value=4, help="0 = baris pertama", key='oh_h')
    
    if st.button("✅ Load Timesheet"):
        df_oh = pd.read_excel(file_oh, sheet_name=sheet_oh, header=header_oh)
        df_oh.columns = df_oh.columns.str.strip().str.upper()
        
        col_map_oh = {
            'DATE':'Tanggal', 'TANGGAL':'Tanggal',
            'NO UNIT':'Unit', 'UNIT NO':'Unit', 'UNIT':'Unit',
            'TOTAL':'Operating Hours', 'TOTAL HM':'Operating Hours', 'HM':'Operating Hours', 'OH':'Operating Hours',
            'MOH':'Calendar Hours', 'CH':'Calendar Hours', 'CALENDAR':'Calendar Hours', 'MIN CH':'Calendar Hours'
        }
        df_oh = df_oh.rename(columns=col_map_oh)
        
        if 'Calendar Hours' not in df_oh.columns:
            df_oh['Calendar Hours'] = 24
            st.info("Kolom 'Calendar Hours' ga ada, otomatis diisi 24 jam/hari")
        
        wajib = ['Tanggal', 'Unit', 'Operating Hours']
        hilang = [k for k in wajib if k not in df_oh.columns]
        if hilang:
            st.error(f"Kolom wajib Timesheet nggak ada: {hilang}")
            st.write("Kolom yg kebaca:", list(df_oh.columns))
        else:
            df_oh = df_oh.dropna(subset=['Tanggal', 'Unit'])
            df_oh['Tanggal'] = pd.to_datetime(df_oh['Tanggal'], dayfirst=True, errors='coerce')
            df_oh['Operating Hours'] = pd.to_numeric(df_oh['Operating Hours'], errors='coerce').fillna(0)
            df_oh['Calendar Hours'] = pd.to_numeric(df_oh['Calendar Hours'], errors='coerce').fillna(24)
            st.session_state['df_oh'] = df_oh
            st.success(f"Timesheet OK! {len(df_oh)} baris loaded")

# ==================== DASHBOARD UTAMA ====================
df_bd = st.session_state.get('df_bd', pd.DataFrame())
df_oh = st.session_state.get('df_oh', pd.DataFrame())

st.divider()

if not df_bd.empty and not df_oh.empty:
    with st.sidebar:
        st.header("📅 Filter Periode")
        df_oh['Periode'] = df_oh['Tanggal'].dt.to_period('M')
        list_periode = sorted(df_oh['Periode'].unique().astype(str), reverse=True)
        periode_pilih = st.selectbox("Pilih Bulan", list_periode)
        df_oh_f = df_oh[df_oh['Periode'].astype(str) == periode_pilih]
        df_bd_f = df_bd[df_bd['Start Job'].dt.to_period('M').astype(str) == periode_pilih]

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 KPI", "🛢️ Lube", "🔧 Mechanic", "📈 Trend", "📋 Data", "📝 PICA"])

    with tab1:
        st.subheader(f"KPI Bulan: {periode_pilih}")
        oh = df_oh_f['Operating Hours'].sum()
        ch = df_oh_f['Calendar Hours'].sum()
        bh = df_bd_f['Downtime'].sum()
        freq_bd = len(df_bd_f)
        mar = oh/ch*100 if ch>0 else 0
        mttr = bh/freq_bd if freq_bd>0 else 0
        mtbf = oh/freq_bd if freq_bd>0 else 0
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("MAR", f"{mar:.1f}%")
        c2.metric("MTTR", f"{mttr:.1f} jam")
        c3.metric("MTBF", f"{mtbf:.1f} jam")
        c4.metric("Total BD", f"{freq_bd} kali")
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Operating Hours", f"{oh:,.1f} jam")
        c2.metric("Calendar Hours", f"{ch:,.1f} jam")
        c3.metric("Breakdown Hours", f"{bh:,.1f} jam")

    with tab2:
        st.subheader("🛢️ Lube Consumption")
        st.info("Tempel code Lube lu disini. Data: `df_oh_f`")
        st.dataframe(df_oh_f.head())

    with tab3:
        st.subheader("🔧 Mechanic Performance") 
        st.info("Tempel code Wrench Time lu disini. Data: `df_bd_f`")
        st.dataframe(df_bd_f.head())

    with tab4:
        st.subheader("📈 Trend Bulanan")
        trend = df_oh.groupby(df_oh['Tanggal'].dt.to_period('M')).agg({'Operating Hours':'sum','Calendar Hours':'sum'}).reset_index()
        trend['Tanggal'] = trend['Tanggal'].astype(str)
        st.line_chart(trend, x='Tanggal', y=['Operating Hours','Calendar Hours'])

    with tab5:
        st.subheader("📋 Raw Data")
        st.write("**Data BD - Bulan Terpilih**")
        st.dataframe(df_bd_f, use_container_width=True)
        st.write("**Data Timesheet - Bulan Terpilih**")
        st.dataframe(df_oh_f, use_container_width=True)

    with tab6:
        st.subheader("📝 PICA")
        st.info("Tempel code PICA lu disini")
        
else:
    st.warning("⚠️ Setup & Load 2 file dulu pake tombol '✅ Load' di atas")
