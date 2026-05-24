# ETL Pipeline — Fashion Studio

Pipeline **ETL (Extract, Transform, Load)** sederhana yang melakukan *web scraping* katalog produk fashion dari [fashion-studio.dicoding.dev](https://fashion-studio.dicoding.dev/), membersihkan datanya, lalu menyimpannya ke **tiga repositori**: berkas CSV, database PostgreSQL, dan Google Sheets.

Proyek ini merupakan submission kelas *Belajar Fundamental Pemrosesan Data* — Dicoding.

---

## 🗂️ Struktur Proyek

```
submission-etl-pipeline/
├── main.py                 # Orkestrator pipeline (Extract → Transform → Load)
├── requirements.txt        # Daftar dependency
├── submission.txt          # Instruksi run, test, coverage, & URL Google Sheets
├── products.csv            # Hasil output tahap Load (CSV)
├── google-sheets-api.json  # Kredensial Service Account Google (JANGAN di-commit publik)
├── README.md
├── utils/
│   ├── extract.py          # Tahap Extract — scraping HTML
│   ├── transform.py        # Tahap Transform — pembersihan & konversi tipe data
│   └── load.py             # Tahap Load — simpan ke CSV / PostgreSQL / Google Sheets
└── tests/
    ├── test_extract.py
    ├── test_transform.py
    └── test_load.py
```

---

## 🔄 Alur Pipeline

### 1. Extract — [utils/extract.py](utils/extract.py)
Mengambil data dari 50 halaman katalog (`page1` s.d. `page50`).
- `fetching_content(url)` — mengunduh HTML mentah via `requests`.
- `extract_product_data(card)` — mem-parsing tiap `div.collection-card` dengan BeautifulSoup.
- `scrape_product(...)` — menelusuri semua halaman dan menambahkan `timestamp` waktu ekstraksi pada setiap produk.

### 2. Transform — [utils/transform.py](utils/transform.py)
Membersihkan data mentah dan mengonversi tipe (urutan langkah penting: buang baris kotor **sebelum** casting tipe):
- Membuang `Title` tidak valid (`"Unknown Product"`).
- Membuang `Price` kosong, lalu mengonversi `"$102.15"` → rupiah `float` (kurs **Rp16.000**).
- Membuang `Rating` tidak valid (`"Invalid Rating"`, `"Not Rated"`), lalu mengambil nilai numeriknya.
- `Colors`: `"3 Colors"` → `int` `3`.
- `Size` / `Gender`: menghapus prefix label.
- Membuang nilai *null* dan baris duplikat.

**Skema hasil akhir:**

| Kolom     | Tipe    | Contoh                       |
|-----------|---------|------------------------------|
| Title     | object  | `T-shirt 2`                  |
| Price     | float64 | `1634400.0`                  |
| Rating    | float64 | `3.9`                        |
| Colors    | int64   | `3`                          |
| Size      | object  | `M`                          |
| Gender    | object  | `Women`                      |
| timestamp | object  | `2026-05-24T19:02:00.123456` |

### 3. Load — [utils/load.py](utils/load.py)
Menyimpan DataFrame yang sudah bersih ke tiga tujuan:
- `store_to_csv(df)` → [products.csv](products.csv)
- `store_to_postgresql(df, db_url)` → tabel `fashion_products` (via SQLAlchemy)
- `store_to_google_sheets(df, spreadsheet_id)` → Google Sheets (via Google Sheets API)

---

## ⚙️ Prasyarat

- Python **3.12**
- [uv](https://docs.astral.sh/uv/) (opsional, package manager yang lebih cepat — bisa diganti `pip`)
- PostgreSQL berjalan (hanya jika ingin menguji tahap Load ke database)
- Berkas kredensial `google-sheets-api.json` (Service Account Google) — lihat bagian Konfigurasi

---

## 🚀 Cara Menjalankan

### Menggunakan uv (disarankan)

```bash
# 1. Buat & siapkan virtual environment
uv venv --python 3.12

# 2. Install dependency
uv pip install -r requirements.txt

# 3. Jalankan pipeline
uv run main.py
```

### Alternatif tanpa uv (pip biasa)

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 main.py
```

> `uv` dan `requirements.txt` tidak saling bertentangan — `uv` membaca format `requirements.txt` yang sama persis seperti `pip`, hanya jauh lebih cepat.

---

## 🔧 Konfigurasi

Sesuaikan variabel di bagian atas [main.py](main.py):

| Variabel            | Keterangan                                                     |
|---------------------|----------------------------------------------------------------|
| `DB_URL`            | Connection string PostgreSQL (`user:password@host:port/db`)    |
| `SPREADSHEET_ID`    | ID Google Sheets (bagian di antara `/d/` dan `/edit` pada URL) |
| `GOOGLE_CREDS_FILE` | Path berkas kredensial Service Account                         |
| `EXCHANGE_RATE`     | Kurs USD → IDR (default `16000`)                               |

### Menyiapkan Google Sheets API
1. Di [Google Cloud Console](https://console.cloud.google.com): buat project → **Enable** *Google Sheets API*.
2. **Create Credentials → Service Account**, lalu buat **key** format **JSON**.
3. Rename berkas menjadi `google-sheets-api.json` dan letakkan di root proyek.
4. **Penting:** buka berkas JSON, salin nilai `client_email`, lalu **Share** spreadsheet tujuan ke email tersebut dengan akses **Editor**. Tanpa langkah ini akan muncul error `403 PERMISSION_DENIED`.

---

## 🧪 Pengujian

```bash
# Menjalankan unit test
python3 -m pytest tests
# atau: uv run pytest tests

# Menjalankan test coverage
coverage run -m pytest tests
coverage report -m
# atau (pytest-cov): uv run pytest tests --cov=utils
```

---

## 🔐 Catatan Keamanan

`google-sheets-api.json` berisi *private key* Service Account.
- Jangan commit ke repositori publik — berkas ini sudah masuk `.gitignore`.
- Berkas ini disertakan dalam ZIP submission karena diminta oleh ketentuan Dicoding. Setelah proses penilaian selesai, disarankan untuk **menghapus / me-*rotate* key** tersebut di Google Cloud Console.
