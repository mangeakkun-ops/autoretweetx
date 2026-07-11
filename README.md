# AutoretweetX

AutoretweetX adalah automation lokal berbasis **Python + Selenium** untuk memonitor tweet terbaru dari beberapa akun target X/Twitter dan melakukan retweet memakai beberapa akun retweeter yang login dengan cookies masing-masing.

> Gunakan hanya untuk akun yang Anda miliki/kelola dan patuhi aturan X/Twitter. Otomasi yang terlalu agresif dapat membuat akun dibatasi. Default delay dibuat panjang agar perilaku lebih natural.

## Fitur

- Fleksibel untuk banyak akun target dan banyak akun retweeter melalui `config/accounts.json`.
- Tetap mendukung **cookies per akun** di folder `config/cookies/`.
- Retweet hanya untuk tweet yang belum tercatat di `data/retweet_history.json`.
- Delay acak antar siklus pengecekan agar tidak terlalu repetitif.
- Opsi `run_once`, `--once`, atau `--test` untuk menjalankan satu siklus saja saat testing.
- Progress bar sederhana saat mengecek target.
- Console log berwarna dengan `colorama` dan file log di `logs/autoretweetx.log`.
- Folder runtime `logs/` dan `data/` dibuat otomatis jika belum ada.
- Error handling lebih aman untuk cookies gagal, login expired, browser crash, dan selector yang berubah.
- Opsi proxy per akun tetap tersedia.

## Struktur Repository

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
logs/
  .gitkeep
data/
  .gitkeep
  retweet_history.json
requirements.txt
README.md
.gitignore
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

Pastikan **Google Chrome** sudah terinstall. Paket `undetected-chromedriver` akan menyiapkan driver yang kompatibel secara otomatis pada banyak environment.

## 3. Setup cookies untuk akun retweeter

Cara paling mudah adalah export cookies dari Chrome memakai extension exporter cookies.

1. Buka Chrome normal, login ke akun X/Twitter retweeter pertama.
2. Buka `https://x.com/home` dan pastikan akun benar-benar sudah login.
3. Install extension export cookies JSON, misalnya **Cookie-Editor** dari Chrome Web Store.
4. Buka extension tersebut saat berada di domain `x.com`.
5. Export cookies dalam format JSON.
6. Simpan file hasil export ke folder `config/cookies/` sesuai nama di `accounts.json`, contoh:
   - `config/cookies/akun_retweeter_1.json`
   - `config/cookies/akun_retweeter_2.json`
   - `config/cookies/akun_retweeter_3.json`
7. Ulangi untuk semua akun retweeter. Gunakan profile Chrome berbeda atau logout-login bergantian supaya cookies tidak tertukar.

Catatan penting:

- Jangan commit file cookies. `.gitignore` sudah mengabaikan `config/cookies/*.json`.
- Jika script gagal login, cookies kemungkinan expired atau salah akun. Export ulang cookies dari akun tersebut.
- Format JSON dari extension biasanya berisi list object cookies. Script mendukung field umum seperti `name`, `value`, `domain`, `path`, `expiry`, dan `expirationDate`.

## 4. Isi `config/accounts.json`

Contoh bawaan berisi beberapa retweeter dan target:

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

```json
{
  "headless": false,
  "browser_window_size": "1280,900",
  "disable_gpu": true,
  "run_once": false,
  "colored_console": true,
  "check_delay_minutes": {
    "min": 40,
    "max": 90
  },
  "per_account_pause_seconds": {
    "min": 3,
    "max": 8
  },
  "page_load_timeout_seconds": 45,
  "wait_timeout_seconds": 20,
  "action_delay_seconds": {
    "min": 2,
    "max": 6
  },
  "max_latest_tweets_per_target": 3,
  "retweet_history_path": "data/retweet_history.json",
  "log_file": "logs/autoretweetx.log"
}
```

Penjelasan singkat:

- `headless`: `false` untuk debugging awal agar browser terlihat; `true` untuk berjalan tanpa UI.
- `run_once`: `true` untuk satu siklus pengecekan saja, cocok untuk testing.
- `colored_console`: aktifkan/nonaktifkan warna log di terminal.
- `check_delay_minutes`: delay acak antar siklus.
- `per_account_pause_seconds`: jeda antar akun agar multi akun lebih stabil.
- `action_delay_seconds`: delay acak antar aksi klik.
- `max_latest_tweets_per_target`: jumlah tweet terbaru yang dibaca per target.
- `log_file`: lokasi file log runtime.

## 6. Menjalankan script

Setelah cookies tersimpan dan config sudah benar:

```bash
python main.py
```

Alur kerja script:

1. Membaca `config/accounts.json` dan `config/settings.json`.
2. Membuat folder `logs/`, `data/`, dan `config/cookies/` jika belum ada.
3. Membuka browser untuk setiap retweeter aktif.
4. Memuat cookies dari file JSON akun tersebut.
5. Memastikan akun berhasil login.
6. Mengecek tweet terbaru target aktif dengan progress bar sederhana.
7. Melakukan retweet jika tweet belum ada di history.
8. Menyimpan history retweet dan cookies terbaru.
9. Jika `run_once: false` dan tidak memakai `--once/--test`, menunggu delay acak sebelum siklus berikutnya.

Untuk berhenti, tekan:

```bash
Ctrl+C
```

## Mode testing satu kali

Untuk test tanpa loop panjang, pilih salah satu cara berikut. Cara paling praktis adalah memakai CLI flag:

```bash
python main.py --once
# atau
python main.py --test
```

Alternatif permanen via `config/settings.json`:

```json
"run_once": true
```

Jika sudah stabil, ubah kembali ke `false` agar bot berjalan berulang.

## Tips anti-detect sederhana

- Jangan gunakan delay yang terlalu pendek.
- Jangan menaruh terlalu banyak target dan retweeter sekaligus pada akun baru.
- Gunakan cookies akun yang valid dan stabil.
- Gunakan proxy hanya jika proxy tersebut berkualitas dan konsisten dengan lokasi akun.
- Untuk debugging awal, gunakan `headless: false` agar mudah melihat jika ada captcha, challenge, atau popup.

## Troubleshooting

- **Browser terbuka tetapi tidak login**: cookies expired, salah akun, atau format cookie tidak cocok. Export ulang cookies.
- **Cookie file belum ada**: cek nama `cookies_file` di `config/accounts.json` dan pastikan file berada di `config/cookies/`.
- **Browser gagal dibuat/crash**: pastikan Google Chrome terinstall dan update. Coba nonaktifkan proxy dulu.
- **Tidak menemukan tweet**: target protected, tidak ada tweet, koneksi/proxy lambat, atau selector X berubah.
- **Retweet gagal**: akun dibatasi, tweet tidak bisa diretweet, selector berubah, popup menghalangi klik, atau muncul verifikasi keamanan.
- **Proxy gagal**: coba jalankan tanpa proxy dahulu, lalu validasi proxy dengan browser biasa.

## Instruksi update untuk user lama

1. Pull/update repo terbaru.
2. Jalankan ulang install dependency karena ada dependency baru:

   ```bash
   pip install -r requirements.txt
   ```

3. Pastikan folder berikut ada, atau biarkan script membuatnya otomatis:
   - `logs/`
   - `data/`
   - `config/cookies/`
4. Cek `config/settings.json` dan sesuaikan nilai baru seperti `run_once`, `colored_console`, `per_account_pause_seconds`, dan `wait_timeout_seconds`.
5. Untuk testing aman, jalankan `python main.py --once` atau set `run_once: true`, lalu cek log.
6. Jika login gagal, export ulang cookies setiap akun retweeter.
