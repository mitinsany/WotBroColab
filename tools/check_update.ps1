param(
    [string]$GameRoot = (Get-Location).Path,
    [string]$VersionUrl = "https://mitinsany.github.io/WotBroColab/version.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pathsXml = Join-Path $GameRoot "paths.xml"
if (-not (Test-Path $pathsXml)) {
    throw "paths.xml not found in $GameRoot. Run from WoT game folder."
}

[xml]$xml = Get-Content -Raw -LiteralPath $pathsXml
$activeVersion = $null
foreach ($n in $xml.SelectNodes("//Path")) {
    $text = $n.InnerText
    if ($text -match "res_mods[/\\]([0-9.]+)") {
        $activeVersion = $Matches[1]
        break
    }
}
if (-not $activeVersion) {
    throw "Cannot detect active version from paths.xml"
}

$localManifestPath = Join-Path $GameRoot ("mods\\{0}\\wot_telegram_notifier_current.manifest.json" -f $activeVersion)
$localVersion = "unknown"
if (Test-Path $localManifestPath) {
    $local = Get-Content -Raw -LiteralPath $localManifestPath | ConvertFrom-Json
    if ($local.version) { $localVersion = "$($local.version)" }
}

$remote = Invoke-RestMethod -Uri $VersionUrl -TimeoutSec 10
$remoteVersion = "$($remote.version)"

Write-Host ("Active WoT version: {0}" -f $activeVersion)
Write-Host ("Local mod version: {0}" -f $localVersion)
Write-Host ("Remote mod version: {0}" -f $remoteVersion)

if ($localVersion -eq $remoteVersion -and $localVersion -ne "unknown") {
    Write-Host "Status: up-to-date"
} else {
    Write-Host "Status: update available"
    Write-Host "Run: git pull"
}
