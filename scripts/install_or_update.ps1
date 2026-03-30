param(
    [string]$GameRoot = "D:\GAMES\World_of_Tanks_EU",
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$SourcePy = "res_mods\mods\mod_wot_telegram_notifier.py",
    [string]$OutputWotmodName = "wot_telegram_notifier_current.wotmod"
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

$sourcePath = Join-Path $ProjectRoot $SourcePy
if (-not (Test-Path $sourcePath)) {
    throw "Source file not found: $sourcePath"
}
$metaPath = Join-Path $ProjectRoot "packaging\meta.xml"
if (-not (Test-Path $metaPath)) {
    throw "Meta file not found: $metaPath"
}
[xml]$metaXmlDoc = Get-Content -Raw -LiteralPath $metaPath
$metaVersion = "$($metaXmlDoc.root.version)"
if (-not $metaVersion) {
    throw "Could not read <version> from $metaPath"
}

$gameModsDirGui = Join-Path $GameRoot ("res_mods\{0}\scripts\client\gui\mods" -f $activeVersion)
if (-not (Test-Path $gameModsDirGui)) {
    New-Item -ItemType Directory -Path $gameModsDirGui -Force | Out-Null
}
$gameModsDirClient = Join-Path $GameRoot ("res_mods\{0}\scripts\client\mods" -f $activeVersion)
if (-not (Test-Path $gameModsDirClient)) {
    New-Item -ItemType Directory -Path $gameModsDirClient -Force | Out-Null
}

$gameSourceTargetGui = Join-Path $gameModsDirGui "mod_wot_telegram_notifier.py"
$gameSourceTargetClient = Join-Path $gameModsDirClient "mod_wot_telegram_notifier.py"
$sourceText = [System.IO.File]::ReadAllText($sourcePath)
$patchedSourceText = $sourceText.Replace('__MOD_VERSION__', $metaVersion)
[System.IO.File]::WriteAllText($gameSourceTargetGui, $patchedSourceText, [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText($gameSourceTargetClient, $patchedSourceText, [System.Text.Encoding]::UTF8)
Write-Host "Updated source: $gameSourceTargetGui"
Write-Host "Updated source: $gameSourceTargetClient"

$buildScript = Join-Path $ProjectRoot "scripts\build_wotmod.ps1"
$outputRel = Join-Path "build" $OutputWotmodName
& $buildScript -ProjectRoot $ProjectRoot -OutputFile $outputRel

$builtWotmod = Join-Path $ProjectRoot $outputRel
$gameWotmodDir = Join-Path $GameRoot ("mods\{0}" -f $activeVersion)
if (-not (Test-Path $gameWotmodDir)) {
    New-Item -ItemType Directory -Path $gameWotmodDir -Force | Out-Null
}
$gameWotmodTarget = Join-Path $gameWotmodDir $OutputWotmodName
Copy-Item -LiteralPath $builtWotmod -Destination $gameWotmodTarget -Force
Write-Host "Updated package: $gameWotmodTarget"

Write-Host ("Active version: {0}" -f $activeVersion)
