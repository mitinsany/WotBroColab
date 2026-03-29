param(
    [string]$GameRoot = "D:\GAMES\World_of_Tanks_EU"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ActiveResModsVersion {
    param([string]$PathsXmlPath)

    if (-not (Test-Path $PathsXmlPath)) {
        throw "paths.xml not found: $PathsXmlPath"
    }

    [xml]$xml = Get-Content -Raw -LiteralPath $PathsXmlPath
    $nodes = $xml.SelectNodes("//Path")
    foreach ($pathNode in $nodes) {
        $nodeValue = $pathNode.InnerText
        if ($nodeValue -match "res_mods[/\\]([0-9.]+)") {
            return $Matches[1]
        }
    }

    throw "Could not detect active res_mods version from $PathsXmlPath"
}

$activeVersion = Get-ActiveResModsVersion -PathsXmlPath (Join-Path $GameRoot "paths.xml")
$modsDir = Join-Path $GameRoot ("res_mods\{0}\scripts\client\gui\mods" -f $activeVersion)

if (-not (Test-Path $modsDir)) {
    Write-Host "Mods directory does not exist: $modsDir"
    exit 0
}

$removed = @()
$targets = @(
    (Join-Path $modsDir "mod_wot_telegram_notifier.pyc"),
    (Join-Path $modsDir "mod_wot_telegram_notifier.pyo"),
    (Join-Path $modsDir "mod_wot_telegram_notifier_test.py"),
    (Join-Path $modsDir "mod_wot_telegram_notifier_test.pyc"),
    (Join-Path $modsDir "mod_wot_telegram_notifier_debug.py"),
    (Join-Path $modsDir "mod_wot_telegram_notifier_debug.pyc")
)

foreach ($target in $targets) {
    if (Test-Path $target) {
        Remove-Item -LiteralPath $target -Force
        $removed += $target
    }
}

if ($removed.Count -eq 0) {
    Write-Host ("Nothing to clean in {0}" -f $modsDir)
} else {
    Write-Host "Removed files:"
    foreach ($item in $removed) {
        Write-Host (" - {0}" -f $item)
    }
}
