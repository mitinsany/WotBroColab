param(
    [string]$GameRoot = "D:\GAMES\World_of_Tanks_EU",
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$Python2Exe = "D:\SOFT\Python2.7\python.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-ActiveResModsVersion {
    param([string]$PathsXmlPath)

    if (-not (Test-Path $PathsXmlPath)) {
        throw "paths.xml not found: $PathsXmlPath"
    }

    [xml]$xml = Get-Content -Raw -LiteralPath $PathsXmlPath
    $value = $null
    $nodes = $xml.SelectNodes("//Path")

    foreach ($pathNode in $nodes) {
        $nodeValue = $pathNode.InnerText
        if ($nodeValue -match "res_mods[/\\]([0-9.]+)") {
            $value = $Matches[1]
            break
        }
    }

    if (-not $value) {
        throw "Could not detect active res_mods version from $PathsXmlPath"
    }

    return $value
}

$pathsXml = Join-Path $GameRoot "paths.xml"
$activeVersion = Get-ActiveResModsVersion -PathsXmlPath $pathsXml

$buildScript = Join-Path $ProjectRoot "scripts\build_wotmod.ps1"
$releaseRootRel = Join-Path "build" "pyc_release"
& $buildScript -ProjectRoot $ProjectRoot -WotVersion $activeVersion -OutputRoot $releaseRootRel -Python2Exe $Python2Exe

$releaseRoot = Join-Path $ProjectRoot $releaseRootRel
$sourceGuiPyc = Join-Path $releaseRoot ("res_mods\{0}\scripts\client\gui\mods\mod_wot_telegram_notifier.pyc" -f $activeVersion)
$sourceClientPyc = Join-Path $releaseRoot ("res_mods\{0}\scripts\client\mods\mod_wot_telegram_notifier.pyc" -f $activeVersion)

if (-not (Test-Path $sourceGuiPyc)) {
    throw "Missing built file: $sourceGuiPyc"
}
if (-not (Test-Path $sourceClientPyc)) {
    throw "Missing built file: $sourceClientPyc"
}

$targetGuiDir = Join-Path $GameRoot ("res_mods\{0}\scripts\client\gui\mods" -f $activeVersion)
$targetClientDir = Join-Path $GameRoot ("res_mods\{0}\scripts\client\mods" -f $activeVersion)
if (-not (Test-Path $targetGuiDir)) {
    New-Item -ItemType Directory -Path $targetGuiDir -Force | Out-Null
}
if (-not (Test-Path $targetClientDir)) {
    New-Item -ItemType Directory -Path $targetClientDir -Force | Out-Null
}

$targetGuiPyc = Join-Path $targetGuiDir "mod_wot_telegram_notifier.pyc"
$targetClientPyc = Join-Path $targetClientDir "mod_wot_telegram_notifier.pyc"
Copy-Item -LiteralPath $sourceGuiPyc -Destination $targetGuiPyc -Force
Copy-Item -LiteralPath $sourceClientPyc -Destination $targetClientPyc -Force
Write-Host "Updated runtime: $targetGuiPyc"
Write-Host "Updated runtime: $targetClientPyc"

$legacyGuiPy = Join-Path $targetGuiDir "mod_wot_telegram_notifier.py"
$legacyClientPy = Join-Path $targetClientDir "mod_wot_telegram_notifier.py"
foreach ($legacyPy in @($legacyGuiPy, $legacyClientPy)) {
    if (Test-Path $legacyPy) {
        Remove-Item -LiteralPath $legacyPy -Force
        Write-Host "Removed legacy source: $legacyPy"
    }
}

$legacyWotmod = Join-Path $GameRoot ("mods\{0}\wot_telegram_notifier_current.wotmod" -f $activeVersion)
if (Test-Path $legacyWotmod) {
    Remove-Item -LiteralPath $legacyWotmod -Force
    Write-Host "Removed legacy package: $legacyWotmod"
}

Write-Host ("Active version: {0}" -f $activeVersion)
