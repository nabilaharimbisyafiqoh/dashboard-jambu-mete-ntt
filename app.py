from pathlib import Path

code = r'''import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# PAGE CONFIG & THEME
# =========================================================
st.set_page_config(
    page_title="Jambu Mete NTT | Data Center",
    page_icon="🌰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Palette: forest green, cashew orange, warm cream
GREEN = "#1F5D42"
GREEN_2 = "#3F8B62"
ORANGE = "#E59A3A"
CREAM = "#F7F4EC"
INK = "#1F2D26"
MUTED = "#6B786F"
RED = "#C65B4B"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #F6F7F3; color: #1F2D26; }
.block-container { padding-top: 1.4rem; padding-bottom: 2.5rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #173F30; }
[data-testid="stSidebar"] * { color: #F7F4EC !important; }
[data-testid="stSidebar"] [data-baseweb="select"] * { color: #1F2D26 !important; }
[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #E6EAE3; border-radius: 16px;
    padding: 17px 18px; box-shadow: 0 3px 14px rgba(31,45,38,.045);
}
[data-testid="stMetricLabel"] { color: #6B786F !important; font-weight: 600; }
[data-testid="stMetricValue"] { color: #1F5D42 !important; font-family: 'Manrope', sans-serif; }
.hero {
    background: linear-gradient(115deg, #173F30 0%, #236447 62%, #D58B35 150%);
    padding: 28px 32px; border-radius: 22px; color: #FFFFFF; margin-bottom: 22px;
    box-shadow: 0 10px 28px rgba(23,63,48,.13);
}
.hero h1 { color: white; font-family: 'Manrope', sans-serif; font-size: 2rem; margin: 0 0 6px 0; }
.hero p { color: #E8F0E9; margin: 0; font-size: .98rem; }
.eyebrow { color: #F2C47C; font-weight: 800; font-size: .72rem; letter-spacing: .14em; text-transform: uppercase; margin-bottom: 9px; }
.section-title { font-family: 'Manrope', sans-serif; color: #1F5D42; font-size: 1.18rem; font-weight: 800; margin: 12px 0 4px; }
.section-sub { color: #748078; font-size: .85rem; margin-bottom: 12px; }
.info-card {
    background: white; border: 1px solid #E6EAE3; border-radius: 16px;
    padding: 17px 19px; height: 100%;
}
.info-card h4 { color: #1F5D42; margin: 0 0 7px 0; font-size: 1rem; }
.info-card p { color: #6B786F; margin: 0; font-size: .88rem; }
div[data-testid="stDataFrame"] { border: 1px solid #E6EAE3; border-radius: 12px; overflow: hidden; }
.stButton button, .stDownloadButton button {
    border-radius: 10px; font-weight: 700; border: 1px solid #DCE5DC;
}
hr { border-color: #E3E9E1; }
.small-note { color: #7B867E; font-size: .78rem; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATA ACCESS
# =========================================================
@st.cache_data(ttl=300)
def load_data():
    database_url = st.secrets["database"]["url"]
    conn = psycopg2.connect(database_url)
    try:
        query = """
            SELECT
                kode_wilayah, nama_wilayah, tahun,
                luas_tm_ha, luas_tbm_ha, luas_tt_tr_ha,
                produksi_ton, produktivitas_kg_ha,
                produktivitas_hitung, status_data, updated_at
            FROM jambu_mete_pusat
            ORDER BY nama_wilayah, tahun
        """
        data = pd.read_sql_query(query, conn)
    finally:
        conn.close()
    return data

try:
    df = load_data()
except Exception as exc:
    st.markdown('<div class="hero"><div class="eyebrow">NTT AGRICULTURE DATA</div><h1>Jambu Mete Data Center</h1><p>Dashboard analisis komoditas jambu mete Provinsi Nusa Tenggara Timur</p></div>', unsafe_allow_html=True)
    st.error("Dashboard belum dapat mengambil data dari database Neon.")
    st.info("Periksa App settings → Secrets. Pastikan format [database] dan url sudah benar.")
    st.code(str(exc))
    st.stop()

if df.empty:
    st.warning("Belum ada data pada tabel jambu_mete_pusat.")
    st.stop()

numeric_cols = [
    "tahun", "luas_tm_ha", "luas_tbm_ha", "luas_tt_tr_ha",
    "produksi_ton", "produktivitas_kg_ha", "produktivitas_hitung"
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["status_data"] = df["status_data"].fillna("BELUM DIPERIKSA").astype(str)
df["nama_wilayah"] = df["nama_wilayah"].fillna("Tidak diketahui").astype(str)
df["tahun"] = df["tahun"].astype("Int64")

# =========================================================
# HELPERS
# =========================================================
def fmt(value, decimals=1):
    if pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def sum_col(frame, col):
    return pd.to_numeric(frame[col], errors="coerce").sum(min_count=1)

def make_chart(fig, height=360):
    fig.update_layout(
        height=height, margin=dict(l=12, r=12, t=30, b=12),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans", color=INK),
        hoverlabel=dict(bgcolor="white", font_size=12),
        legend_title_text=""
    )
    fig.update_xaxes(showgrid=False, linecolor="#E6EAE3")
    fig.update_yaxes(gridcolor="#E9EEE8", zeroline=False)
    return fig

def metric_delta(current, previous):
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return None
    return f"{((current - previous) / abs(previous)) * 100:+.1f}% dibanding tahun sebelumnya"

# =========================================================
# SIDEBAR NAVIGATION & FILTERS
# =========================================================
st.sidebar.markdown("## 🌰 METE NTT")
st.sidebar.caption("Pusat Informasi Data Komoditas")
page = st.sidebar.radio(
    "NAVIGASI",
    ["Ringkasan", "Perbandingan Wilayah", "Tren & Perkembangan", "Eksplorasi Data", "Kualitas Data"],
    label_visibility="visible"
)
st.sidebar.markdown("---")
years = sorted(df["tahun"].dropna().astype(int).unique().tolist())
if not years:
    st.error("Kolom tahun belum memiliki data yang valid.")
    st.stop()
selected_year = st.sidebar.selectbox("Tahun analisis", years, index=len(years)-1)
all_regions = sorted(df["nama_wilayah"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Kabupaten/Kota", all_regions, default=all_regions)
st.sidebar.markdown("---")
st.sidebar.markdown("**Sumber data**")
st.sidebar.caption("Database pusat Neon PostgreSQL")
st.sidebar.caption(f"Periode tersedia: {min(years)}–{max(years)}")
st.sidebar.caption("Pembaruan data mengikuti sinkronisasi database.")

filtered_all = df[df["nama_wilayah"].isin(selected_regions)].copy()
year_df = filtered_all[filtered_all["tahun"] == selected_year].copy()
prev_year_df = filtered_all[filtered_all["tahun"] == selected_year - 1].copy()
annual = (
    filtered_all.groupby("tahun", as_index=False)
    .agg(
        produksi_ton=("produksi_ton", "sum"),
        luas_tm_ha=("luas_tm_ha", "sum"),
        luas_tbm_ha=("luas_tbm_ha", "sum"),
        luas_tt_tr_ha=("luas_tt_tr_ha", "sum")
    )
    .sort_values("tahun")
)
annual["produktivitas_rata2"] = annual.apply(
    lambda r: (r["produksi_ton"] * 1000 / r["luas_tm_ha"])
    if pd.notna(r["luas_tm_ha"]) and r["luas_tm_ha"] > 0 else None,
    axis=1
)

# =========================================================
# HEADER
# =========================================================
st.markdown(f"""
<div class="hero">
  <div class="eyebrow">NTT AGRICULTURE • COMMODITY INSIGHT</div>
  <h1>🌰 Jambu Mete Data Center</h1>
  <p>Memantau produksi, produktivitas, dan luas areal jambu mete di Nusa Tenggara Timur.</p>
</div>
""", unsafe_allow_html=True)

# =========================================================
# PAGE 1: SUMMARY
# =========================================================
if page == "Ringkasan":
    st.markdown(f'<div class="section-title">Ikhtisar Provinsi • {selected_year}</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Ringkasan indikator berdasarkan tahun dan wilayah yang dipilih pada panel kiri.</div>', unsafe_allow_html=True)

    wilayah_count = year_df["kode_wilayah"].nunique()
    produksi = sum_col(year_df, "produksi_ton")
    tm = sum_col(year_df, "luas_tm_ha")
    tbm = sum_col(year_df, "luas_tbm_ha")
    tttr = sum_col(year_df, "luas_tt_tr_ha")
    produktivitas = produksi * 1000 / tm if pd.notna(tm) and tm > 0 else None
    prev_produksi = sum_col(prev_year_df, "produksi_ton") if not prev_year_df.empty else None
    prev_tm = sum_col(prev_year_df, "luas_tm_ha") if not prev_year_df.empty else None
    prev_prod = prev_produksi * 1000 / prev_tm if pd.notna(prev_tm) and prev_tm > 0 else None
    flagged = int(year_df["status_data"].str.upper().str.contains("CEK|BELUM", na=False).sum())

    a, b, c, d = st.columns(4)
    a.metric("Kabupaten/Kota", fmt(wilayah_count, 0))
    b.metric("Total Produksi", f"{fmt(produksi, 2)} ton", metric_delta(produksi, prev_produksi))
    c.metric("Luas Tanaman Menghasilkan", f"{fmt(tm, 2)} ha")
    d.metric("Produktivitas Hitung", f"{fmt(produktivitas, 2)} kg/ha", metric_delta(produktivitas, prev_prod))
    e, f, g = st.columns(3)
    e.metric("Luas TBM", f"{fmt(tbm, 2)} ha")
    f.metric("Luas TT/TR", f"{fmt(tttr, 2)} ha")
    g.metric("Catatan Perlu Ditinjau", fmt(flagged, 0))

    st.markdown("---")
    left, right = st.columns([1.35, 1])
    with left:
        st.markdown('<div class="section-title">Kontributor Produksi Terbesar</div>', unsafe_allow_html=True)
        top = year_df.dropna(subset=["produksi_ton"]).nlargest(10, "produksi_ton").sort_values("produksi_ton")
        if not top.empty:
            fig = px.bar(
                top, x="produksi_ton", y="nama_wilayah", orientation="h",
                text="produksi_ton", color="produksi_ton",
                color_continuous_scale=["#B9D8C2", GREEN],
                labels={"produksi_ton": "Produksi (ton)", "nama_wilayah": ""}
            )
            fig.update_traces(texttemplate="%{text:,.1f}", textposition="outside", cliponaxis=False)
            fig.update_layout(coloraxis_showscale=False, yaxis_title=None, xaxis_title="Ton")
            st.plotly_chart(make_chart(fig, 420), use_container_width=True)
        else:
            st.info("Belum ada angka produksi untuk filter ini.")
    with right:
        st.markdown('<div class="section-title">Komposisi Luas Areal</div>', unsafe_allow_html=True)
        land = pd.DataFrame({
            "Kategori": ["Tanaman Menghasilkan", "Tanaman Belum Menghasilkan", "Tanaman Tua/Rusak"],
            "Luas (ha)": [tm, tbm, tttr]
        }).dropna()
        land = land[land["Luas (ha)"] > 0]
        if not land.empty:
            fig = px.pie(
                land, names="Kategori", values="Luas (ha)", hole=.62,
                color="Kategori",
                color_discrete_map={
                    "Tanaman Menghasilkan": GREEN,
                    "Tanaman Belum Menghasilkan": ORANGE,
                    "Tanaman Tua/Rusak": "#9BA8A0"
                }
            )
            fig.update_traces(textposition="outside", textinfo="percent")
            st.plotly_chart(make_chart(fig, 420), use_container_width=True)
        else:
            st.info("Komposisi luas areal belum tersedia.")

    st.markdown('<div class="section-title">Sorotan Data</div>', unsafe_allow_html=True)
    if not year_df.empty and year_df["produksi_ton"].notna().any():
        best = year_df.loc[year_df["produksi_ton"].idxmax()]
        low = year_df.loc[year_df["produksi_ton"].idxmin()]
        x, y = st.columns(2)
        with x:
            st.markdown(f'<div class="info-card"><h4>🏆 Produksi tertinggi</h4><p><b>{best["nama_wilayah"]}</b><br>{fmt(best["produksi_ton"], 2)} ton pada {selected_year}</p></div>', unsafe_allow_html=True)
        with y:
            st.markdown(f'<div class="info-card"><h4>📌 Produksi terendah</h4><p><b>{low["nama_wilayah"]}</b><br>{fmt(low["produksi_ton"], 2)} ton pada {selected_year}</p></div>', unsafe_allow_html=True)
    else:
        st.info("Belum cukup data untuk membuat sorotan wilayah.")
    st.caption("Produktivitas hitung pada ringkasan dihitung dari total produksi ÷ total luas tanaman menghasilkan. Nilai sumber tetap tersedia pada halaman eksplorasi data.")

# =========================================================
# PAGE 2: REGIONAL COMPARISON
# =========================================================
elif page == "Perbandingan Wilayah":
    st.markdown('<div class="section-title">Perbandingan Kabupaten/Kota</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Bandingkan indikator utama antarwilayah pada tahun terpilih.</div>', unsafe_allow_html=True)
    indicator_map = {
        "Produksi (ton)": "produksi_ton",
        "Produktivitas sumber (kg/ha)": "produktivitas_kg_ha",
        "Luas TM (ha)": "luas_tm_ha",
        "Luas TBM (ha)": "luas_tbm_ha",
        "Luas TT/TR (ha)": "luas_tt_tr_ha"
    }
    chosen_label = st.selectbox("Indikator yang dibandingkan", list(indicator_map.keys()))
    chosen_col = indicator_map[chosen_label]
    comp = year_df[["nama_wilayah", chosen_col, "status_data"]].dropna(subset=[chosen_col]).sort_values(chosen_col, ascending=False)
    if not comp.empty:
        chart_type = st.radio("Bentuk grafik", ["Batang horizontal", "Treemap"], horizontal=True)
        if chart_type == "Batang horizontal":
            fig = px.bar(
                comp.sort_values(chosen_col), x=chosen_col, y="nama_wilayah",
                orientation="h", color=chosen_col,
                color_continuous_scale=["#C9DFCF", GREEN],
                labels={chosen_col: chosen_label, "nama_wilayah": ""}
            )
            fig.update_layout(coloraxis_showscale=False, yaxis_title=None)
        else:
            fig = px.treemap(comp, path=["nama_wilayah"], values=chosen_col, color=chosen_col,
                             color_continuous_scale=["#D9E9DC", GREEN])
        st.plotly_chart(make_chart(fig, 520), use_container_width=True)
        st.markdown("#### Peringkat wilayah")
        rank = comp.reset_index(drop=True)
        rank.insert(0, "Peringkat", range(1, len(rank)+1))
        rank.columns = ["Peringkat", "Kabupaten/Kota", chosen_label, "Status data"]
        st.dataframe(rank, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada nilai yang dapat dibandingkan untuk indikator ini.")

# =========================================================
# PAGE 3: TREN
# =========================================================
elif page == "Tren & Perkembangan":
    st.markdown('<div class="section-title">Tren & Perkembangan Tahunan</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Lihat perubahan indikator dari tahun ke tahun untuk wilayah yang dipilih.</div>', unsafe_allow_html=True)
    trend_options = {
        "Total produksi (ton)": "produksi_ton",
        "Produktivitas hitung (kg/ha)": "produktivitas_rata2",
        "Luas TM (ha)": "luas_tm_ha",
        "Luas TBM (ha)": "luas_tbm_ha",
        "Luas TT/TR (ha)": "luas_tt_tr_ha"
    }
    trend_label = st.selectbox("Pilih indikator tren", list(trend_options.keys()))
    trend_col = trend_options[trend_label]
    fig = px.line(
        annual.dropna(subset=[trend_col]), x="tahun", y=trend_col, markers=True,
        labels={"tahun": "Tahun", trend_col: trend_label},
        color_discrete_sequence=[GREEN]
    )
    fig.update_traces(line_width=4, marker_size=11, marker_color=ORANGE,
                      fill="tozeroy", fillcolor="rgba(63,139,98,.10)")
    st.plotly_chart(make_chart(fig, 420), use_container_width=True)

    if len(annual.dropna(subset=[trend_col])) >= 2:
        trend_data = annual.dropna(subset=[trend_col]).copy()
        trend_data["Perubahan (%)"] = trend_data[trend_col].pct_change() * 100
        trend_data["Perubahan (%)"] = trend_data["Perubahan (%)"].round(2)
        st.markdown("#### Ringkasan perubahan")
        st.dataframe(
            trend_data[["tahun", trend_col, "Perubahan (%)"]].rename(columns={"tahun": "Tahun", trend_col: trend_label}),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Data minimal dua tahun dibutuhkan untuk menghitung perubahan.")

    st.markdown("#### Bandingkan dua tahun")
    year_choices = sorted(annual["tahun"].dropna().astype(int).unique().tolist())
    if len(year_choices) >= 2:
        c1, c2 = st.columns(2)
        with c1:
            y1 = st.selectbox("Tahun awal", year_choices, index=0)
        with c2:
            y2 = st.selectbox("Tahun pembanding", year_choices, index=len(year_choices)-1)
        v1 = annual.loc[annual["tahun"] == y1, trend_col]
        v2 = annual.loc[annual["tahun"] == y2, trend_col]
        if not v1.empty and not v2.empty and pd.notna(v1.iloc[0]) and pd.notna(v2.iloc[0]):
            st.metric(f"{trend_label} • {y2}", fmt(v2.iloc[0], 2), metric_delta(v2.iloc[0], v1.iloc[0]))

# =========================================================
# PAGE 4: DATA EXPLORER
# =========================================================
elif page == "Eksplorasi Data":
    st.markdown('<div class="section-title">Eksplorasi Data Jambu Mete</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Cari, saring, periksa, dan unduh data yang tersimpan di database pusat.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        search_text = st.text_input("Cari kabupaten/kota", placeholder="Ketik nama wilayah...")
    with c2:
        years_filter = st.multiselect("Filter tahun", years, default=years)
    with c3:
        status_options = sorted(df["status_data"].dropna().unique().tolist())
        status_filter = st.multiselect("Status data", status_options, default=status_options)
    view = df[
        df["nama_wilayah"].str.contains(search_text, case=False, na=False)
        & df["tahun"].isin(years_filter)
        & df["status_data"].isin(status_filter)
    ].copy()
    display_cols = [
        "kode_wilayah", "nama_wilayah", "tahun", "produksi_ton",
        "produktivitas_kg_ha", "produktivitas_hitung",
        "luas_tm_ha", "luas_tbm_ha", "luas_tt_tr_ha", "status_data"
    ]
    display_cols = [c for c in display_cols if c in view.columns]
    st.caption(f"Menampilkan {len(view)} baris data")
    st.dataframe(
        view[display_cols].sort_values(["nama_wilayah", "tahun"]),
        use_container_width=True, hide_index=True
    )
    csv = view[display_cols].to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Unduh hasil filter (CSV)", data=csv,
        file_name="data_jambu_mete_ntt_filtered.csv", mime="text/csv"
    )

# =========================================================
# PAGE 5: DATA QUALITY
# =========================================================
else:
    st.markdown('<div class="section-title">Pemeriksaan Kualitas Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Membantu menemukan baris yang perlu ditinjau sebelum data dianalisis lebih lanjut.</div>', unsafe_allow_html=True)
    status_counts = df["status_data"].value_counts(dropna=False).reset_index()
    status_counts.columns = ["Status", "Jumlah baris"]
    c1, c2 = st.columns([1, 1.2])
    with c1:
        fig = px.pie(status_counts, names="Status", values="Jumlah baris", hole=.55,
                     color_discrete_sequence=[GREEN, ORANGE, "#9BA8A0", "#C65B4B"])
        st.plotly_chart(make_chart(fig, 330), use_container_width=True)
    with c2:
        st.markdown("#### Rekap status data")
        st.dataframe(status_counts, use_container_width=True, hide_index=True)
        st.metric("Total baris", fmt(len(df), 0))

    flagged_rows = df[df["status_data"].str.upper().str.contains("CEK|BELUM|KOSONG", na=False)].copy()
    st.markdown("#### Baris yang perlu ditinjau")
    if flagged_rows.empty:
        st.success("Tidak ditemukan baris dengan status PERLU CEK atau BELUM DIPERIKSA.")
    else:
        quality_cols = [
            "kode_wilayah", "nama_wilayah", "tahun", "produksi_ton",
            "produktivitas_kg_ha", "status_data"
        ]
        st.warning(f"Terdapat {len(flagged_rows)} baris yang perlu diperiksa.")
        st.dataframe(flagged_rows[quality_cols].sort_values(["nama_wilayah", "tahun"]),
                     use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown(
    '<div class="small-note">Jambu Mete Data Center • Sumber: database pusat Neon PostgreSQL • '
    'Visualisasi bersifat deskriptif dan mengikuti data yang tersedia.</div>',
    unsafe_allow_html=True
)
'''

path = Path("/mnt/data/app_jambu_mete_ntt_redesign.py")
path.write_text(code, encoding="utf-8")
print(f"File berhasil dibuat: {path}")
