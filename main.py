import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Mine Planner", page_icon="🛠️", layout="wide")

st.title("🛠️ Mine Planner God-Tier Dashboard")
st.caption("MAR | MTTR | MTBF | PICA | Lube | Wrench Time")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1995/1995470.png", width=80)
    st.header("📁 Data Input")
    
file_bd = st.file_uploader("1. Upload Daily BD Excel", type="xlsx")
file_oh = st.file_uploader("2. Upload Timesheet Excel", type="xlsx")

df_bd = pd.DataFrame()
df_oh = pd.DataFrame()

# BACA FILE DAILY BD
if file_bd: 
    df_bd = pd.read_excel(file_bd)
    
    # 1. Bersihin semua nama kolom: hapus spasi, lowercase
    df_bd.columns = df_bd.columns.str.strip().str.upper()
    
    # 2. Bikin mapping biar fleksibel nama kolomnya
    col_map = {
        'UNIT NO':'Unit',
        'TOTAL BD':'Downtime', 
        'COMPONEN':'Komponen',
        'COMPONENT':'Komponen',
        'STATUS BREAKDOWN':'Status_BD',
        'CODE BD':'Kode_BD',
        'DATE IN':'DateIn',
        'TIME IN':'TimeIn',
        'DATE OUT':'DateOut',
        'TIME OUT':'TimeOut'
    }
    df_bd = df_bd.rename(columns=col_map)
    
    # 3. Cek kolom wajib ada apa nggak
    kolom_wajib = ['DateIn', 'TimeIn', 'DateOut', 'TimeOut', 'Unit', 'Downtime']
    kolom_hilang = [k for k in kolom_wajib if k not in df_bd.columns]
    
    if kolom_hilang:
        st.error(f"Kolom ini nggak ketemu di Daily BD: {kolom_hilang}")
        st.write("Nama kolom yg kebaca:", list(df_bd.columns))
        st.stop()
    
    # 4. Baru bikin Start Job & Finish Job
    df_bd['Start Job'] = pd.to_datetime(
        df_bd['DateIn'].astype(str) + ' ' + df_bd['TimeIn'].astype(str),
        dayfirst=True, errors='coerce'
    )
    df_bd['Finish Job'] = pd.to_datetime(
        df_bd['DateOut'].astype(str) + ' ' + df_bd['TimeOut'].astype(str),
        dayfirst=True, errors='coerce'
    )
    df_bd['Downtime'] = pd.to_numeric(df_bd['Downtime'], errors='coerce').fillna(0)

# BACA FILE TIMESHEET
if file_oh: 
    df_oh = pd.read_excel(file_oh, skiprows=4)
    df_oh.columns = df_oh.columns.str.strip()
    df_oh = df_oh.rename(columns={'Date':'Tanggal','No Unit':'Unit','TOTAL HM':'Operating Hours','MOH':'Calendar Hours','BD':'Breakdown Hours'})
    df_oh = df_oh.dropna(subset=['Tanggal', 'Unit'])
    df_oh['Tanggal'] = pd.to_datetime(df_oh['Tanggal'], dayfirst=True)
    df_oh['Operating Hours'] = pd.to_numeric(df_oh['Operating Hours'], errors='coerce').fillna(0)
    df_oh['Calendar Hours'] = pd.to_numeric(df_oh['Calendar Hours'], errors='coerce').fillna(24)

# FILTER BULAN
with st.sidebar:
    st.header("📅 Filter Periode")
    if not df_oh.empty:
        df_oh['Periode'] = df_oh['Tanggal'].dt.to_period('M')
        list_periode = sorted(df_oh['Periode'].unique().astype(str), reverse=True)
        periode_pilih = st.selectbox("Pilih Bulan", list_periode, index=0)
        df_oh_f = df_oh[df_oh['Periode'].astype(str) == periode_pilih]
        df_bd_f = df_bd[df_bd['Start Job'].dt.to_period('M').astype(str) == periode_pilih] if not df_bd.empty else df_bd
    else:
        df_oh_f, df_bd_f = df_oh, df_bd
        periode_pilih = "Semua Data"

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 KPI", "🛢️ Lube", "🔧 Mechanic", "📈 Trend", "📋 Data", "📝 PICA"])

with tab1:
    st.subheader(f"KPI Bulan: {periode_pilih}")
    
    # CEK DULU DATANYA ADA ATAU KOSONG
    if df_oh_f.empty or df_bd_f.empty:
        st.warning("⚠️ Upload file Timesheet + Daily BD dulu bro, baru KPI muncul")
    else:
        # HITUNG KPI DARI 2 FILE
        oh = df_oh_f['Operating Hours'].sum()
        ch = df_oh_f['Calendar Hours'].sum()
        bh = df_bd_f['Downtime'].sum()
        freq_bd = len(df_bd_f)
        
        mar = oh/ch*100 if ch>0 else 0
        mttr = bh/freq_bd if freq_bd>0 else 0
        mtbf = oh/freq_bd if freq_bd>0 else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("MAR", f"{mar:.1f}%", delta=f"{mar-90:.1f}%" if mar else None)
        c2.metric("MTTR", f"{mttr:.1f} jam", help="Breakdown Hours / Frekuensi")
        c3.metric("MTBF", f"{mtbf:.1f} jam", help="Operating Hours / Frekuensi")
        c4.metric("Total BD", f"{freq_bd} kali")
        
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Operating Hours", f"{oh:,.1f} jam")
        c2.metric("Calendar Hours", f"{ch:,.1f} jam")
        c3.metric("Breakdown Hours", f"{bh:,.1f} jam")

        # TOP 5 KOMPONEN
        if 'Komponen' in df_bd_f.columns:
            st.subheader("Top 5 Komponen Biang Kerok")
            top_komp = df_bd_f.groupby('Komponen')['Downtime'].sum().nlargest(5).reset_index()
            fig = px.bar(top_komp, x='Downtime', y='Komponen', orientation='h', text_auto='.1f')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("🛢️ Lube Consumption")
    st.info("Fitur lube lu taruh disini. Data pake df_oh_f")
    if not df_oh_f.empty:
        st.dataframe(df_oh_f[['Tanggal','Unit','Operating Hours']].head())

with tab3:
    st.subheader("🔧 Mechanic Performance")
    st.info("Fitur wrench time & manpower lu taruh disini. Data pake df_bd_f")
    if not df_bd_f.empty:
        st.dataframe(df_bd_f[['Unit','Start Job','Finish Job','Downtime','Komponen']].head())

with tab4:
    st.subheader("📈 Trend MTBF & MTTR")
    st.info("Grafik trend bulanan. Nanti otomatis ke-filter sesuai bulan yg dipilih")
    if not df_oh.empty:
        trend = df_oh.groupby(df_oh['Tanggal'].dt.to_period('M')).agg({'Operating Hours':'sum','Calendar Hours':'sum'})
        st.line_chart(trend)

with tab5:
    st.subheader("📋 Raw Data")
    st.write("**Data Breakdown - Bulan Terpilih**")
    st.dataframe(df_bd_f, use_container_width=True)
    st.write("**Data Timesheet - Bulan Terpilih**")
    st.dataframe(df_oh_f, use_container_width=True)

with tab6:
    st.subheader("📝 PICA - Corrective Action")
    st.info("Form RCA 5-Why lu taruh disini. Nggak gue ubah sama sekali")
    problem = st.text_area("Deskripsi Problem")
    if st.button("Generate PICA"):
        st.success("PICA Generated!")
