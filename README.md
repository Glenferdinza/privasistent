# Irma - Virtual Assistant

Asisten virtual berbasis voice command yang bisa bantu kamu ngerjain berbagai task di Windows.

## Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/your-username/irma.git
cd irma
```

### 2. Install Python Dependencies

Pastikan Python 3.8 atau lebih baru udah terinstall.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

Download Tesseract dari [sini](https://github.com/UB-Mannheim/tesseract/wiki) dan install dengan default settings. Pastikan waktu install, opsi "Add to PATH" di-checklist.

### 4. Download Vosk Model

1. Download model bahasa Indonesia dari [Vosk Models](https://alphacephei.com/vosk/models)
2. Extract ke folder `models/` di root project
3. Rename folder model jadi `vosk-model-small-id-0.22` atau sesuai nama model yang ada

### 5. Setup Environment Variables

Copy file `.env.example` jadi `.env`:

```bash
copy .env.example .env
```

Edit file `.env` sesuai kebutuhan, terutama bagian:
- `WHITELIST_DIRS` - folder yang boleh diakses Irma
- `ALLOWED_DOMAINS` - domain yang boleh dibuka

### 6. Validasi Setup

Jalankan validator untuk memastikan semua dependency terinstall dengan benar:

```bash
python validate_setup.py
```

Kalo ada yang error, ikutin instruksi yang muncul.

### 7. Jalankan Aplikasi

#### Mode GUI (Web Interface):

```bash
run_web.bat
```

Atau manual:

```bash
venv\Scripts\activate
python web/app.py
```

Browser bakal otomatis kebuka di `http://localhost:5000`

#### Mode CLI (Console):

```bash
venv\Scripts\activate
python src/main.py
```

### 8. Auto-Start di Windows (Optional)

Kalo mau Irma jalan otomatis waktu laptop nyala:

```bash
setup_autostart.bat
```

Jalankan sebagai Administrator. Untuk disable auto-start:

```bash
disable_autostart.bat
```

## Update GUI ke v2.0

Kalo masih pake GUI versi lama, jalankan:

```bash
update_gui.bat
```

Ini bakal update interface ke versi terbaru dengan dark mode dan chat management.

## Troubleshooting

### Vosk Model Not Found

Pastikan folder model ada di `models/` dan nama foldernya sesuai dengan yang dipake di code. Kalo beda, rename folder model atau update path di `src/audio/voice_recognition.py`.

### Port 5000 Already in Use

Kalo port 5000 udah dipake aplikasi lain, edit file `web/app.py` dan ganti port number di bagian paling bawah:

```python
app.run(host='0.0.0.0', port=5001, debug=False)
```

### Tesseract Not Found

Pastikan Tesseract udah terinstall dan ada di PATH. Cek dengan:

```bash
tesseract --version
```

Kalo belum kedetect, tambahkan path Tesseract manual di `src/executors/screen_reader.py`.

## License

Project ini pake lisensi yang sama dengan [privasistent](LICENSE.txt). Check file LICENSE di repo tersebut untuk detail lengkap.

## Catatan

- File `.env` jangan di-commit ke Git karena berisi konfigurasi personal
- Vosk model filenya besar (50-1000MB tergantung model), makanya ga di-include di repo
- Untuk dokumentasi lengkap, check folder docs atau file markdown lainnya di project

---

Kalo ada issue atau pertanyaan, silakan buat issue di GitHub repo.
