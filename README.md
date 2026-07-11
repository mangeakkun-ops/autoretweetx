# AutoretweetX

AutoretweetX adalah automation lokal berbasis Python + Selenium untuk memonitor tweet terbaru dari beberapa akun target X/Twitter dan melakukan retweet memakai beberapa akun retweeter yang login dengan cookies masing-masing.

> Gunakan hanya untuk akun yang Anda miliki/kelola dan patuhi aturan X/Twitter. Otomasi yang agresif dapat membuat akun dibatasi. Default delay dibuat panjang (40-90 menit) agar penggunaan lebih natural.

## Fitur

- Fleksibel untuk N akun retweeter dan M akun target melalui `config/accounts.json`.
- Login akun retweeter menggunakan file cookies JSON per akun.
- Monitor beberapa tweet terbaru dari semua target aktif.
- Retweet hanya untuk tweet yang belum tercatat di `data/retweet_history.json`.
- Delay acak 40-90 menit antar siklus pengecekan.
- Struktur proxy per akun sudah tersedia.
- Logging ke console dan file `logs/autoretweetx.log`.
- Jalankan dengan `python main.py`.
- Bisa dihentikan dengan `Ctrl+C`.

## Struktur Repository

```text
main.py
config/
  accounts.json
  settings.json
  cookies/
src/
  browser.py
  retweeter.py
  tracker.py
  utils.py
requirements.txt
README.md
.gitignore
data/retweet_history.json
```

## 1. Clone repo

```bash
git clone https://github.com/mangeakkun-ops/autoreweetx.git
cd autoreweetx
```

Jika folder lokal repo ini bernama `autoretweetx`, tetap bisa digunakan; yang penting Anda menjalankan perintah dari root project.

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

Catatan:

- Jangan commit file cookies. `.gitignore` sudah mengabaikan `config/cookies/*.json`.
- Jika script gagal login, cookies kemungkinan expired. Export ulang cookies dari akun tersebut.
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

## 5. Menjalankan script pertama kali

Setelah cookies tersimpan dan config sudah benar:

```bash
python main.py
```

Alur kerja script:

1. Membaca `config/accounts.json` dan `config/settings.json`.
2. Membuka browser untuk setiap retweeter aktif.
3. Memuat cookies dari file JSON akun tersebut.
4. Mengecek tweet terbaru target aktif.
5. Melakukan retweet jika tweet belum ada di `data/retweet_history.json`.
6. Menyimpan history retweet dan cookies terbaru.
7. Menunggu delay acak 40-90 menit sebelum siklus berikutnya.

Untuk berhenti, tekan:

```bash
Ctrl+C
```

## Konfigurasi delay dan logging

Edit `config/settings.json`:

```json
{
  "headless": false,
  "browser_window_size": "1280,900",
  "check_delay_minutes": {"min": 40, "max": 90},
  "page_load_timeout_seconds": 45,
  "action_delay_seconds": {"min": 2, "max": 6},
  "max_latest_tweets_per_target": 3,
  "retweet_history_path": "data/retweet_history.json",
  "log_file": "logs/autoretweetx.log"
}
```

Untuk debugging awal, biarkan `headless` bernilai `false` agar browser terlihat. Setelah stabil, Anda bisa mencoba `true`.

## Troubleshooting

- **Browser terbuka tetapi tidak login**: cookies expired atau file cookies salah akun. Export ulang cookies.
- **Tidak menemukan tweet**: X/Twitter mengubah struktur halaman, target protected, atau koneksi/proxy bermasalah.
- **Retweet gagal**: akun dibatasi, tweet tidak bisa diretweet, selector X berubah, atau muncul verifikasi keamanan.
- **Proxy gagal**: coba jalankan tanpa proxy dahulu, lalu validasi proxy dengan browser biasa.
