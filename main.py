import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

st.set_page_config(
    page_title="Mine Planner Pro Dashboard",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CSS PREMIUM ===
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
   .main > div {padding-top: 1rem;}
    h1 {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF9068 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; text-align: center;
    }
    [data-testid="stMetric"] {
        background: #1E1E1E;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    [data-testid="stSidebar"] {background: #0E1117;}
   .stTabs [data-baseweb="tab-list"] {gap: 8px;}
   .stTabs [data-baseweb="tab"] {
        background-color: #262730;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("⛏️ Mine Planner Pro Dashboard")
st.caption("Upload data mentah Excel → Auto jadi analisa & planning breakdown")

# === SIDEBAR ===
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4359/4359963.png", width=100)
    st.header("📁 Control Panel")
    uploaded_file = st.file_uploader("Upload Daily BD Excel (.xlsx)", type=["xlsx"])
    st.markdown("---")
    st.info("**Tips:** Pastikan Excel ada kolom: Code Number, Unit Model, Start Job, Problem Description, Type B/D")

@st.cache_data(show_spinner="Processing data...")
def load_and_clean(file):
    df = pd.read_excel(file)
    df.columns = [c.strip().replace("\n", " ") for c in df.columns]
    df = df.fillna('')
    
    # Auto convert date
    date_cols = [c for c in df.columns if any(k in c.lower() for k in ['date', 'start', 'finish', 'tgl'])]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Auto convert numeric
    num_cols = ['Aging', 'HM/KM', 'Downtime', 'MTTR', 'MTBF']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # Hitung Duration kalo ada Start & Finish
    if 'Start Job' in df.columns and 'Finish Job' in df.columns:
        df['Duration (Hours)'] = (df['Finish Job'] - df['Start Job']).dt.total_seconds() / 3600
    
    return df, date_cols

if uploaded_file:
    df, date_cols = load_and_clean(uploaded_file)
    df_filtered = df.copy()

    # === FILTER PINTAR ===
    with st.sidebar:
        st.subheader("🔍 Smart Filter")
        if date_cols:
            main_date = st.selectbox("Kolom Tanggal Utama", date_cols, index=0)
            min_d, max_d = df[main_date].min(), df[main_date].max()
            if pd.notna(min_d):
                date_range = st.date_input("Rentang Tanggal", (min_d, max_d), min_d, max_d)
                if len(date_range) == 2:
                    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + timedelta(days=1)
                    df_filtered = df_filtered[(df_filtered[main_date] >= start) & (df_filtered[main_date] < end)]

        for col in ['Site', 'Category Unit', 'Type B/D', 'Sts B/D', 'Unit Model', 'Section']:
            if col in df.columns:
                opts = sorted([x for x in df[col].unique() if x])
                sel = st.multiselect(col, opts)
                if sel: df_filtered = df_filtered[df_filtered[col].isin(sel)]
        
        st.success(f"Data aktif: {len(df_filtered):,} baris")
        st.markdown("---")
        st.metric("Periode Data", f"{df_filtered[main_date].min().date()} s/d {df_filtered[main_date].max().date()}" if date_cols else "-")

    # === TABS UTAMA PLANNER ===
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Summary", "🔧 Maintenance Analysis", "📈 Planning & Forecast", "📋 Raw Data"])

    with tab1: # EXECUTIVE SUMMARY
        st.subheader("KPI Utama Planner")
        k1, k2, k3, k4, k5 = st.columns(5)
        
        total_bd = len(df_filtered)
        k1.metric("Total Breakdown", f"{total_bd:,}", help="Jumlah kejadian BD periode ini")
        
        unique_unit = df_filtered['Code Number'].nunique() if 'Code Number' in df_filtered else 0
        k2.metric("Unit Terdampak", unique_unit)
        
        if 'Duration (Hours)' in df_filtered:
            total_dt = df_filtered['Duration (Hours)'].sum()
            k3.metric("Total Downtime", f"{total_dt:,.0f} Jam")
            avg_dt = df_filtered['Duration (Hours)'].mean()
            k4.metric("Avg Downtime", f"{avg_dt:.1f} Jam")
        
        if 'Aging' in df_filtered:
            avg_aging = df_filtered['Aging'].mean()
            k5.metric("Avg Aging BD", f"{avg_aging:.1f} Hari", delta=f"{avg_aging-7:.1f} vs target 7 hari", delta_color="inverse")

        st.markdown("---")
        c1, c2 = st.columns([2,1])
        with c1:
            if main_date in df_filtered:
                daily = df_filtered.groupby(df_filtered[main_date].dt.date).size().reset_index(name='Jumlah BD')
                fig = px.area(daily, x=main_date, y='Jumlah BD', title='Trend Breakdown Harian', template="plotly_dark", markers=True)
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            if 'Type B/D' in df_filtered:
                fig2 = px.pie(df_filtered, names='Type B/D', title='Komposisi Type BD', hole=.5, template="plotly_dark")
                st.plotly_chart(fig2, use_container_width=True)

    with tab2: # MAINTENANCE ANALYSIS
        st.subheader("Analisa Akar Masalah")
        c1, c2 = st.columns(2)
        with c1:
            if 'Problem Description' in df_filtered:
                top_prob = df_filtered['Problem Description'].value_counts().nlargest(10).reset_index()
                fig = px.bar(top_prob, y='Problem Description', x='count', orientation='h', title='Top 10 Problem Berulang',
                             template="plotly_dark", text='count', color='count', color_continuous_scale='Reds')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            if 'Code Number' in df_filtered:
                top_unit = df_filtered['Code Number'].value_counts().nlargest(10).reset_index()
                fig = px.bar(top_unit, x='Code Number', y='count', title='Top 10 Unit Paling Rewel',
                             template="plotly_dark", text='count', color='count', color_continuous_scale='Oranges')
                st.plotly_chart(fig, use_container_width=True)
        
        if 'Unit Model' in df_filtered and 'Problem Description' in df_filtered:
            st.subheader("Heatmap Problem vs Unit Model")
            heatmap_data = pd.crosstab(df_filtered['Unit Model'], df_filtered['Problem Description'])
            fig = px.imshow(heatmap_data, text_auto=True, aspect="auto", template="plotly_dark",
                            color_continuous_scale='Reds', title='Unit mana sering kena problem apa')
            st.plotly_chart(fig, use_container_width=True)

    with tab3: # PLANNING & FORECAST
        st.subheader("Tools Buat Planning")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**1. Pareto Problem 80/20**")
            if 'Problem Description' in df_filtered:
                prob_count = df_filtered['Problem Description'].value_counts().reset_index()
                prob_count['cumperc'] = prob_count['count'].cumsum() / prob_count['count'].sum() * 100
                fig = go.Figure()
                fig.add_trace(go.Bar(x=prob_count['Problem Description'][:15], y=prob_count['count'][:15], name='Jumlah', marker_color='#FF4B4B'))
                fig.add_trace(go.Scatter(x=prob_count['Problem Description'][:15], y=prob_count['cumperc'][:15], name='Kumulatif %', yaxis='y2', line=dict(color='#00CC96')))
                fig.update_layout(template="plotly_dark", yaxis2=dict(overlaying='y', side='right', range=[0,100]),
                                  title="Fokus ke 20% problem ini untuk selesaikan 80% BD")
                st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.write("**2. Aging Breakdown Monitor**")
            if 'Aging' in df_filtered and 'Sts B/D' in df_filtered:
                aging_open = df_filtered[df_filtered['Sts B/D'].str.contains('Open|Progress', na=False)]
                if not aging_open.empty:
                    fig = px.histogram(aging_open, x='Aging', nbins=20, title='Distribusi Aging BD yang Masih Open', template="plotly_dark")
                    fig.add_vline(x=7, line_dash="dash", line_color="yellow", annotation_text="Target 7 Hari")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.success("Keren! Tidak ada BD yang masih Open.")
        
        st.write("**3. Rekomendasi Planner Otomatis**")
        if 'Problem Description' in df_filtered:
            top3_prob = df_filtered['Problem Description'].value_counts().nlargest(3).index.tolist()
            st.warning(f"**Fokus Minggu Ini:** Siapkan part & manpower untuk problem: 1. {top3_prob[0] if len(top3_prob)>0 else '-'}, 2. {top3_prob[1] if len(top3_prob)>1 else '-'}, 3. {top3_prob[2] if len(top3_prob)>2 else '-'}")
        if 'Aging' in df_filtered:
            critical_aging = df_filtered[df_filtered['Aging'] > 14]
            if not critical_aging.empty:
                st.error(f"**PERHATIAN:** Ada {len(critical_aging)} unit dengan Aging > 14 hari. Segera eskalasi!")
                st.dataframe(critical_aging[['Code Number', 'Unit Model', 'Problem Description', 'Aging']], use_container_width=True)

    with tab4:
        st.dataframe(df_filtered, use_container_width=True, height=600)
        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Filtered')
            return output.getvalue()
        st.download_button("📥 Download Data Filter", to_excel(df_filtered), f"BD_Filter_{datetime.now().strftime('%Y%m%d')}.xlsx", use_container_width=True)

else:
    st.warning("👈 Upload file Excel Daily Breakdown dulu di sidebar")
    st.image("https://i.imgur.com/gJtT4lD.png")
