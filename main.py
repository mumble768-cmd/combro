import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Daily Breakdown Planner", layout="wide")

st.title("Aplikasi Daily Breakdown & Maintenance Planner")

st.write("Upload file Excel laporan daily breakdown unit untuk melihat dan analisa data.")

uploaded_file = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])

@st.cache_data
def load_data(file) -> pd.DataFrame:
    df = pd.read_excel(file)
    # Normalisasi nama kolom biar aman
    df.columns = [c.strip().replace("\n", " ") for c in df.columns]
    return df

if uploaded_file is not None:
    df = load_data(uploaded_file)

    st.subheader("Preview Data")
    st.dataframe(df.head(50), use_container_width=True)

    # --- Filter Sidebar ---
    st.sidebar.header("Filter Data")

    # Filter tanggal mulai kerja
    if "Start Job Date" in df.columns:
        df["Start Job Date"] = pd.to_datetime(df["Start Job Date"])
        min_date = df["Start Job Date"].min()
        max_date = df["Start Job Date"].max()
        date_range = st.sidebar.date_input(
            "Periode Start Job",
            value=(min_date, max_date)
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df["Start Job Date"] >= pd.to_datetime(start_date)) &
                    (df["Start Job Date"] <= pd.to_datetime(end_date))]

    # Filter kategori unit (EXCAVATOR, DUMP TRUCK, dll) bila ada
    if "Category Unit" in df.columns:
        categories = sorted(df["Category Unit"].dropna().unique())
        selected_cat = st.sidebar.multiselect(
            "Category Unit",
            options=categories,
            default=categories
        )
        if selected_cat:
            df = df[df["Category Unit"].isin(selected_cat)]

    # Filter type B/D
    if "Type B/D" in df.columns:
        types_bd = sorted(df["Type B/D"].dropna().unique())
        selected_types = st.sidebar.multiselect(
            "Type B/D",
            options=types_bd,
            default=types_bd
        )
        if selected_types:
            df = df[df["Type B/D"].isin(selected_types)]

    # Filter status B/D
    if "Sts B/D" in df.columns:
        sts_bd = sorted(df["Sts B/D"].dropna().unique())
        selected_sts = st.sidebar.multiselect(
            "Status B/D",
            options=sts_bd,
            default=sts_bd
        )
        if selected_sts:
            df = df[df["Sts B/D"].isin(selected_sts)]

    # Filter code number
    if "Code Number" in df.columns:
        codes = sorted(df["Code Number"].dropna().unique())
        selected_codes = st.sidebar.multiselect(
            "Code Number",
            options=codes
        )
        if selected_codes:
            df = df[df["Code Number"].isin(selected_codes)]

    st.subheader("Data Setelah Filter")
    st.dataframe(df, use_container_width=True)

    # --- Dashboard Sederhana ---
    st.subheader("Dashboard Ringkas")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_record = len(df)
        st.metric("Total Record Breakdown", total_record)

    if "Aging" in df.columns:
        with col2:
            try:
                df["Aging"] = pd.to_numeric(df["Aging"], errors="coerce")
                avg_aging = df["Aging"].mean()
                st.metric("Rata-rata Aging (hari)", f"{avg_aging:.1f}")
            except Exception:
                st.write("Kolom Aging tidak numerik")

    if "Type B/D" in df.columns:
        with col3:
            bd_count = df["Type B/D"].value_counts()
            st.write("Distribusi Type B/D")
            st.bar_chart(bd_count)

    # Breakdown per hari
    if "Start Job Date" in df.columns:
        st.subheader("Jumlah Breakdown per Hari")
        by_date = df.groupby(df["Start Job Date"].dt.date).size()
        st.line_chart(by_date)

    # --- Download hasil filter ---
    st.subheader("Download Data Hasil Filter")

    def convert_df_to_excel(df_download):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_download.to_excel(writer, index=False, sheet_name="Data")
        processed_data = output.getvalue()
        return processed_data

    excel_data = convert_df_to_excel(df)

    st.download_button(
        label="Download Excel",
        data=excel_data,
        file_name="daily_breakdown_filtered.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )