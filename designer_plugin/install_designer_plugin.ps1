param(
    [string]$DllPath = "",
    [switch]$DownloadLatest,
    [switch]$Launch,
    [switch]$Uninstall,
    [switch]$DebugPlugin
)

$ErrorActionPreference = 'Stop'
$releaseUrl = 'https://github.com/GUEThe/torr-craft/releases/latest/download/torr_craft_designer.dll'

function Get-PySideDirectory {
    $pyside = & python -c "import PySide2, pathlib; print(pathlib.Path(PySide2.__file__).parent)" 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $pyside) {
        throw "Cannot locate PySide2. Run this from the Python environment that provides pyside2-designer."
    }
    $pyside = ($pyside | Select-Object -First 1).Trim()
    if (-not (Test-Path -LiteralPath (Join-Path $pyside 'designer.exe'))) {
        throw "designer.exe not found under $pyside"
    }
    return $pyside
}

$pysideDir = Get-PySideDirectory
$pluginDir = Join-Path $pysideDir 'plugins\designer'
$target = Join-Path $pluginDir 'torr_craft_designer.dll'

if ($Uninstall) {
    if (Test-Path -LiteralPath $target) {
        Remove-Item -LiteralPath $target -Force
        Write-Host "Removed $target"
    } else {
        Write-Host "Plugin is not installed."
    }
    exit 0
}

if ($DownloadLatest) {
    $tempDir = Join-Path $env:TEMP ('torr-craft-designer-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    try {
        $download = Join-Path $tempDir 'torr_craft_designer.dll'
        Write-Host "Downloading latest Designer plugin from GitHub Releases..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $releaseUrl -OutFile $download -UseBasicParsing
        $DllPath = $download
    } catch {
        throw "Download failed: $($_.Exception.Message). Download torr_craft_designer.dll from the repository Releases page and pass -DllPath."
    }
}

if (-not $DllPath) {
    throw "Pass -DllPath <torr_craft_designer.dll> or -DownloadLatest."
}
$source = (Resolve-Path -LiteralPath $DllPath).Path
if (-not (Test-Path -LiteralPath $pluginDir)) {
    New-Item -ItemType Directory -Path $pluginDir -Force | Out-Null
}
Copy-Item -LiteralPath $source -Destination $target -Force
Write-Host "Installed Designer plugin:"
Write-Host "  $target"

if ($Launch) {
    $designer = Join-Path $pysideDir 'designer.exe'
    $env:QT_PLUGIN_PATH = Join-Path $pysideDir 'plugins'
    if ($DebugPlugin) {
        $env:QT_DEBUG_PLUGINS = '1'
    }
    Write-Host "Starting pyside2-designer..."
    & $designer
} else {
    Write-Host ""
    Write-Host "Start pyside2-designer, then look for 'Torr Craft 真空元件' in the Widget Box."
}
