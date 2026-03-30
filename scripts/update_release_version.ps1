param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$WotVersion = "2.2.0.2",
    [string]$ReleaseDate = (Get-Date -Format "yyyy-MM-dd"),
    [string]$ChangelogShort = "Maintenance release"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$metaPath = Join-Path $ProjectRoot "packaging\meta.xml"
$versionPath = Join-Path $ProjectRoot "release\version.json"

if (-not (Test-Path $metaPath)) {
    throw "meta.xml not found: $metaPath"
}
if (-not (Test-Path $versionPath)) {
    throw "version.json not found: $versionPath"
}

[xml]$meta = Get-Content -Raw -LiteralPath $metaPath
$metaVersion = $meta.root.version
if (-not $metaVersion) {
    throw "Could not read <version> from $metaPath"
}

$json = Get-Content -Raw -LiteralPath $versionPath | ConvertFrom-Json
$json.version = "$metaVersion"
$json.release_date = "$ReleaseDate"
$json.wot_version = "$WotVersion"
$json.changelog_short = "$ChangelogShort"

($json | ConvertTo-Json -Depth 6) | Set-Content -LiteralPath $versionPath -Encoding UTF8 -NoNewline
Write-Host "Updated release metadata: $versionPath"