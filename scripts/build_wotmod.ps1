param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$SourcePy = "res_mods\mods\mod_wot_telegram_notifier.py",
    [string]$MetaXml = "packaging\meta.xml",
    [string]$OutputFile = "build\wot_telegram_notifier_current.wotmod"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function New-Crc32Table {
    $table = New-Object 'UInt32[]' 256
    for ($i = 0; $i -lt 256; $i++) {
        $crc = [uint32]$i
        for ($j = 0; $j -lt 8; $j++) {
            if (($crc -band 1) -ne 0) {
                $crc = ([uint32]3988292384) -bxor ($crc -shr 1)
            } else {
                $crc = $crc -shr 1
            }
        }
        $table[$i] = $crc
    }
    return $table
}

function Get-Crc32([byte[]]$bytes, [uint32[]]$table) {
    $crc = [uint32]4294967295
    foreach ($b in $bytes) {
        $idx = ($crc -bxor [uint32]$b) -band 0xFF
        $crc = $table[$idx] -bxor ($crc -shr 8)
    }
    return [uint32]((-bnot $crc) -band 4294967295)
}

function Get-DosTimeDate([DateTime]$dt) {
    $sec = [int][Math]::Floor($dt.Second / 2)
    $dosTime = ($dt.Hour -shl 11) -bor ($dt.Minute -shl 5) -bor $sec
    $year = $dt.Year
    if ($year -lt 1980) { $year = 1980 }
    $dosDate = (($year - 1980) -shl 9) -bor ($dt.Month -shl 5) -bor $dt.Day
    return @([uint16]$dosTime, [uint16]$dosDate)
}

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
$patchedSourceBytes = [System.Text.Encoding]::UTF8.GetBytes($patchedSourceText)

$files = @()
$files += [PSCustomObject]@{
    Name = "scripts/client/gui/mods/mod_wot_telegram_notifier.py"
    Data = $patchedSourceBytes
}
$files += [PSCustomObject]@{
    Name = "scripts/client/mods/mod_wot_telegram_notifier.py"
    Data = $patchedSourceBytes
}
$files += [PSCustomObject]@{
    Name = "res/scripts/client/gui/mods/mod_wot_telegram_notifier.py"
    Data = $patchedSourceBytes
}
$files += [PSCustomObject]@{
    Name = "res/scripts/client/mods/mod_wot_telegram_notifier.py"
    Data = $patchedSourceBytes
}
$files += [PSCustomObject]@{
    Name = "meta.xml"
    Data = [System.IO.File]::ReadAllBytes($metaPath)
}

if (Test-Path $outputPath) {
    Remove-Item -LiteralPath $outputPath -Force
}

$table = New-Crc32Table
$now = Get-Date
$td = Get-DosTimeDate $now
$dosTime = $td[0]
$dosDate = $td[1]

$fullOutputPath = [System.IO.Path]::GetFullPath($outputPath)
$fs = [System.IO.File]::Open($fullOutputPath, [System.IO.FileMode]::CreateNew)
$bw = New-Object System.IO.BinaryWriter($fs)
$central = New-Object System.Collections.Generic.List[object]

try {
    foreach ($f in $files) {
        $nameBytes = [System.Text.Encoding]::ASCII.GetBytes($f.Name)
        $data = [byte[]]$f.Data
        $crc = Get-Crc32 $data $table
        $size = [uint32]$data.Length
        $offset = [uint32]$fs.Position

        # Local file header
        $bw.Write([uint32]0x04034B50)
        $bw.Write([uint16]20)      # version needed
        $bw.Write([uint16]0)       # flags
        $bw.Write([uint16]0)       # method: STORE (no compression)
        $bw.Write([uint16]$dosTime)
        $bw.Write([uint16]$dosDate)
        $bw.Write([uint32]$crc)
        $bw.Write([uint32]$size)
        $bw.Write([uint32]$size)
        $bw.Write([uint16]$nameBytes.Length)
        $bw.Write([uint16]0)       # extra length
        $bw.Write($nameBytes)
        $bw.Write($data)

        $central.Add([PSCustomObject]@{
            NameBytes = $nameBytes
            Crc = [uint32]$crc
            Size = [uint32]$size
            Offset = [uint32]$offset
        }) | Out-Null
    }

    $centralStart = [uint32]$fs.Position

    foreach ($c in $central) {
        # Central directory header
        $bw.Write([uint32]0x02014B50)
        $bw.Write([uint16]20)      # version made by
        $bw.Write([uint16]20)      # version needed
        $bw.Write([uint16]0)       # flags
        $bw.Write([uint16]0)       # method: STORE
        $bw.Write([uint16]$dosTime)
        $bw.Write([uint16]$dosDate)
        $bw.Write([uint32]$c.Crc)
        $bw.Write([uint32]$c.Size)
        $bw.Write([uint32]$c.Size)
        $bw.Write([uint16]$c.NameBytes.Length)
        $bw.Write([uint16]0)       # extra len
        $bw.Write([uint16]0)       # comment len
        $bw.Write([uint16]0)       # disk number start
        $bw.Write([uint16]0)       # internal attrs
        $bw.Write([uint32]0)       # external attrs
        $bw.Write([uint32]$c.Offset)
        $bw.Write($c.NameBytes)
    }

    $centralEnd = [uint32]$fs.Position
    $centralSize = [uint32]($centralEnd - $centralStart)
    $count = [uint16]$central.Count

    # End of central directory
    $bw.Write([uint32]0x06054B50)
    $bw.Write([uint16]0)           # disk number
    $bw.Write([uint16]0)           # central dir start disk
    $bw.Write([uint16]$count)      # entries on this disk
    $bw.Write([uint16]$count)      # total entries
    $bw.Write([uint32]$centralSize)
    $bw.Write([uint32]$centralStart)
    $bw.Write([uint16]0)           # comment length

    $bw.Flush()
}
finally {
    $bw.Dispose()
    $fs.Dispose()
}

Write-Host ("Created wotmod: {0}" -f $fullOutputPath)
