# Pumpshop KP Demo v2

Demo sintetis baru. Proyek lama tidak diubah. Arsitektur: GitHub privat menyimpan kode; Streamlit Community Cloud menjalankan Python/UI; Supabase Postgres menyimpan data online bersama.

## Role demo

`demo-tech` (Teknisi/client), `demo-admin` (Admin), `demo-superadmin` (Superadmin), `demo-viewer` (Viewer). Pemilik deployment menetapkan satu `DEMO_PASSWORD` melalui Secrets; password tidak ada di source/fixture. Akun ini simulasi, jangan dipakai untuk sistem nyata.

## Penyimpanan dan akses

Hosted mode memerlukan `SUPABASE_DB_URL`; tidak ada fallback SQLite jika secret itu kosong. SQLite hanya untuk uji lokal eksplisit dengan `ALLOW_LOCAL_SQLITE=1`. Perubahan menggunakan fungsi backend yang memvalidasi role; audit masuk tabel append-only. Label database tidak dianggap serial barang fisik. Stok pool dikelompokkan berdasarkan barang, pemilik, lokasi, dan kondisi.

## Menjalankan lokal

Python 3.11+; buat `.streamlit/secrets.toml` lokal (di-ignore Git):

```toml
ALLOW_LOCAL_SQLITE = "1"
DEMO_PASSWORD = "isi-sandi-demo-unik-minimal-12-karakter"
```

Lalu `python -m venv .venv`, aktifkan environment, `pip install -r requirements.txt`, dan `streamlit run streamlit_app.py`.

## Deploy

Ikuti `TUTORIAL_DEPLOY.md`. Terapkan `schema.sql` sekali di proyek Supabase kosong. Jangan commit Secrets, database lokal, atau workbook lapangan. Koneksi Supabase hanya dipakai server Streamlit; jangan pakai service key di browser.

## Keterbatasan demo

Data fixture fiktif dan tidak mewakili rekomendasi operasi. Dashboard menghitung catatan, bukan akar penyebab. Belum ada upload dokumen, autentikasi perusahaan/SSO, offline mode, RLS per end-user, atau operasi produksi.
