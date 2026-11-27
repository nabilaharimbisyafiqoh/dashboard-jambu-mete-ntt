import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px

# =========================
# KONFIGURASI HALAMAN
# =========================
st.set_page_config(
    page_title="Jambu Mete NTT | Data Center",
    page_icon="🌰",
    layout="wide"
)

GREEN = "#1F5D42"
ORANGE = "#E59A3A"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.stApp {
    background: #F6F7F3;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 1500px;
}

[data-testid="stSidebar"] {
    background: #173F30;
}

[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
}

.hero {
    background: linear-gradient(115deg, #173F30, #276447, #D58B35);
    padding: 30px;
    border-radius: 20px;
    color: white;
    margin-bottom: 25px;
}

.hero h1 {
    color: white;
    font-size: 2rem;
    font-weight: 800;
}

.hero p {
    color: #E8F0E9;
}

[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 15px;
    border: 1px solid #E6EAE3;
}

[data-testid="stMetricValue"] {
    color: #1F5D42;
}

.section-title {
    color: #1F5D42;
    font-size: 1.2rem;
    font-weight: 800;
    margin-top: 15px;
}
</style>
""", unsafe_allow_html=True)


# =========================
# MENGAMBIL DATA DATABASE
# =========================
@st.cache_data(ttl=300)
def load_data():
    conn = psycopg2.connect(st.secrets["database"]["url"])

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

    try:
        data = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    return data


try:
    df = load_data()

except Exception as e:
    st.error("Dashboard gagal mengambil data dari database.")
    st.caption("Silakan periksa pengaturan Secrets di Streamlit.")
    st.exception(e)
    st.stop()


if df.empty:
    st.warning("Belum ada data pada database.")
    st.stop()


# =========================
# PENGOLAHAN DATA
# =========================
numeric_columns = [
    "tahun",
    "luas_tm_ha",
    "luas_tbm_ha",
    "luas_tt_tr_ha",
    "produksi_ton",
    "produktivitas_kg_ha",
    "produktivitas_hitung"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["nama_wilayah"] = df["nama_wilayah"].fillna("Tidak diketahui")
df["status_data"] = df["status_data"].fillna("BELUM DIPERIKSA")

years = sorted(df["tahun"].dropna().astype(int).unique())

if not years:
    st.error("Tidak ditemukan tahun data yang valid.")
    st.stop()


# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## 🌰 METE NTT")
st.sidebar.caption("Pusat Informasi Data Komoditas")

page = st.sidebar.radio(
    "NAVIGASI",
    [
        "Ringkasan",
        "Perbandingan Wilayah",
        "Tren & Perkembangan",
        "Eksplorasi Data",
        "Kualitas Data"
    ]
)

st.sidebar.markdown("---")

selected_year = st.sidebar.selectbox(
    "Tahun Analisis",
    years,
    index=len(years)-1
)

regions = sorted(df["nama_wilayah"].unique())

selected_regions = st.sidebar.multiselect(
    "Kabupaten/Kota",
    regions,
    default=regions
)

filtered = df[
    (df["tahun"] == selected_year) &
    (df["nama_wilayah"].isin(selected_regions))
].copy()

historical = df[
    df["nama_wilayah"].isin(selected_regions)
].copy()


# =========================
# HEADER
# =========================
st.markdown("""
<div class="hero">
    <h1>🌰 Jambu Mete Data Center</h1>
    <p>
        Dashboard analisis produksi, produktivitas,
        dan luas areal jambu mete Provinsi Nusa Tenggara Timur.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================
# MENU 1: RINGKASAN
# =========================
if page == "Ringkasan":

    st.markdown(
        '<div class="section-title">Ikhtisar Provinsi</div>',
        unsafe_allow_html=True
    )

    produksi = filtered["produksi_ton"].sum()
    luas_tm = filtered["luas_tm_ha"].sum()
    luas_tbm = filtered["luas_tbm_ha"].sum()
    luas_tttr = filtered["luas_tt_tr_ha"].sum()

    produktivitas = (
        produksi * 1000 / luas_tm
        if luas_tm > 0 else 0
    )

    jumlah_wilayah = filtered["nama_wilayah"].nunique()

    flagged = filtered["status_data"].str.contains(
        "CEK|BELUM|KOSONG|PERLU",
        case=False,
        na=False
    ).sum()

    a, b, c, d = st.columns(4)

    a.metric("Kabupaten/Kota", jumlah_wilayah)
    b.metric("Total Produksi", f"{produksi:,.2f} ton")
    c.metric("Luas Tanaman Menghasilkan", f"{luas_tm:,.2f} ha")
    d.metric("Produktivitas Hitung", f"{produktivitas:,.2f} kg/ha")

    e, f, g = st.columns(3)

    e.metric("Luas TBM", f"{luas_tbm:,.2f} ha")
    f.metric("Luas TT/TR", f"{luas_tttr:,.2f} ha")
    g.metric("Data Perlu Ditinjau", int(flagged))

    st.markdown("---")

    left, right = st.columns([1.4, 1])

    with left:
        st.markdown("### 🏆 10 Wilayah Produksi Tertinggi")

        ranking = (
            filtered.groupby("nama_wilayah")["produksi_ton"]
            .sum()
            .sort_values()
            .tail(10)
            .reset_index()
        )

        fig = px.bar(
            ranking,
            x="produksi_ton",
            y="nama_wilayah",
            orientation="h",
            color="produksi_ton",
            color_continuous_scale=["#B9D8C2", GREEN],
            labels={
                "produksi_ton": "Produksi (ton)",
                "nama_wilayah": "Kabupaten/Kota"
            }
        )

        fig.update_layout(
            height=430,
            coloraxis_showscale=False,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("### 🌱 Komposisi Luas Areal")

        area = pd.DataFrame({
            "Kategori": [
                "Tanaman Menghasilkan",
                "Tanaman Belum Menghasilkan",
                "Tanaman Tua/Rusak"
            ],
            "Luas": [luas_tm, luas_tbm, luas_tttr]
        })

        area = area[area["Luas"] > 0]

        fig = px.pie(
            area,
            names="Kategori",
            values="Luas",
            hole=0.55,
            color_discrete_sequence=[
                GREEN,
                ORANGE,
                "#9BA8A0"
            ]
        )

        fig.update_layout(height=430)

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📌 Sorotan Wilayah")

    if not filtered["produksi_ton"].dropna().empty:

        best = filtered.loc[
            filtered["produksi_ton"].idxmax()
        ]

        low = filtered.loc[
            filtered["produksi_ton"].idxmin()
        ]

        x, y = st.columns(2)

        x.success(
            f"Produksi tertinggi: {best['nama_wilayah']} "
            f"({best['produksi_ton']:,.2f} ton)"
        )

        y.info(
            f"Produksi terendah: {low['nama_wilayah']} "
            f"({low['produksi_ton']:,.2f} ton)"
        )


# =========================
# MENU 2: PERBANDINGAN
# =========================
elif page == "Perbandingan Wilayah":

    st.markdown("## 📊 Perbandingan Kabupaten/Kota")

    indicators = {
        "Produksi (ton)": "produksi_ton",
        "Produktivitas sumber (kg/ha)": "produktivitas_kg_ha",
        "Luas TM (ha)": "luas_tm_ha",
        "Luas TBM (ha)": "luas_tbm_ha",
        "Luas TT/TR (ha)": "luas_tt_tr_ha"
    }

    selected_indicator = st.selectbox(
        "Pilih indikator",
        list(indicators.keys())
    )

    col = indicators[selected_indicator]

    comparison = (
        filtered.groupby("nama_wilayah")[col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig = px.bar(
        comparison,
        x="nama_wilayah",
        y=col,
        color=col,
        text_auto=".2s",
        color_continuous_scale=["#B9D8C2", GREEN]
    )

    fig.update_layout(
        height=480,
        coloraxis_showscale=False,
        xaxis_title="Kabupaten/Kota",
        yaxis_title=selected_indicator,
        xaxis_tickangle=-35
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        comparison,
        use_container_width=True,
        hide_index=True
    )


# =========================
# MENU 3: TREN
# =========================
elif page == "Tren & Perkembangan":

    st.markdown("## 📈 Tren & Perkembangan Tahunan")

    options = {
        "Produksi (ton)": "produksi_ton",
        "Luas TM (ha)": "luas_tm_ha",
        "Luas TBM (ha)": "luas_tbm_ha",
        "Luas TT/TR (ha)": "luas_tt_tr_ha"
    }

    selected = st.selectbox(
        "Pilih indikator",
        list(options.keys())
    )

    col = options[selected]

    trend = (
        historical.groupby("tahun")[col]
        .sum()
        .reset_index()
        .sort_values("tahun")
    )

    fig = px.line(
        trend,
        x="tahun",
        y=col,
        markers=True,
        color_discrete_sequence=[GREEN]
    )

    fig.update_traces(
        line_width=4,
        marker_size=10
    )

    fig.update_layout(
        height=430,
        xaxis_title="Tahun",
        yaxis_title=selected
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        trend,
        use_container_width=True,
        hide_index=True
    )


# =========================
# MENU 4: EKSPLORASI DATA
# =========================
elif page == "Eksplorasi Data":

    st.markdown("## 🔎 Eksplorasi Data")

    search = st.text_input(
        "Cari Kabupaten/Kota"
    )

    year_filter = st.multiselect(
        "Filter tahun",
        years,
        default=years
    )

    view = df[
        df["nama_wilayah"].str.contains(
            search,
            case=False,
            na=False
        ) &
        df["tahun"].isin(year_filter)
    ].copy()

    st.caption(f"Jumlah data: {len(view)} baris")

    st.dataframe(
        view,
        use_container_width=True,
        hide_index=True
    )

    csv = view.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "⬇️ Unduh Data CSV",
        csv,
        "data_jambu_mete_ntt.csv",
        "text/csv"
    )


# =========================
# MENU 5: KUALITAS DATA
# =========================
elif page == "Kualitas Data":

    st.markdown("## 🛡️ Kualitas Data")

    status = (
        df["status_data"]
        .value_counts()
        .reset_index()
    )

    status.columns = ["Status", "Jumlah"]

    left, right = st.columns(2)

    with left:

        fig = px.pie(
            status,
            names="Status",
            values="Jumlah",
            hole=0.55,
            color_discrete_sequence=[
                GREEN,
                ORANGE,
                "#9BA8A0",
                "#C65B4B"
            ]
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with right:

        st.dataframe(
            status,
            use_container_width=True,
            hide_index=True
        )

    flagged = df[
        df["status_data"].str.contains(
            "CEK|BELUM|KOSONG|PERLU",
            case=False,
            na=False
        )
    ]

    st.markdown("### Data yang Perlu Ditinjau")

    if flagged.empty:
        st.success("Tidak ditemukan data yang perlu ditinjau.")
    else:
        st.warning(f"{len(flagged)} baris perlu diperiksa.")

        st.dataframe(
            flagged,
            use_container_width=True,
            hide_index=True
        )


st.markdown("---")
st.caption(
    "Jambu Mete Data Center • Database pusat Neon PostgreSQL"
)
