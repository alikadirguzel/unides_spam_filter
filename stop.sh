#!/bin/bash
# Spam Filter Flask Uygulamasını Durdurma Scripti

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_FILE="$SCRIPT_DIR/spam_filter.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "PID dosyası bulunamadı. Uygulama çalışmıyor olabilir."
    exit 1
fi

PID=$(cat "$PID_FILE")

if ps -p "$PID" > /dev/null 2>&1; then
    echo "Uygulama durduruluyor (PID: $PID)..."
    kill "$PID"
    
    # 5 saniye bekle
    sleep 5
    
    # Hala çalışıyorsa force kill
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Uygulama durmuyor, zorla kapatılıyor..."
        kill -9 "$PID"
    fi
    
    rm -f "$PID_FILE"
    echo "Uygulama durduruldu."
else
    echo "Uygulama zaten durmuş."
    rm -f "$PID_FILE"
fi

