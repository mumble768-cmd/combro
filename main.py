import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

st.set_page_config(page_title="Mine KPI Dashboard", page_icon="⛏️", layout="wide")
st.title("⛏️ Mine KPI Dashboard - God Tier")

@st.cache_data
def load_data(file):
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        'UNIT NO':'Unit', 'UNIT OWNER':'Owner', 'UNIT TYPE':'Type',
        'MOHH (Machine On Hand Hour)':'MOHH', 'WH (Work Hours)':'WH',
        'TOTAL BD':'BD Hours', 'REPAIR TOTAL':'Repair Freq', 'UA%':'UA', 'MA%':'MA'
    })
    for col in ['UA','MA','BD Hours','MTTR','MTBF','WH','MOHH','Repair Freq']:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def color_bad(val, threshold=85):
    return 'background-color: #FF4B4B; color: white' if isinstance(val, (int,float)) and val < threshold else ''

with st.sidebar:
    st.header("📁 Upload Data")
    file = st.file_uploader("Upload Excel Data Mateng", type="xlsx")

if file:
    df = load_data(file)

    with st.sidebar:
        st.header("📅 Filter")
        list_owner = st.multiselect("Owner", df['Owner'].unique(), default=df['Owner'].unique())
        list_type = st.multiselect("Type Unit", df['Type'].unique(), default=df['Type'].unique())
        df_temp = df[(df['Owner'].isin(list_owner)) & (df['Type'].isin(list_type))]
        list_unit = st.multiselect("Unit No", df_temp['Unit'].unique(), default=df_temp['Unit'].unique())

    df_f = df[(df['Owner'].isin(list_owner)) & (df['Type'].isin(list_type)) & (df['Unit'].isin(list_unit))]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Avg UA", f"{df_f['UA'].mean():.2f}%")
    c2.metric("Avg MA", f"{df_f['MA'].mean():.2f}%")
    c3.metric("Total BD", f"{df_f['BD Hours'].sum():.2f} jam")
    c4.metric("Total Unit", f"{df_f['Unit'].nunique()}")
    
    st.dataframe(df_f.style.applymap(color_bad, subset=['UA','MA']), use_container_width=True)
    st.download_button("📥 Download Excel", df_f.to_csv(index=False), "laporan_kpi.csv")

else:
    st.info("👆 Upload file Excel untuk mulai")
