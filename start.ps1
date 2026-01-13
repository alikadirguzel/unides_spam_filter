# Spam Filter Flask Uygulamasını Arka Planda Başlatma Scripti (PowerShell)

# Proje dizinini bul
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# PID dosyası
$PidFile = Join-Path $ScriptDir "spam_filter.pid"
$LogFile = Join-Path $ScriptDir "spam_filter.log"
$ErrorLog = Join-Path $ScriptDir "spam_filter_error.log"

# Eğer zaten çalışıyorsa uyar
if (Test-Path $PidFile) {
    $OldPid = Get-Content $PidFile
    $Process = Get-Process -Id $OldPid -ErrorAction SilentlyContinue
    if ($Process) {
        Write-Host "Uygulama zaten çalışıyor (PID: $OldPid)" -ForegroundColor Yellow
        exit 1
    } else {
        # Eski PID dosyasını temizle
        Remove-Item $PidFile -Force
    }
}

# Python'un yolunu kontrol et
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
} else {
    Write-Host "Hata: Python bulunamadı!" -ForegroundColor Red
    exit 1
}

# Virtual environment kontrolü
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .\.venv\Scripts\Activate.ps1
}

# Uygulamayı arka planda başlat
Write-Host "Flask uygulaması başlatılıyor..." -ForegroundColor Green

$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$ProcessInfo.FileName = $PythonCmd
$ProcessInfo.Arguments = "app.py"
$ProcessInfo.WorkingDirectory = $ScriptDir
$ProcessInfo.UseShellExecute = $false
$ProcessInfo.RedirectStandardOutput = $true
$ProcessInfo.RedirectStandardError = $true
$ProcessInfo.CreateNoWindow = $true

$Process = New-Object System.Diagnostics.Process
$Process.StartInfo = $ProcessInfo

# Output ve Error stream'lerini dosyalara yönlendir
$Process.Start() | Out-Null
$Process.BeginOutputReadLine()
$Process.BeginErrorReadLine()

# Output ve Error event handler'ları
$OutputBuilder = New-Object System.Text.StringBuilder
$ErrorBuilder = New-Object System.Text.StringBuilder

$Process.add_OutputDataReceived({
    param($sender, $e)
    if ($e.Data) {
        $OutputBuilder.AppendLine($e.Data) | Out-Null
        Add-Content -Path $LogFile -Value $e.Data
    }
})

$Process.add_ErrorDataReceived({
    param($sender, $e)
    if ($e.Data) {
        $ErrorBuilder.AppendLine($e.Data) | Out-Null
        Add-Content -Path $ErrorLog -Value $e.Data
    }
})

# PID'yi kaydet
$Process.Id | Out-File -FilePath $PidFile -Encoding ASCII

# Kısa bir süre bekle ve kontrol et
Start-Sleep -Seconds 2

if (-not $Process.HasExited) {
    Write-Host "Uygulama başarıyla başlatıldı (PID: $($Process.Id))" -ForegroundColor Green
    Write-Host "Log dosyası: $LogFile" -ForegroundColor Cyan
    Write-Host "Hata log dosyası: $ErrorLog" -ForegroundColor Cyan
    Write-Host "Durdurmak için: .\stop.ps1 veya Stop-Process -Id $($Process.Id)" -ForegroundColor Yellow
} else {
    Write-Host "Hata: Uygulama başlatılamadı. Hata logunu kontrol edin: $ErrorLog" -ForegroundColor Red
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    exit 1
}

