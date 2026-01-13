@echo off
REM Spam Filter Flask Uygulamasını Durdurma Scripti (Windows Batch)

cd /d "%~dp0"
set PID_FILE=spam_filter.pid

if not exist "%PID_FILE%" (
    echo PID dosyası bulunamadı. Uygulama çalışmıyor olabilir.
    exit /b 1
)

for /f %%i in (%PID_FILE%) do (
    tasklist /FI "PID eq %%i" 2>NUL | find /I /N "%%i">NUL
    if "%%ERRORLEVEL%%"=="0" (
        echo Uygulama durduruluyor (PID: %%i)...
        taskkill /PID %%i /F >nul 2>&1
        timeout /t 2 /nobreak >nul
        del "%PID_FILE%"
        echo Uygulama durduruldu.
    ) else (
        echo Uygulama zaten durmuş.
        del "%PID_FILE%"
    )
)

