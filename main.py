import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
from datetime import datetime

st.set_page_config(
    page_title="Daily Breakdown Planner Pro",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CUSTOM CSS BIAR NGGAK KAYAK APP 2005 ===
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
   .main > div {padding-top: 1rem;}
    h1 {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF9068 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-align: center;
    }
    [data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464646;
        padding: 15px;
        border-radius: 10px;
    }
    [data-testid="stSidebar"] {
        background-image: linear-gradient(#1E1E1E,#262730);
    }
</style>
""", unsafe_allow_html=True)

st.title("🚜 Daily Breakdown & Maintenance Planner Pro")

# === SIDEBAR ===
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1087/1087815.png", width=80)
    st.header("📁 Control Panel")
    uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"], help="File KPI Daily Breakdown")
    st.markdown("---")

@st.cache_data(show_spinner="Loading data...")
def load_data(file) -> pd.DataFrame:
    df = pd.read_excel(file)
    df.columns = [c.strip().replace("\n", " ") for c in df.columns]
    df = df.fillna('') # FIX ARROW ERROR

    # Auto detect & convert date columns
    for col in df.columns:
        if any(key in col.lower() for key in ['date', 'start', 'finish', 'tgl']):
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            except: pass
    return df

if uploaded_file is not None:
    df = load_data(uploaded_file)
    df_filtered = df.copy()

    # === FILTER DINAMIS ===
    with st.sidebar:
        st.subheader("🔍 Smart Filter")

        # Filter Date
        date_cols = df.select_dtypes(include=['datetime64[ns]']).columns.tolist()
        if date_cols:
            date_col = st.selectbox("Pilih Kolom Tanggal", date_cols, index=0)
            min_date, max_date = df[date_col].min(), df[date_col].max()
            if pd.notna(min_date):
                date_range = st.date_input("Rentang Tanggal", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                if len(date_range) == 2:
                    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
                    df_filtered = df_filtered[(df_filtered[date_col] >= start) & (df_filtered[date_col] <= end)]

        # Filter Categorical auto-generate
        for col in ['Category Unit', 'Type B/D', 'Sts B/D', 'Code Number', 'Unit Model']:
            if col in df.columns:
                options = sorted([x for x in df[col].unique() if x!= ''])
                selected = st.multiselect(f"Filter {col}", options=options)
                if selected:
                    df_filtered = df_filtered[df_filtered[col].isin(selected)]

        st.markdown("---")
        st.success(f"Data tampil: {len(df_filtered)} dari {len(df)} baris")

    # === TABS BUAT RAPIIN LAYOUT ===
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📋 Data Table", "⬇️ Export"])

    with tab1:
        # === KPI ROW ===
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        kpi1.metric("Total Breakdown", f"{len(df_filtered):,}", help="Jumlah baris setelah filter")

        if "Aging" in df_filtered.columns:
            avg_aging = pd.to_numeric(df_filtered["Aging"], errors='coerce').mean()
            kpi2.metric("Rata-rata Aging", f"{avg_aging:.1f} Hari" if pd.notna(avg_aging) else "-")

        if "Unit Model" in df_filtered.columns:
            kpi3.metric("Unit Terdampak", df_filtered["Unit Model"].nunique())

        if "HM/KM" in df_filtered.columns:
            total_hm = pd.to_numeric(df_filtered["HM/KM"], errors='coerce').sum()
            kpi4.metric("Total HM/KM", f"{total_hm:,.0f}")

        st.markdown("---")

        # === CHARTS SECTION ===
        c1, c2 = st.columns([2, 1])

        with c1:
            if date_col in df_filtered.columns:
                daily = df_filtered.groupby(df_filtered[date_col].dt.date).size().reset_index(name='count')
                fig = px.line(daily, x=date_col, y='count', markers=True, title='Trend Breakdown Harian',
                              template="plotly_dark")
                fig.update_layout(height=400, margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            if "Type B/D" in df_filtered.columns:
                pie_data = df_filtered["Type B/D"].value_counts().reset_index()
                fig2 = px.pie(pie_data, names="Type B/D", values="count", title='Komposisi Type B/D',
                              hole=.4, template="plotly_dark")
                fig2.update_traces(textinfo='percent+label')
                fig2.update_layout(height=400, margin=dict(l=20,r=20,t=40,b=20))
                st.plotly_chart(fig2, use_container_width=True)

        c3, c4 = st.columns(2)
        with c3:
            if "Problem Description" in df_filtered.columns:
                top_prob = df_filtered["Problem Description"].value_counts().nlargest(10).reset_index()
                fig3 = px.bar(top_prob, y='Problem Description', x='count', orientation='h',
                              title='Top 10 Problem', template="plotly_dark", text='count')
                fig3.update_layout(height=450, yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig3, use_container_width=True)

        with c4:
            if "Unit Model" in df_filtered.columns:
                unit_count = df_filtered["Unit Model"].value_counts().nlargest(10).reset_index()
                fig4 = px.bar(unit_count, x='Unit Model', y='count', title='Top 10 Unit Model Breakdown',
                              template="plotly_dark", text='count', color='count', color_continuous_scale='Reds')
                fig4.update_layout(height=450)
                st.plotly_chart(fig4, use_container_width=True)

    with tab2:
        st.subheader("Data Hasil Filter")
        st.dataframe(df_filtered, use_container_width=True, height=600)

    with tab3:
        st.subheader("Download Data")
        st.write("Download data yang sudah difilter ke format Excel")

        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='FilteredData')
            return output.getvalue()

        excel_data = to_excel(df_filtered)
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"breakdown_filtered_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    st.info("👈 Silakan upload file Excel di sidebar untuk memulai analisa", icon="ℹ️")
    st.image("https://i.imgur.com/gJtT4lD.png", caption="Contoh Tampilan Dashboard Pro")
