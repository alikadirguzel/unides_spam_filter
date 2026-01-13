# Linux'ta Arka Planda Çalıştırma

## Yöntem 1: Basit Shell Script (Önerilen)

### Kurulum
```bash
# Script dosyalarına çalıştırma izni ver
chmod +x start.sh stop.sh

# Uygulamayı başlat
./start.sh

# Uygulamayı durdur
./stop.sh
```

### Log Dosyaları
- `spam_filter.log` - Standart çıktı
- `spam_filter_error.log` - Hata logları
- `spam_filter.pid` - Process ID dosyası

## Yöntem 2: Systemd Service (Production için)

### 1. Service dosyasını düzenle
`spam-filter.service` dosyasındaki yolları kendi sisteminize göre güncelleyin:
- `/path/to/unides_spam_filter` → Projenizin tam yolu
- `User=%i` → Çalıştırmak istediğiniz kullanıcı adı (örn: `User=www-data`)

### 2. Service dosyasını kopyala
```bash
sudo cp spam-filter.service /etc/systemd/system/
```

### 3. Service'i etkinleştir ve başlat
```bash
# Systemd'yi yeniden yükle
sudo systemctl daemon-reload

# Service'i başlat
sudo systemctl start spam-filter

# Otomatik başlatmayı etkinleştir
sudo systemctl enable spam-filter

# Durumu kontrol et
sudo systemctl status spam-filter
```

### 4. Yönetim Komutları
```bash
# Durdur
sudo systemctl stop spam-filter

# Başlat
sudo systemctl start spam-filter

# Yeniden başlat
sudo systemctl restart spam-filter

# Durumu göster
sudo systemctl status spam-filter

# Logları görüntüle
sudo journalctl -u spam-filter -f
```

## Environment Variables

Uygulamayı özelleştirmek için environment variable'lar kullanabilirsiniz:

```bash
# Debug modunu açmak için
export FLASK_DEBUG=true

# Port değiştirmek için
export FLASK_PORT=8080

# Host değiştirmek için (varsayılan: 0.0.0.0)
export FLASK_HOST=127.0.0.1
```

## Sorun Giderme

### Uygulama başlamıyor
```bash
# Log dosyalarını kontrol edin
tail -f spam_filter_error.log

# Python ve bağımlılıkları kontrol edin
python3 --version
pip3 list | grep -i flask
```

### Port zaten kullanılıyor
```bash
# Hangi process portu kullanıyor?
sudo lsof -i :5000

# Process'i durdur
kill <PID>
```

### Virtual environment sorunları
```bash
# Virtual environment oluştur
python3 -m venv .venv

# Aktif et
source .venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt
```

