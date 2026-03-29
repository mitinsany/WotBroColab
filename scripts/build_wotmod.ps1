param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$SourcePy = "res_mods\mods\mod_wot_telegram_notifier.py",
    [string]$MetaXml = "packaging\meta.xml",
    [string]$OutputFile = "build\wot_telegram_notifier_current.wotmod"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$sourcePath = Join-Path $ProjectRoot $SourcePy
$metaPath = Join-Path $ProjectRoot $MetaXml
$outputPath = Join-Path $ProjectRoot $OutputFile
$outputDir = Split-Path -Parent $outputPath

if (-not (Test-Path $sourcePath)) {
    throw "Source file not found: $sourcePath"
}
if (-not (Test-Path $metaPath)) {
    throw "Meta file not found: $metaPath"
}
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

if (Test-Path $outputPath) {
    Remove-Item -LiteralPath $outputPath -Force
}

$archivePath = [System.IO.Path]::GetFullPath($outputPath)
$sourceContent = [System.IO.File]::ReadAllText($sourcePath)
$metaContent = [System.IO.File]::ReadAllText($metaPath)

$fs = [System.IO.File]::Open($archivePath, [System.IO.FileMode]::CreateNew)
$zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create, $false)

try {
    $entryScript = $zip.CreateEntry("scripts/client/gui/mods/mod_wot_telegram_notifier.py", [System.IO.Compression.CompressionLevel]::NoCompression)
    $s1 = $entryScript.Open()
    $w1 = New-Object System.IO.StreamWriter($s1, [System.Text.Encoding]::UTF8)
    try { $w1.Write($sourceContent) } finally { $w1.Dispose(); $s1.Dispose() }

    $entryMeta = $zip.CreateEntry("meta.xml", [System.IO.Compression.CompressionLevel]::NoCompression)
    $s2 = $entryMeta.Open()
    $w2 = New-Object System.IO.StreamWriter($s2, [System.Text.Encoding]::UTF8)
    try { $w2.Write($metaContent) } finally { $w2.Dispose(); $s2.Dispose() }
}
finally {
    $zip.Dispose()
    $fs.Dispose()
}

Write-Host "Created wotmod: $archivePath"