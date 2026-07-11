# AutoretweetX

AutoretweetX adalah automation lokal berbasis Python + Selenium untuk memonitor tweet terbaru dari beberapa akun target X/Twitter dan melakukan retweet memakai beberapa akun retweeter yang login dengan cookies masing-masing.

> Gunakan hanya untuk akun yang Anda miliki/kelola dan patuhi aturan X/Twitter. Otomasi yang agresif dapat membuat akun dibatasi. Default delay dibuat panjang (40-90 menit) agar penggunaan lebih natural.

## Fitur utama

- Fleksibel untuk N akun retweeter dan M akun target melalui `config/accounts.json`.
- Login akun retweeter menggunakan file cookies JSON per akun.
- Monitor beberapa tweet terbaru dari semua target aktif.
- Retweet hanya untuk tweet yang belum tercatat di `data/retweet_history.json`.
- Delay acak 40-90 menit antar siklus pengecekan.
- Cooldown acak antar akun retweeter.
- Struktur proxy per akun sudah tersedia.
- Logging lengkap ke console berwarna dan file `logs/autoretweetx.log`.
- Progress bar sederhana saat mengecek akun retweeter.
- Mode `run_once` untuk testing sekali jalan.
- Jalankan dengan `python main.py` dan hentikan aman dengan `Ctrl+C`.

## Struktur repository

```text
main.py
config/
  accounts.json
  settings.json
  cookies/
    .gitkeep
src/
  browser.py
  retweeter.py
  tracker.py
  utils.py
requirements.txt
README.md
.gitignore
data/
  .gitkeep
  retweet_history.json
logs/
  .gitkeep
```

## 1. Clone repo

```bash
git clone https://github.com/mangeakkun-ops/autoretweetx.git
cd autoretweetx
```

## 2. Install dependencies

Disarankan memakai virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
```

Pastikan Google Chrome sudah terinstall. Paket `undetected-chromedriver` akan menyiapkan driver yang kompatibel secara otomatis pada banyak environment.

## 3. Setup cookies untuk akun retweeter

Cara paling mudah adalah export cookies dari Chrome memakai extension exporter cookies.

1. Buka Chrome normal, login ke akun X/Twitter retweeter pertama.
2. Buka `https://x.com/home` dan pastikan akun benar-benar sudah login.
3. Install salah satu extension export cookies JSON, misalnya **Cookie-Editor** dari Chrome Web Store.
4. Buka extension tersebut saat berada di domain `x.com`.
5. Export cookies dalam format JSON.
6. Simpan file hasil export ke folder `config/cookies/` sesuai nama di `accounts.json`, contoh:
   - `config/cookies/akun_retweeter_1.json`
   - `config/cookies/akun_retweeter_2.json`
   - `config/cookies/akun_retweeter_3.json`
7. Ulangi untuk semua akun retweeter. Gunakan profile Chrome berbeda atau logout-login bergantian supaya cookies tidak tertukar.

Catatan penting:

- Jangan commit file cookies. `.gitignore` sudah mengabaikan `config/cookies/*.json`.
- Jika script gagal login, cookies kemungkinan expired, salah akun, atau X meminta verifikasi. Export ulang cookies setelah login manual.
- Format JSON dari extension biasanya berisi list object cookies. Script mendukung field umum seperti `name`, `value`, `domain`, `path`, `expiry`, dan `expirationDate`.

## 4. Isi `config/accounts.json`

Contoh bawaan berisi 5 retweeter dan 2 target:

```json
{
  "targets": [
    {"username": "OpenAI", "enabled": true},
    {"username": "XDevelopers", "enabled": true}
  ],
  "retweeters": [
    {
      "name": "akun_retweeter_1",
      "enabled": true,
      "cookies_file": "config/cookies/akun_retweeter_1.json",
      "proxy": null
    },
    {
      "name": "akun_retweeter_2",
      "enabled": true,
      "cookies_file": "config/cookies/akun_retweeter_2.json",
      "proxy": null
    },
    {
      "name": "akun_retweeter_3",
      "enabled": true,
      "cookies_file": "config/cookies/akun_retweeter_3.json",
      "proxy": "http://user:password@127.0.0.1:8080"
    },
    {
      "name": "akun_retweeter_4",
      "enabled": false,
      "cookies_file": "config/cookies/akun_retweeter_4.json",
      "proxy": null
    },
    {
      "name": "akun_retweeter_5",
      "enabled": false,
      "cookies_file": "config/cookies/akun_retweeter_5.json",
      "proxy": null
    }
  ]
}
```

Cara modifikasi:

- Tambah target baru dengan menambahkan object ke `targets`.
- Tambah akun retweeter baru dengan menambahkan object ke `retweeters`.
- Set `enabled: false` untuk menonaktifkan sementara akun tanpa menghapus konfigurasinya.
- Isi `proxy` dengan `null` jika tidak memakai proxy.
- Format proxy yang umum: `http://user:password@host:port` atau `http://host:port`.

## 5. Konfigurasi `config/settings.json`

Contoh setting yang tersedia:

```json
{
  "headless": false,
  "browser_window_size": "1280,900",
  "run_once": false,
  "check_delay_minutes": {"min": 40, "max": 90},
  "page_load_timeout_seconds": 45,
  "element_wait_timeout_seconds": 20,
  "action_delay_seconds": {"min": 2, "max": 6},
  "account_cooldown_seconds": {"min": 8, "max": 20},
  "max_latest_tweets_per_target": 3,
  "retweet_history_path": "data/retweet_history.json",
  "log_file": "logs/autoretweetx.log",
  "console_colors": true,
  "show_progress_bar": true,
  "save_cookies_after_run": true,
  "retry": {
    "browser_start_attempts": 2,
    "page_refresh_attempts": 1
  }
}
```

Rekomendasi pemula:

- Biarkan `headless: false` saat setup awal agar browser terlihat.
- Pakai `run_once: true` untuk mengetes 1 siklus tanpa menunggu 40-90 menit.
- Setelah stabil, ubah `run_once: false` untuk berjalan terus.
- Jangan membuat delay terlalu kecil karena dapat membuat akun mudah terkena limit.

## 6. Menjalankan script pertama kali

Setelah cookies tersimpan dan config sudah benar:

```bash
python main.py
```

Alur kerja script:

1. Membaca `config/accounts.json` dan `config/settings.json`.
2. Membuat folder runtime seperti `logs/`, `data/`, dan `config/cookies/` jika belum ada.
3. Membuka browser untuk setiap retweeter aktif.
4. Memuat cookies dari file JSON akun tersebut.
5. Mengecek apakah akun sudah login.
6. Membaca tweet terbaru target aktif.
7. Melakukan retweet jika tweet belum ada di `data/retweet_history.json`.
8. Menyimpan history retweet dan cookies terbaru.
9. Menunggu delay acak 40-90 menit sebelum siklus berikutnya, kecuali `run_once` aktif.

Untuk berhenti:

```bash
Ctrl+C
```

## 7. Instruksi update dari versi sebelumnya

Jika Anda sudah memakai versi awal repo ini, lakukan langkah berikut setelah pull/update:

```bash
git pull
pip install -r requirements.txt
```

Lalu cek file berikut:

1. Pastikan URL clone/documentation sudah memakai `autoretweetx`, bukan `autoreweetx`.
2. Tambahkan setting baru dari `config/settings.json` jika file lokal Anda pernah diedit manual.
3. Pastikan folder `logs/` dan `data/` ada. Script akan membuatnya otomatis, tetapi repo juga menyertakan `.gitkeep`.
4. Jalankan test sekali dengan mengubah `"run_once": true`.
5. Setelah berhasil, ubah kembali `"run_once": false` untuk mode normal.

## Troubleshooting

- **Browser tidak terbuka**: pastikan Google Chrome terinstall dan dependency sudah diinstall ulang.
- **Browser terbuka tetapi tidak login**: cookies expired, salah akun, atau X meminta verifikasi keamanan. Login manual lalu export ulang cookies.
- **Cookie JSON error**: pastikan file cookies berupa list JSON, bukan format Netscape `.txt`.
- **Tidak menemukan tweet**: target private, belum punya tweet, koneksi/proxy bermasalah, atau layout X berubah.
- **Retweet gagal**: tweet tidak bisa diretweet, akun terkena limit, selector X berubah, atau muncul verifikasi keamanan.
- **Proxy gagal**: coba jalankan tanpa proxy dahulu, lalu validasi proxy dengan browser biasa.
- **Log terlalu ramai**: cek file `logs/autoretweetx.log` untuk riwayat detail dan gunakan console hanya untuk progres utama.
