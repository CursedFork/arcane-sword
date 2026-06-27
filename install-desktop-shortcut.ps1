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

$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "Arcane Sword.lnk"

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnkPath)
$sc.TargetPath = $pythonw
$sc.Arguments = '"' + $main + '"'
$sc.WorkingDirectory = $proj
if (Test-Path $icon) { $sc.IconLocation = $icon }
$sc.Description = "Arcane Sword - D&D 5e player companion"
$sc.WindowStyle = 1
$sc.Save()

Write-Host "Created desktop shortcut:"
Write-Host "  $lnkPath"
Write-Host "  -> $pythonw `"$main`""
Write-Host "Double-click 'Arcane Sword' on your Desktop to launch (no console window)."
