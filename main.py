import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Mine Planner God-Tier", page_icon="⚙️", layout="wide")

# === CSS Biar Makin Sangar ===
st.markdown("""
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
  .main > div {padding-top: 1rem;}
    h1 {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF9068 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 800; text-align: center;
    }
    [data-testid="stMetric"] {
        background: #1E1E1E; border: 1px solid #333; padding: 20px;
        border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
  .stTabs [data-baseweb="tab"] {background-color: #262730; border-radius: 8px 8px 0 0;}
</style>
""", unsafe_allow_html=True)

st.title("⚙️ Mine Planner God-Tier Dashboard")
st.caption("MAR | MTTR | MTBF | PICA | Akurasi Service → Auto dari Excel mentah")

# === SIDEBAR ===
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4359/4359963.png", width=80)
    st.header("📁 Data Input")
    bd_file = st.file_uploader("1. Upload Daily BD Excel", type=["xlsx"])
    oh_file = st.file_uploader("2. Upload Calendar & OH Excel", type=["xlsx"], help="Wajib buat hitung MAR/MTBF")
    st.markdown("---")
    st.info("**Rumus Dipake:**\n\n- **MAR** = OH / Calendar Hours\n- **MTTR** = Total Repair Time / Frek BD\n- **MTBF** = Operating Hours / Frek BD\n- **Akurasi Service** = OnTime Service / Total Service")

@st.cache_data
def load_bd(file):
    df = pd.read_excel(file)
    df.columns = [c.strip() for c in df.columns]
    for col in ['Start Job', 'Finish Job', 'Plan Start', 'Plan Finish']:
        if col in df.columns: df[col] = pd.to_datetime(df[col], errors='coerce')
    if 'Start Job' in df.columns and 'Finish Job' in df.columns:
        df['Downtime'] = (df['Finish Job'] - df['Start Job']).dt.total_seconds() / 3600
    return df.fillna('')

@st.cache_data
def load_oh(file):
    df = pd.read_excel(file)
    df.columns = [c.strip() for c in df.columns]
    if 'Tanggal' in df.columns: df['Tanggal'] = pd.to_datetime(df['Tanggal'])
    return df

if bd_file:
    df_bd = load_bd(bd_file)
    df_oh = load_oh(oh_file) if oh_file else pd.DataFrame()

    # === FILTER ===
    with st.sidebar:
        st.subheader("🔍 Filter")
        if 'Start Job' in df_bd:
            min_d, max_d = df_bd['Start Job'].min().date(), df_bd['Start Job'].max().date()
            date_range = st.date_input("Periode Analisa", (min_d, max_d), min_d, max_d)
            if len(date_range) == 2:
                start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + timedelta(days=1)
                df_bd = df_bd[(df_bd['Start Job'] >= start) & (df_bd['Start Job'] < end)]
                if not df_oh.empty: df_oh = df_oh[(df_oh['Tanggal'] >= start) & (df_oh['Tanggal'] < end)]
        
        unit_list = sorted(df_bd['Code Number'].unique()) if 'Code Number' in df_bd else []
        sel_unit = st.multiselect("Filter Unit", unit_list)
        if sel_unit: 
            df_bd = df_bd[df_bd['Code Number'].isin(sel_unit)]
            if not df_oh.empty: df_oh = df_oh[df_oh['Unit'].isin(sel_unit)]

    # === HITUNG KPI GOD-TIER ===
    total_bd = len(df_bd)
    total_dt = df_bd['Downtime'].sum() if 'Downtime' in df_bd else 0
    mttr = total_dt / total_bd if total_bd > 0 else 0
    
    # MAR & MTBF butuh data OH
    if not df_oh.empty and 'Operating Hours' in df_oh and 'Calendar Hours' in df_oh:
        total_oh = df_oh['Operating Hours'].sum()
        total_ch = df_oh['Calendar Hours'].sum()
        mar = (total_oh / total_ch * 100) if total_ch > 0 else 0
        mtbf = (total_oh / total_bd) if total_bd > 0 else 0
    else:
        total_oh, mar, mtbf = 0, 0, 0

    # Akurasi Service: Asumsi ada kolom 'Plan Finish' vs 'Finish Job'
    if 'Plan Finish' in df_bd and 'Finish Job' in df_bd:
        ontime = df_bd[df_bd['Finish Job'] <= df_bd['Plan Finish']]
        akurasi = (len(ontime) / total_bd * 100) if total_bd > 0 else 0
    else:
        akurasi = 0

    # === TABS ===
    tab1, tab2, tab3, tab4 = st.tabs(["📊 KPI Maintenance", "🔧 PICA Analysis", "📈 Trend & Forecast", "📋 Data"])

    with tab1:
        st.subheader("KPI Level Manager")
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("MAR %", f"{mar:.2f}%", help="Mechanical Availability Ratio = OH / Calendar Hours. Target >90%")
        c2.metric("MTTR", f"{mttr:.1f} Jam", help="Mean Time To Repair = Total DT / Frek BD. Makin kecil makin bagus")
        c3.metric("MTBF", f"{mtbf:.0f} Jam", help="Mean Time Between Failure = OH / Frek BD. Makin besar makin bagus")
        c4.metric("Akurasi Service", f"{akurasi:.1f}%", help="Job selesai tepat waktu vs plan. Target >95%")
        c5.metric("Total Downtime", f"{total_dt:,.0f} Jam")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1: # Gauge MAR
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=mar, domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "MAR %"}, gauge={
                    'axis': {'range': [None, 100]}, 'bar': {'color': "#FF4B4B"},
                    'steps': [{'range': [0, 80], 'color': "#450a0a"}, {'range': [80, 90], 'color': "#854d0e"}, {'range': [90, 100], 'color': "#14532d"}],
                    'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 90}}))
            fig.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig, use_container_width=True)
        with c2: # MTTR vs MTBF
            fig = go.Figure()
            fig.add_trace(go.Bar(name='MTTR', x=['Current'], y=[mttr], marker_color='#FF4B4B'))
            fig.add_trace(go.Bar(name='MTBF', x=['Current'], y=[mtbf], marker_color='#00CC96'))
            fig.update_layout(template="plotly_dark", title="MTTR vs MTBF", barmode='group', height=300)
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("PICA - Problem Identification & Corrective Action")
        st.write("**1. Pareto Problem 80/20** → Fokus ke 20% problem yang sebabkan 80% downtime")
        if 'Problem Description' in df_bd and 'Downtime' in df_bd:
            pareto = df_bd.groupby('Problem Description')['Downtime'].sum().sort_values(ascending=False).reset_index()
            pareto['cumperc'] = pareto['Downtime'].cumsum() / pareto['Downtime'].sum() * 100
            fig = go.Figure()
            fig.add_trace(go.Bar(x=pareto['Problem Description'][:10], y=pareto['Downtime'][:10], name='Downtime Jam', marker_color='#FF4B4B'))
            fig.add_trace(go.Scatter(x=pareto['Problem Description'][:10], y=pareto['cumperc'][:10], name='Kumulatif %', yaxis='y2', line=dict(color='white')))
            fig.update_layout(template="plotly_dark", yaxis2=dict(overlaying='y', side='right', range=[0,100]), title="Problem Mana yg Bikin Rugi Jam Paling Banyak?")
            st.plotly_chart(fig, use_container_width=True)
        
        st.write("**2. Top Unit by Downtime** → Unit mana yg harus jadi prioritas PM")
        if 'Code Number' in df_bd and 'Downtime' in df_bd:
            unit_dt = df_bd.groupby('Code Number')['Downtime'].sum().sort_values(ascending=False).head(10).reset_index()
            fig = px.bar(unit_dt, x='Code Number', y='Downtime', text='Downtime', template="plotly_dark", color='Downtime', color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)

        st.write("**3. Corrective Action Tracker**")
        st.warning("**Rekomendasi Otomatis:**")
        if 'Problem Description' in df_bd:
            top_prob_dt = df_bd.groupby('Problem Description')['Downtime'].sum().idxmax()
            st.write(f"1. **Fokus Problem:** `{top_prob_dt}` karena menyumbang downtime terbesar. Cek root cause & ketersediaan part.")
        if mttr > 8:
            st.write(f"2. **MTTR Tinggi:** {mttr:.1f} Jam. Evaluasi kompetensi mekanik, ketersediaan tools, atau SOP repair.")
        if mar < 90 and mar > 0:
            st.write(f"3. **MAR Rendah:** {mar:.2f}%. Tingkatkan PM compliance & percepat eksekusi BD.")

    with tab3:
        st.subheader("Trend Analysis Buat Planning")
        if not df_oh.empty:
            daily = df_oh.groupby('Tanggal').agg({'Operating Hours':'sum', 'Calendar Hours':'sum'}).reset_index()
            daily['MAR'] = daily['Operating Hours'] / daily['Calendar Hours'] * 100
            fig = px.line(daily, x='Tanggal', y='MAR', title='Trend MAR Harian', template="plotly_dark", markers=True)
            fig.add_hline(y=90, line_dash="dash", line_color="green", annotation_text="Target 90%")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Upload file Calendar & OH buat lihat trend MAR/MTBF")

    with tab4:
        st.dataframe(df_bd, use_container_width=True)
        if not df_oh.empty:
            st.write("Data Operating Hours")
            st.dataframe(df_oh, use_container_width=True)

else:
    st.warning("👈 Upload 2 file: 1. Daily BD, 2. Calendar & OH buat unlock semua KPI")
