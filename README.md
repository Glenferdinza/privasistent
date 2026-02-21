# Irma - Virtual Assistant

Asisten virtual berbasis voice command yang bisa bantu kamu ngerjain berbagai task di Windows.

## Project Structure

```
irma/
├── src/
│   ├── audio/
│   │   ├── speech_recognition.py      # Vosk speech recognition engine
│   │   ├── text_to_speech.py          # TTS with multi-language support
│   │   ├── voice_language_manager.py  # Language switching manager
│   │   └── whisper_recognition.py     # Whisper STT for Indonesian
│   ├── core/
│   │   ├── assistant.py                # Main assistant logic
│   │   ├── command_processor.py        # Command parsing & routing
│   │   ├── memory_manager.py           # RAM & resource management
│   │   └── context_manager.py          # Conversation context
│   ├── executors/
│   │   ├── browser_executor.py         # Web browsing automation
│   │   ├── file_executor.py            # File operations
│   │   ├── app_executor.py             # Application launcher
│   │   ├── screen_reader.py            # OCR screen reading
│   │   └── system_executor.py          # System commands
│   ├── security/
│   │   ├── zero_trust.py               # Zero-trust security model
│   │   ├── validator.py                # Input validation
│   │   └── audit_logger.py             # Security audit logging
│   ├── utils/
│   │   ├── helpers.py                  # Utility functions
│   │   └── logger.py                   # Logging configuration
│   ├── config.py                       # Central configuration
│   └── main.py                         # CLI entry point
├── web/
│   ├── app.py                          # Flask web server
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css               # Web UI styling
│   │   └── js/
│   │       └── chat.js                 # Frontend logic
│   └── templates/
│       └── index.html                  # Web interface
├── models/                             # Vosk/Whisper models (not in repo)
│   ├── vosk-model-small-en-us-0.15/   # English model
│   └── vosk-model-small-ru-0.22/      # Russian model
├── logs/                               # Application logs
│   ├── security_audit.log              # Security events
│   └── errors.log                      # Error tracking
├── database/                           # User data & training
│   └── training/                       # ML training data
├── config/                             # Configuration files
├── .env                                # Environment variables (not in repo)
├── .env.example                        # Environment template
├── .gitignore                          # Git ignore rules
├── requirements.txt                    # Python dependencies
├── validate_setup.py                   # Setup validator
├── test_whisper.py                     # Whisper testing suite
├── WHISPER_SETUP.md                    # Whisper setup guide
├── COMPLETE_SETUP_GUIDE.md             # Complete installation guide
├── MULTILANGUAGE_VOICE_GUIDE.md        # Voice language switching guide
└── README.md                           # This file
```

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

### 4. Download Voice Recognition Models

#### Option A: Vosk (Fast, Real-time)

Vosk cocok untuk quick commands dengan latency rendah. Available models:

1. Download dari [Vosk Models](https://alphacephei.com/vosk/models):
   - English: `vosk-model-small-en-us-0.15` (40MB) - Bisa recognize Indonesian dengan akurasi 60-70%
   - Russian: `vosk-model-small-ru-0.22` (45MB)
   
2. Extract ke folder `models/` di root project
3. Keep nama folder sesuai download

Note: Indonesian & Malay models tidak tersedia di Vosk. English model bisa digunakan sebagai workaround.

#### Option B: Whisper (Accurate, Multi-language) - RECOMMENDED untuk Indonesian

- `VOICE_ENGINE` - pilih `vosk`, `whisper`, atau `hybrid`
- `DEFAULT_VOICE_LANGUAGE` - bahasa default untuk Vosk (en/ru)
- `DEFAULT_WHISPER_LANGUAGE` - bahasa default untuk Whisper (id/ms/en/ru)
- `WHISPER_MODEL` - ukuran model Whisper (tiny/base/small/medium/large)
Whisper memberikan akurasi jauh lebih baik untuk bahasa Indonesia (85-95%).

Install Whisper:

```bash
pip install openai-whisper torch torchaudio
```

Model akan auto-download saat pertama kali digunakan. Pilihan model:
- `tiny` (75MB) - Fast, 70-75% accuracy
- `base` (145MB) - Balanced, 75-80% accuracy
- `small` (488MB) - RECOMMENDED, 85-90% accuracy
- `medium` (1.5GB) - High accuracy, 90-95%
- `large` (3GB) - Best accuracy, 95%+

Lihat [WHISPER_SETUP.md](WHISPER_SETUP.md) untuk panduan lengkap.

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
```Voice Recognition Engines

### Vosk vs Whisper

| Feature | Vosk | Whisper |
|---------|------|---------|
| Indonesian Support | 60-70% (via English model) | 85-95% (native) |
| Speed | Very fast (0.1s real-time) | Slower (2-3s latency) |
| Size | Small (40-45MB) | Medium (488MB recommended) |
| RAM Usage | Low (~40MB) | Medium (~1GB) |
| Best For | Quick commands, fast response | Accurate transcription, dictation |

### Hybrid Mode (Recommended)

Gunakan kedua engine untuk mendapatkan best of both worlds:
- Fast commands menggunakan Vosk (real-time)
- Accurate Indonesian menggunakan Whisper (high accuracy)

Set `VOICE_ENGINE=hybrid` di file `.env`.

Voice commands untuk switching:
- "switch to fast mode" - Gunakan Vosk
- "switch to accurate mode" - Gunakan Whisper

### Whisper Too Slow

Jika Whisper terlalu lambat:
1. Gunakan model lebih kecil: `WHISPER_MODEL=tiny` atau `base`
2. Reduce recording duration di code
3. Gunakan Vosk untuk quick commands, Whisper hanya untuk transcription

### Whisper Installation Failed
Additional Guides

- [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md) - Panduan lengkap setup dari awal hingga akhir
- [WHISPER_SETUP.md](WHISPER_SETUP.md) - Panduan instalasi dan penggunaan Whisper untuk Indonesian
- [MULTILANGUAGE_VOICE_GUIDE.md](MULTILANGUAGE_VOICE_GUIDE.md) - Panduan multi-language voice switching
- [LICENSE.txt](LICENSE.txt) - GPLv3 License details

## Testing

### Test Vosk Recognition

```bash
python -c "from src.audio.speech_recognition import SpeechRecognizer; r = SpeechRecognizer('en'); print(r.listen_once())"
```

### Test Whisper Recognition

```bash
python test_whisper.py
```

Pilih option 1 untuk basic test, atau 4 untuk compare Vosk vs Whisper.

## Catatan

- File `.env` jangan di-commit ke Git karena berisi konfigurasi personal
- Vosk models (40-45MB per language) tidak di-include di repo, harus download manual
- Whisper models (75MB-3GB) akan auto-download saat pertama kali digunakan
- Untuk Indonesian voice recognition, Whisper strongly recommended (85-95% vs 60-70% Vosk)
pip install torch torchaudio
pip install openai-whisper

# Atau gunakan CPU-only version (lebih kecil)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install openai-whisper
```

### High Memory Usage

Jika RAM usage tinggi:
1. Gunakan Vosk instead of Whisper (40MB vs 1GB)
2. Gunakan Whisper model lebih kecil (tiny: 75MB)
3. Set `VOICE_ENGINE=vosk` untuk disable Whisper
4. Enable auto cleanup: `AUTO_CLEANUP_ENABLED=true`

## Troubleshooting

### Vosk Model Not Found

Pastikan folder model ada di `models/` dan nama foldernya sesuai dengan yang dipake di config. Kalo beda, rename folder model atau update path di `src/config

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

Project ini menggunakan lisensi dari [GPLv3](LICENSE.txt). Check file LICENSE di repo tersebut untuk detail lengkap.

## Catatan

- File `.env` jangan di-commit ke Git karena berisi konfigurasi personal
- Vosk model filenya besar (50-1000MB tergantung model), makanya ga di-include di repo
- Untuk dokumentasi lengkap, check folder docs atau file markdown lainnya di project

---

Kalo ada issue atau pertanyaan, silakan buat issue di GitHub repo.
