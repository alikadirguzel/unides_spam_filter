# Windows'ta Arka Planda Çalıştırma

## Yöntem 1: PowerShell Script (Önerilen)

### Kurulum ve Kullanım
```powershell
# Uygulamayı başlat
.\start.ps1

# Uygulamayı durdur
.\stop.ps1
```

**Not:** İlk çalıştırmada execution policy hatası alırsanız:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Yöntem 2: Batch Dosyası

### Kullanım
```cmd
# Uygulamayı başlat
start.bat

# Uygulamayı durdur
stop.bat
```

## Yöntem 3: Windows Task Scheduler (Otomatik Başlatma)

### 1. Task Scheduler'ı açın
- Windows tuşu + R → `taskschd.msc` → Enter

### 2. Yeni görev oluşturun
- "Create Basic Task" seçin
- İsim: "Spam Filter Flask App"
- Trigger: "When I log on" veya "When the computer starts"
- Action: "Start a program"
- Program: Python'un tam yolu (örn: `C:\Python311\python.exe`)
- Arguments: `app.py`
- Start in: Proje dizininizin tam yolu

### 3. Görevi kaydedin

## Log Dosyaları
- `spam_filter.log` - Standart çıktı
- `spam_filter_error.log` - Hata logları
- `spam_filter.pid` - Process ID dosyası

## Sorun Giderme

### PowerShell execution policy hatası
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port zaten kullanılıyor
```powershell
# Hangi process portu kullanıyor?
netstat -ano | findstr :5000

# Process'i durdur
taskkill /PID <PID> /F
```

### Python bulunamadı hatası
```powershell
# Python'un yüklü olup olmadığını kontrol edin
python --version

# PATH'e ekleyin veya tam yolu kullanın
```

### Virtual environment sorunları
```cmd
# Virtual environment oluştur
python -m venv .venv

# Aktif et (PowerShell)
.\.venv\Scripts\Activate.ps1

# Aktif et (CMD)
.venv\Scripts\activate.bat

# Bağımlılıkları yükle
pip install -r requirements.txt
```

## Environment Variables

PowerShell'de:
```powershell
$env:FLASK_DEBUG = "true"
$env:FLASK_PORT = "8080"
$env:FLASK_HOST = "127.0.0.1"
.\start.ps1
```

CMD'de:
```cmd
set FLASK_DEBUG=true
set FLASK_PORT=8080
set FLASK_HOST=127.0.0.1
start.bat
```

