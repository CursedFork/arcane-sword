# Creates a Desktop shortcut that launches Arcane Sword with NO console window.
#
# It targets pythonw.exe (the windowed Python interpreter), so double-clicking
# the shortcut opens the app directly — no flashing command prompt.
#
# Run it once (right-click > "Run with PowerShell", or):
#     powershell -ExecutionPolicy Bypass -File install-desktop-shortcut.ps1
#
# Re-run it any time (e.g. after replacing icon.ico with a new logo).

$ErrorActionPreference = "Stop"

$proj = Split-Path -Parent $MyInvocation.MyCommand.Path
$main = Join-Path $proj "main.py"
$icon = Join-Path $proj "icon.ico"

# Locate pythonw.exe (windowed Python — runs without a console window).
$pythonw = $null
$cmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if ($cmd) {
    $pythonw = $cmd.Source
} else {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        $cand = Join-Path (Split-Path $py.Source) "pythonw.exe"
        if (Test-Path $cand) { $pythonw = $cand }
    }
}
if (-not $pythonw) {
    throw "Could not find pythonw.exe. Install Python 3.10+ (it ships with pythonw) and retry."
}

# Windows caches shortcut icons by file PATH, so overwriting icon.ico in place
# won't refresh the Desktop icon. Point the shortcut at a content-hashed copy:
# a new logo => new hash => new path Windows has never cached => it shows at once.
$iconLocation = $null
if (Test-Path $icon) {
    $hash = (Get-FileHash $icon -Algorithm MD5).Hash.Substring(0, 8).ToLower()
    $iconDir = Join-Path $proj "assets\shortcut-icon"
    New-Item -ItemType Directory -Force -Path $iconDir | Out-Null
    $iconLocation = Join-Path $iconDir "arcane-sword-$hash.ico"
    Copy-Item $icon $iconLocation -Force
    # Prune stale hashed copies from previous logos.
    Get-ChildItem $iconDir -Filter *.ico |
        Where-Object { $_.FullName -ne $iconLocation } |
        Remove-Item -Force -ErrorAction SilentlyContinue
}

$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "Arcane Sword.lnk"
if (Test-Path $lnkPath) { Remove-Item $lnkPath -Force }

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnkPath)
$sc.TargetPath = $pythonw
$sc.Arguments = '"' + $main + '"'
$sc.WorkingDirectory = $proj
if ($iconLocation) { $sc.IconLocation = $iconLocation }
$sc.Description = "Arcane Sword - D&D 5e player companion"
$sc.WindowStyle = 1
$sc.Save()

# Nudge Explorer to re-read the shortcut icon.
Start-Process ie4uinit.exe -ArgumentList '-show' -ErrorAction SilentlyContinue

Write-Host "Created desktop shortcut:"
Write-Host "  $lnkPath"
Write-Host "  -> $pythonw `"$main`""
Write-Host "Double-click 'Arcane Sword' on your Desktop to launch (no console window)."
