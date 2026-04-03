param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$SourcePy = "res_mods\mods\mod_wot_telegram_notifier.py",
    [string]$MetaXml = "packaging\meta.xml",
    [string]$WotVersion = "2.2.0.2",
    [string]$OutputRoot = "build\pyc_release",
    [string]$Python2Exe = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-Python2Path {
    param([string]$PreferredPath)

    $candidates = @()
    if ($PreferredPath) {
        $candidates += $PreferredPath
    }

    try {
        $pythonCmd = Get-Command python -ErrorAction Stop
        if ($pythonCmd -and $pythonCmd.Source) {
            $candidates += $pythonCmd.Source
        }
    } catch {
    }

    foreach ($candidate in $candidates) {
        if (-not $candidate) {
            continue
        }
        if (-not (Test-Path $candidate)) {
            continue
        }

        try {
            $major = & $candidate -c "import sys; print(sys.version_info[0])" 2>$null
            if ("$major".Trim() -eq "2") {
                return (Resolve-Path $candidate).Path
            }
        } catch {
        }
    }

    throw "Python 2 interpreter not found. Set -Python2Exe explicitly."
}

function Remove-DirectorySafe {
    param([string]$PathToRemove)

    if (-not (Test-Path $PathToRemove)) {
        return
    }

    for ($i = 0; $i -lt 5; $i++) {
        try {
            Remove-Item -LiteralPath $PathToRemove -Recurse -Force
            return
        } catch {
            Start-Sleep -Milliseconds 200
        }
    }

    Write-Warning ("Could not remove temporary directory: {0}" -f $PathToRemove)
}

$sourcePath = Join-Path $ProjectRoot $SourcePy
$metaPath = Join-Path $ProjectRoot $MetaXml
$outputRootPath = Join-Path $ProjectRoot $OutputRoot

if (-not (Test-Path $sourcePath)) {
    throw "Source file not found: $sourcePath"
}
if (-not (Test-Path $metaPath)) {
    throw "Meta file not found: $metaPath"
}
if (-not (Test-Path $outputRootPath)) {
    New-Item -ItemType Directory -Path $outputRootPath -Force | Out-Null
}

[xml]$metaXmlDoc = Get-Content -Raw -LiteralPath $metaPath
$metaVersion = "$($metaXmlDoc.root.version)"
if (-not $metaVersion) {
    throw "Could not read <version> from $metaPath"
}

$sourceText = [System.IO.File]::ReadAllText($sourcePath)
if ($sourceText.IndexOf('__MOD_VERSION__') -lt 0) {
    throw "MOD_VERSION placeholder '__MOD_VERSION__' not found in $sourcePath"
}
$patchedSourceText = $sourceText.Replace('__MOD_VERSION__', $metaVersion)

$python2Path = Resolve-Python2Path -PreferredPath $Python2Exe

$tmpRoot = Join-Path $outputRootPath "_tmp_compile"
Remove-DirectorySafe -PathToRemove $tmpRoot
New-Item -ItemType Directory -Path $tmpRoot -Force | Out-Null

$patchedPyPath = Join-Path $tmpRoot "mod_wot_telegram_notifier.py"
$compiledPycPath = Join-Path $tmpRoot "mod_wot_telegram_notifier.pyc"
[System.IO.File]::WriteAllText($patchedPyPath, $patchedSourceText, [System.Text.Encoding]::UTF8)

$compileScriptPath = Join-Path $tmpRoot "compile_pyc.py"
$compileScript = @"
import py_compile
import sys
src = sys.argv[1]
dst = sys.argv[2]
py_compile.compile(src, cfile=dst, dfile='mod_wot_telegram_notifier.py')
"@
[System.IO.File]::WriteAllText($compileScriptPath, $compileScript, [System.Text.Encoding]::ASCII)

& $python2Path $compileScriptPath $patchedPyPath $compiledPycPath

if (-not (Test-Path $compiledPycPath)) {
    throw "Compilation failed: $compiledPycPath was not created"
}

$targets = @(
    "res_mods\$WotVersion\scripts\client\gui\mods\mod_wot_telegram_notifier.pyc"
)

foreach ($relativeTarget in $targets) {
    $targetPath = Join-Path $outputRootPath $relativeTarget
    $targetDir = Split-Path -Parent $targetPath
    if (-not (Test-Path $targetDir)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    Copy-Item -LiteralPath $compiledPycPath -Destination $targetPath -Force
    Write-Host ("Created runtime file: {0}" -f $targetPath)
}

$legacyClientTarget = Join-Path $outputRootPath ("res_mods\{0}\scripts\client\mods\mod_wot_telegram_notifier.pyc" -f $WotVersion)
if (Test-Path $legacyClientTarget) {
    Remove-Item -LiteralPath $legacyClientTarget -Force
    Write-Host ("Removed legacy runtime file: {0}" -f $legacyClientTarget)
}

Remove-DirectorySafe -PathToRemove $tmpRoot
Write-Host ("Python 2 used: {0}" -f $python2Path)
Write-Host ("Release version: {0}" -f $metaVersion)
Write-Host ("WoT version path: {0}" -f $WotVersion)
