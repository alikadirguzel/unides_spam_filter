@echo off
REM Spam Filter Flask Uygulamasını Arka Planda Başlatma Scripti (Windows Batch)

cd /d "%~dp0"

REM PID dosyası
set PID_FILE=spam_filter.pid
set LOG_FILE=spam_filter.log
set ERROR_LOG=spam_filter_error.log

REM Eğer zaten çalışıyorsa kontrol et
if exist "%PID_FILE%" (
    for /f %%i in (%PID_FILE%) do (
        tasklist /FI "PID eq %%i" 2>NUL | find /I /N "%%i">NUL
        if "%%ERRORLEVEL%%"=="0" (
            echo Uygulama zaten calisiyor (PID: %%i)
            exit /b 1
        ) else (
            del "%PID_FILE%"
        )
    )
)

REM Python'un yolunu kontrol et
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3
    ) else (
        echo Hata: Python bulunamadi!
        exit /b 1
    )
)

REM Virtual environment kontrolü
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Uygulamayı arka planda başlat
echo Flask uygulaması başlatılıyor...
start /B "" %PYTHON_CMD% app.py > "%LOG_FILE%" 2> "%ERROR_LOG%"

REM Process ID'yi almak için bir workaround
timeout /t 2 /nobreak >nul
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq %PYTHON_CMD%.exe" /FO LIST ^| findstr /I "PID"') do (
    echo %%a > "%PID_FILE%"
    echo Uygulama başlatıldı (PID: %%a)
    echo Log dosyası: %LOG_FILE%
    echo Hata log dosyası: %ERROR_LOG%
    echo Durdurmak için: stop.bat
    exit /b 0
)

echo Hata: Uygulama başlatılamadı. Hata logunu kontrol edin: %ERROR_LOG%
exit /b 1

