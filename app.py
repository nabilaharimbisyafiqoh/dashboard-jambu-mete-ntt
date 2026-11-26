import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# ------------------------------------------------------------
# KONFIGURASI HALAMAN
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Jambu Mete NTT",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌱 Government Agricultural Data Dashboard")
st.subheader("Dashboard Data Jambu Mete Provinsi Nusa Tenggara Timur")
st.caption("Integrasi data produksi, produktivitas, dan luas areal jambu mete | 2022–2025")

# ------------------------------------------------------------
# KONEKSI DATABASE NEON
# Simpan URL database di Streamlit Secrets, jangan tulis password
# langsung di dalam kode atau unggah ke GitHub.
# ------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    database_url = st.secrets["database"]["url"]
    conn = psycopg2.connect(database_url)
    try:
        query = """
            SELECT
                kode_wilayah,
                nama_wilayah,
                tahun,
                luas_tm_ha,
                luas_tbm_ha,
                luas_tt_tr_ha,
                produksi_ton,
                produktivitas_kg_ha,
                produktivitas_hitung,
                status_data,
                updated_at
            FROM jambu_mete_pusat
            ORDER BY nama_wilayah, tahun
        """
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return df

try:
    df = load_data()
except Exception as e:
    st.error("Dashboard belum dapat terhubung ke database Neon.")
    st.info(
        "Periksa pengaturan App → Settings → Secrets. "
        "Pastikan bagian [database] dan url sudah diisi dengan connection string "
        "project db_PUSAT_JAMBU_METE."
    )
    st.code(str(e))
    st.stop()

if df.empty:
    st.warning("Tabel jambu_mete_pusat belum memiliki data. Jalankan sinkronisasi di Google Colab terlebih dahulu.")
    st.stop()

# Pastikan tipe data numerik
numeric_cols = [
    "tahun", "luas_tm_ha", "luas_tbm_ha", "luas_tt_tr_ha",
    "produksi_ton", "produktivitas_kg_ha", "produktivitas_hitung"
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["status_data"] = df["status_data"].fillna("BELUM DIPERIKSA")

# ------------------------------------------------------------
# SIDEBAR / FILTER
# ------------------------------------------------------------
st.sidebar.header("Menu Navigasi")
menu = st.sidebar.radio(
    "Pilih tampilan",
    ["Dashboard Utama", "Statistik Kabupaten/Kota", "Tren Tahunan", "Data Jambu Mete"]
)

years = sorted(df["tahun"].dropna().astype(int).unique().tolist())
selected_year = st.sidebar.selectbox(
    "Pilih Tahun Snapshot",
    years,
    index=len(years) - 1
)
year_df = df[df["tahun"] == selected_year].copy()

st.sidebar.caption("Sumber: Database pusat Neon – jambu_mete_pusat")
st.sidebar.caption("Periode data: 2022–2025")

# ------------------------------------------------------------
# FUNGSI FORMAT
# ------------------------------------------------------------
def fmt_num(value, decimals=0):
    if pd.isna(value):
        return "-"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ------------------------------------------------------------
# DASHBOARD UTAMA
# ------------------------------------------------------------
if menu == "Dashboard Utama":
    st.header(f"Ringkasan Data Jambu Mete Tahun {selected_year}")

    total_wilayah = year_df["kode_wilayah"].nunique()
    total_produksi = year_df["produksi_ton"].sum()
    total_tm = year_df["luas_tm_ha"].sum()
    total_tbm = year_df["luas_tbm_ha"].sum()
    total_tttr = year_df["luas_tt_tr_ha"].sum()
    rata_prod = (
        total_produksi * 1000 / total_tm
        if pd.notna(total_tm) and total_tm != 0 else 0
    )
    perlu_cek = (year_df["status_data"] == "PERLU CEK").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kabupaten/Kota", fmt_num(total_wilayah))
    c2.metric("Total Produksi", f"{fmt_num(total_produksi, 2)} ton")
    c3.metric("Luas Tanaman Menghasilkan", f"{fmt_num(total_tm, 2)} ha")
    c4.metric("Produktivitas Rata-rata", f"{fmt_num(rata_prod, 2)} kg/ha")

    c5, c6, c7 = st.columns(3)
    c5.metric("Luas TBM", f"{fmt_num(total_tbm, 2)} ha")
    c6.metric("Luas TT/TR", f"{fmt_num(total_tttr, 2)} ha")
    c7.metric("Data Perlu Dicek", fmt_num(perlu_cek))

    st.divider()
    left, right = st.columns(2)

    with left:
        st.subheader("Produksi Jambu Mete per Kabupaten/Kota")
        chart_df = year_df.sort_values("produksi_ton", ascending=False)
        fig = px.bar(
            chart_df, x="nama_wilayah", y="produksi_ton",
            color="produksi_ton", color_continuous_scale="Greens",
            labels={"nama_wilayah": "Kabupaten/Kota", "produksi_ton": "Produksi (ton)"}
        )
        fig.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Distribusi Luas Areal")
        land_df = pd.DataFrame({
            "Kategori": ["Tanaman Menghasilkan (TM)", "Tanaman Belum Menghasilkan (TBM)", "Tanaman Tua/Rusak (TT/TR)"],
            "Luas (ha)": [total_tm, total_tbm, total_tttr]
        })
        fig = px.pie(
            land_df, names="Kategori", values="Luas (ha)", hole=0.35,
            color_discrete_sequence=["#176B45", "#70B77E", "#E0A33A"]
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Produktivitas per Kabupaten/Kota")
    prod_df = year_df.sort_values("produktivitas_kg_ha", ascending=False)
    fig = px.bar(
        prod_df, x="nama_wilayah", y="produktivitas_kg_ha",
        color="produktivitas_kg_ha", color_continuous_scale="Teal",
        labels={"nama_wilayah": "Kabupaten/Kota", "produktivitas_kg_ha": "Produktivitas (kg/ha)"}
    )
    fig.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Catatan: nilai produktivitas tercatat dari sumber. Baris berstatus PERLU CEK "
        "perlu diperhatikan sebelum digunakan sebagai dasar kesimpulan."
    )

# ------------------------------------------------------------
# STATISTIK KABUPATEN/KOTA
# ------------------------------------------------------------
elif menu == "Statistik Kabupaten/Kota":
    st.header(f"Statistik Kabupaten/Kota – {selected_year}")
    metric = st.selectbox(
        "Pilih indikator",
        ["produksi_ton", "produktivitas_kg_ha", "luas_tm_ha", "luas_tbm_ha", "luas_tt_tr_ha"],
        format_func=lambda x: {
            "produksi_ton": "Produksi (ton)",
            "produktivitas_kg_ha": "Produktivitas (kg/ha)",
            "luas_tm_ha": "Luas TM (ha)",
            "luas_tbm_ha": "Luas TBM (ha)",
            "luas_tt_tr_ha": "Luas TT/TR (ha)"
        }[x]
    )
    chart_df = year_df.sort_values(metric, ascending=False)
    fig = px.bar(
        chart_df, x="nama_wilayah", y=metric,
        labels={"nama_wilayah": "Kabupaten/Kota", metric: metric.replace("_", " ").title()},
        color=metric, color_continuous_scale="Greens"
    )
    fig.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        chart_df[["kode_wilayah", "nama_wilayah", metric, "status_data"]],
        use_container_width=True, hide_index=True
    )

# ------------------------------------------------------------
# TREN TAHUNAN
# ------------------------------------------------------------
elif menu == "Tren Tahunan":
    st.header("Tren Data Jambu Mete NTT Tahun 2022–2025")
    annual = (
        df.groupby("tahun", as_index=False)
        .agg(
            produksi_ton=("produksi_ton", "sum"),
            luas_tm_ha=("luas_tm_ha", "sum"),
            luas_tbm_ha=("luas_tbm_ha", "sum"),
            luas_tt_tr_ha=("luas_tt_tr_ha", "sum")
        )
        .sort_values("tahun")
    )
    annual["produktivitas_rata2"] = (
        annual["produksi_ton"] * 1000 / annual["luas_tm_ha"]
    )

    indicator = st.selectbox(
        "Pilih indikator tren",
        ["produksi_ton", "produktivitas_rata2", "luas_tm_ha", "luas_tbm_ha", "luas_tt_tr_ha"],
        format_func=lambda x: {
            "produksi_ton": "Produksi total (ton)",
            "produktivitas_rata2": "Produktivitas rata-rata (kg/ha)",
            "luas_tm_ha": "Luas TM (ha)",
            "luas_tbm_ha": "Luas TBM (ha)",
            "luas_tt_tr_ha": "Luas TT/TR (ha)"
        }[x]
    )
    fig = px.line(
        annual, x="tahun", y=indicator, markers=True,
        labels={"tahun": "Tahun", indicator: indicator.replace("_", " ").title()}
    )
    fig.update_traces(line_width=3, marker_size=10)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(annual.round(2), use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# TABEL DATA
# ------------------------------------------------------------
else:
    st.header("Data Jambu Mete Terintegrasi")
    col1, col2 = st.columns(2)
    with col1:
        filter_year = st.multiselect(
            "Filter tahun", years, default=years
        )
    with col2:
        wilayah_options = sorted(df["nama_wilayah"].dropna().unique().tolist())
        filter_wilayah = st.multiselect(
            "Filter kabupaten/kota", wilayah_options, default=wilayah_options
        )

    filtered = df[
        df["tahun"].isin(filter_year) &
        df["nama_wilayah"].isin(filter_wilayah)
    ].copy()

    display_cols = [
        "kode_wilayah", "nama_wilayah", "tahun", "produksi_ton",
        "produktivitas_kg_ha", "luas_tm_ha", "luas_tbm_ha",
        "luas_tt_tr_ha", "status_data"
    ]
    st.dataframe(
        filtered[display_cols].sort_values(["nama_wilayah", "tahun"]),
        use_container_width=True, hide_index=True
    )

    csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Unduh data hasil filter (CSV)",
        data=csv,
        file_name="data_jambu_mete_ntt.csv",
        mime="text/csv"
    )

st.divider()
st.caption("Dashboard dibuat menggunakan Python, Streamlit, Plotly, dan database PostgreSQL Neon.")
