# Spam Filter Flask Uygulamasını Durdurma Scripti (PowerShell)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidFile = Join-Path $ScriptDir "spam_filter.pid"

if (-not (Test-Path $PidFile)) {
    Write-Host "PID dosyası bulunamadı. Uygulama çalışmıyor olabilir." -ForegroundColor Yellow
    exit 1
}

$Pid = Get-Content $PidFile

try {
    $Process = Get-Process -Id $Pid -ErrorAction Stop
    Write-Host "Uygulama durduruluyor (PID: $Pid)..." -ForegroundColor Yellow
    
    # Önce normal şekilde durdurmayı dene
    Stop-Process -Id $Pid -ErrorAction Stop
    
    # 5 saniye bekle
    Start-Sleep -Seconds 5
    
    # Hala çalışıyorsa force kill
    $Process = Get-Process -Id $Pid -ErrorAction SilentlyContinue
    if ($Process) {
        Write-Host "Uygulama durmuyor, zorla kapatılıyor..." -ForegroundColor Red
        Stop-Process -Id $Pid -Force -ErrorAction Stop
    }
    
    Remove-Item $PidFile -Force
    Write-Host "Uygulama durduruldu." -ForegroundColor Green
} catch {
    Write-Host "Uygulama zaten durmuş veya bulunamadı." -ForegroundColor Yellow
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

