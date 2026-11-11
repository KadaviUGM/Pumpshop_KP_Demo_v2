# Tutorial deploy demo baru

## 1. Buat Supabase

1. Buat proyek baru bernama misalnya `pumpshop-kp-demo-v2`, region Sydney.
2. Gunakan proyek kosong untuk demo.
3. Buka **SQL Editor**, jalankan seluruh isi `schema.sql` satu kali.
4. Buka **Project Settings → Database → Connection string** dan pilih koneksi Postgres sesuai instruksi Supabase. Jangan salin password/connection string ke GitHub atau chat.

## 2. Buat GitHub privat

1. Buat repository privat baru, misalnya `pumpshop-kp-demo-v2`.
2. Ekstrak ZIP paket ini.
3. Unggah **isi folder hasil ekstrak** ke root repository sehingga `streamlit_app.py`, `requirements.txt`, `schema.sql`, `auth.py`, `db.py`, `README.md`, dan `assets/` berada di root/tempat yang disebut.
4. Pastikan `.streamlit/secrets.toml`, `.venv`, file SQLite, dan workbook tidak diunggah. Commit ke branch `main`.

## 3. Buat Streamlit Community Cloud app

1. Masuk ke Streamlit Community Cloud dengan GitHub dan pilih **Create app**.
2. Pilih repository baru, branch `main`, main file `streamlit_app.py`.
3. Buat app. Tentukan akses aplikasi sesuai kebutuhan demo; URL publik berarti siapapun dapat mencoba login, sehingga hanya data dummy.
4. Buka **App settings → Secrets** lalu isi `SUPABASE_DB_URL` (Postgres connection string) dan `DEMO_PASSWORD` (minimal 12 karakter, dummy unik). Jangan kirim nilainya ke chat.
5. Reboot app. App harus menolak start jika DB secret tidak ada; tidak boleh diam-diam pindah ke SQLite.

## 4. Verifikasi demo

Login bergantian dengan `demo-tech`, `demo-admin`, `demo-superadmin`, `demo-viewer` memakai sandi yang sama yang Anda tetapkan. Tambahkan satu kejadian sebagai teknisi, refresh/login viewer dan pastikan data terbaca; periksa audit; coba buka audit sebagai teknisi dan pastikan ditolak. Verifikasi perubahan tetap ada sesudah reboot app.

## Batas gratis dan troubleshooting

Streamlit Community Cloud dapat menidurkan app yang tidak aktif; Supabase Free dapat menjeda proyek dengan aktivitas rendah. Paket gratis cocok untuk demo, bukan jaminan SLA/operasi 24 jam. Jika error, kirim screenshot halaman deploy/log tanpa Secrets, URL koneksi, password, key, token, atau project credentials. Screenshot aman: repository file tree (tanpa file secret), form Create app, error merah yang sudah disensor, atau tabel hasil uji dummy.
