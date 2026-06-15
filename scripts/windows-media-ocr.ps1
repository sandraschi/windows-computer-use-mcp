param([string]$ImagePath)
# Windows Media OCR — uses built-in WinRT API via Windows PowerShell.
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Media.Ocr.OcrEngine,Windows.Media.Ocr,ContentType=WindowsRuntime] | Out-Null
[Windows.Globalization.Language,Windows.Foundation,ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] | Out-Null

$lang = New-Object Windows.Globalization.Language "en"
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
if ($engine -eq $null) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}
if ($engine -eq $null) { Write-Error "No OCR engine"; exit 1 }

$path = Resolve-Path $ImagePath
$asTask = [System.Runtime.InteropServices.WindowsRuntime.WindowsRuntimeSystemExtensions]

$op = [Windows.Storage.StorageFile]::GetFileFromPathAsync($path)
$t = $asTask::AsTask($op, [System.Threading.CancellationToken]::None)
[System.Threading.Tasks.Task]::WaitAll($t) | Out-Null
$file = $t.Result

$op2 = $file.OpenReadAsync()
$t2 = $asTask::AsTask($op2, [System.Threading.CancellationToken]::None)
[System.Threading.Tasks.Task]::WaitAll($t2) | Out-Null
$stream = $t2.Result

$op3 = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)
$t3 = $asTask::AsTask($op3, [System.Threading.CancellationToken]::None)
[System.Threading.Tasks.Task]::WaitAll($t3) | Out-Null
$decoder = $t3.Result

$op4 = $decoder.GetSoftwareBitmapAsync()
$t4 = $asTask::AsTask($op4, [System.Threading.CancellationToken]::None)
[System.Threading.Tasks.Task]::WaitAll($t4) | Out-Null
$bmp = $t4.Result

$op5 = $engine.RecognizeAsync($bmp)
$t5 = $asTask::AsTask($op5, [System.Threading.CancellationToken]::None)
[System.Threading.Tasks.Task]::WaitAll($t5) | Out-Null
$result = $t5.Result

$lines = @()
foreach ($line in $result.Lines) {
    $lines += $line.Text
}
Write-Output ($lines -join "`n")
