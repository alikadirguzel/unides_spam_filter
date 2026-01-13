#!/bin/bash
# Spam Filter Flask Uygulamasını Arka Planda Başlatma Scripti

# Proje dizinini bul
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

# PID dosyası
PID_FILE="$SCRIPT_DIR/spam_filter.pid"
LOG_FILE="$SCRIPT_DIR/spam_filter.log"
ERROR_LOG="$SCRIPT_DIR/spam_filter_error.log"

# Eğer zaten çalışıyorsa uyar
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "Uygulama zaten çalışıyor (PID: $OLD_PID)"
        exit 1
    else
        # Eski PID dosyasını temizle
        rm -f "$PID_FILE"
    fi
fi

# Python'un yolunu kontrol et
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Hata: Python bulunamadı!"
    exit 1
fi

# Virtual environment kontrolü
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Uygulamayı arka planda başlat
echo "Flask uygulaması başlatılıyor..."
nohup "$PYTHON_CMD" app.py >> "$LOG_FILE" 2>> "$ERROR_LOG" &
NEW_PID=$!

# PID'yi kaydet
echo $NEW_PID > "$PID_FILE"

# Kısa bir süre bekle ve kontrol et
sleep 2
if ps -p "$NEW_PID" > /dev/null 2>&1; then
    echo "Uygulama başarıyla başlatıldı (PID: $NEW_PID)"
    echo "Log dosyası: $LOG_FILE"
    echo "Hata log dosyası: $ERROR_LOG"
    echo "Durdurmak için: ./stop.sh veya kill $NEW_PID"
else
    echo "Hata: Uygulama başlatılamadı. Hata logunu kontrol edin: $ERROR_LOG"
    rm -f "$PID_FILE"
    exit 1
fi

