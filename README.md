# Dashboard Data Jambu Mete NTT

Dashboard interaktif untuk data jambu mete Nusa Tenggara Timur periode 2022–2025.

## Teknologi
- Neon PostgreSQL sebagai database
- Python + Streamlit
- Pandas untuk pengolahan data
- Plotly untuk visualisasi

## Menjalankan di komputer sendiri
1. Install Python.
2. Buka terminal pada folder project.
3. Jalankan `pip install -r requirements.txt`.
4. Buat folder `.streamlit` (sudah tersedia) dan file `secrets.toml`.
5. Isi `secrets.toml` dengan format:
   ```toml
   [database]
   url = "PASTE_CONNECTION_STRING_NEON_DI_SINI"
   ```
6. Jalankan `streamlit run app.py`.

## Deploy
Unggah file project ke GitHub, lalu deploy repository tersebut melalui Streamlit Community Cloud. Tambahkan connection string Neon pada App settings > Secrets dengan format TOML di atas.

**Penting:** Jangan pernah mengunggah `secrets.toml`, password, atau connection string ke repository GitHub.
