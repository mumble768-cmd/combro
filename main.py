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
            if not df_oh.empty and 'Unit' in df_oh.columns: df_oh = df_oh[df_oh['Unit'].isin(sel_unit)]

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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 KPI Maintenance", "🔧 PICA Analysis", "📈 Trend & Forecast", "📋 Data", "📝 PICA Tracker"])

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
            fig.update_layout(template="plotly_dark", height=300, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)
        with c2: # MTTR vs MTBF
            fig = go.Figure()
            fig.add_trace(go.Bar(name='MTTR', x=['Current'], y=[mttr], marker_color='#FF4B4B'))
            fig.add_trace(go.Bar(name='MTBF', x=['Current'], y=[mtbf], marker_color='#00CC96'))
            fig.update_layout(template="plotly_dark", title="MTTR vs MTBF", barmode='group', height=300, margin=dict(l=20, r=20, t=50, b=20))
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
        if 'Problem Description' in df_bd and total_dt > 0:
            top_prob_dt = df_bd.groupby('Problem Description')['Downtime'].sum().idxmax()
            st.write(f"1. **Fokus Problem:** `{top_prob_dt}` karena menyumbang downtime terbesar. Cek root cause & ketersediaan part.")
        if mttr > 8:
            st.write(f"2. **MTTR Tinggi:** {mttr:.1f} Jam. Evaluasi kompetensi mekanik, ketersediaan tools, atau SOP repair.")
        if mar < 90 and mar > 0:
            st.write(f"3. **MAR Rendah:** {mar:.2f}%. Tingkatkan PM compliance & percepat eksekusi BD.")

    with tab3:
        st.subheader("Trend Analysis Buat Planning")
        if not df_oh.empty and 'Tanggal' in df_oh:
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

    with tab5:
        st.subheader("📝 PICA - Live Action Plan")
        st.caption("Input Root Cause & Corrective Action langsung dari dashboard. Data bisa di-download.")

        # Inisialisasi database PICA di session
        if 'pica_db' not in st.session_state:
            st.session_state.pica_db = pd.DataFrame(columns=[
                'Tanggal', 'Unit', 'Problem', 'Root Cause', 'Corrective Action', 'PIC', 'Due Date', 'Status'
            ])

        # === FORM INPUT PICA ===
        with st.form("pica_form", clear_on_submit=True):
            st.write("**Input PICA Baru**")
            c1, c2, c3 = st.columns(3)
            with c1:
                p_unit = st.selectbox("Pilih Unit", options=[''] + unit_list, key="pica_unit")
                prob_list = sorted(df_bd['Problem Description'].unique()) if 'Problem Description' in df_bd else []
                p_prob = st.selectbox("Pilih Problem", options=[''] + prob_list, key="pica_prob")
            with c2:
                p_rca = st.text_area("Root Cause Analysis", placeholder="Kenapa bisa rusak? 5-Why Analysis...")
                p_pic = st.text_input("PIC", placeholder="Nama Mekanik/Spv")
            with c3:
                p_ca = st.text_area("Corrective Action", placeholder="Apa tindakan biar nggak kejadian lagi?")
                p_due = st.date_input("Due Date", value=datetime.now() + timedelta(days=7))
            
            submitted = st.form_submit_button("💾 Simpan PICA", use_container_width=True)
            if submitted:
                if p_unit and p_prob and p_rca and p_ca and p_pic:
                    new_pica = pd.DataFrame([{
                        'Tanggal': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'Unit': p_unit,
                        'Problem': p_prob,
                        'Root Cause': p_rca,
                        'Corrective Action': p_ca,
                        'PIC': p_pic,
                        'Due Date': p_due.strftime("%Y-%m-%d"),
                        'Status': 'Open'
                    }])
                    st.session_state.pica_db = pd.concat([st.session_state.pica_db, new_pica], ignore_index=True)
                    st.success(f"PICA untuk {p_unit} - {p_prob} berhasil disimpan!")
                    st.balloons()
                else:
                    st.error("Wajib isi semua kolom bro!")

        st.markdown("---")
        
        # === TABEL PICA LIVE ===
        st.write("**Database PICA**")
        if not st.session_state.pica_db.empty:
            # Filter & Edit Status
            c1, c2, c3 = st.columns([2,2,1])
            with c1:
                filter_status = st.selectbox("Filter Status", ['All', 'Open', 'In Progress', 'Closed'])
            with c2:
                filter_pic = st.selectbox("Filter PIC", ['All'] + sorted(st.session_state.pica_db['PIC'].unique()))
            
            df_display = st.session_state.pica_db.copy()
            if filter_status!= 'All':
                df_display = df_display[df_display['Status'] == filter_status]
            if filter_pic!= 'All':
                df_display = df_display[df_display['PIC'] == filter_pic]

            # Tampilan tabel + edit status
            edited_df = st.data_editor(
                df_display,
                column_config={
                    "Status": st.column_config.SelectboxColumn("Status", options=['Open', 'In Progress', 'Closed'], required=True),
                    "Due Date": st.column_config.DateColumn("Due Date", format="YYYY-MM-DD"),
                },
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic"
            )
            
            # Update database kalo ada perubahan status
            if not edited_df.equals(df_display):
                for idx, row in edited_df.iterrows():
                    mask = (st.session_state.pica_db['Tanggal'] == row['Tanggal']) & (st.session_state.pica_db['Unit'] == row['Unit'])
                    st.session_state.pica_db.loc[mask, 'Status'] = row['Status']
                st.toast("Status PICA berhasil di-update!")

            # KPI PICA
            k1, k2, k3 = st.columns(3)
            k1.metric("Total PICA Open", len(st.session_state.pica_db[st.session_state.pica_db['Status'] == 'Open']))
            overdue = st.session_state.pica_db[
                (st.session_state.pica_db['Status']!= 'Closed') & 
                (pd.to_datetime(st.session_state.pica_db['Due Date']) < datetime.now())
            ]
            k2.metric("PICA Overdue", len(overdue), delta=f"{len(overdue)} case", delta_color="inverse")
            k3.metric("Completion Rate", f"{len(st.session_state.pica_db[st.session_state.pica_db['Status']=='Closed'])/len(st.session_state.pica_db)*100:.0f}%" if len(st.session_state.pica_db)>0 else "0%")

            # Download
            def to_excel_pica(df):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='PICA')
                return output.getvalue()
            st.download_button("📥 Download Database PICA", to_excel_pica(st.session_state.pica_db), f"PICA_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)
        
        else:
            st.info("Belum ada data PICA. Input form di atas dulu bro.")

else:
    st.warning("👈 Upload 2 file: 1. Daily BD, 2. Calendar & OH buat unlock semua KPI")
