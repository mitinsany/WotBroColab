function New-Crc32Table {
    $table = New-Object 'UInt32[]' 256
    for ($i = 0; $i -lt 256; $i++) {
        $crc = [uint32]$i
        for ($j = 0; $j -lt 8; $j++) {
            if (($crc -band 1) -ne 0) {
                $crc = ([uint32]0xEDB88320) -bxor ($crc -shr 1)
            } else {
                $crc = $crc -shr 1
            }
        }
        $table[$i] = $crc
    }
    return $table
}

function Get-Crc32([byte[]]$bytes, [uint32[]]$table) {
    $crc = [uint32]0xFFFFFFFF
    foreach ($b in $bytes) {
        $idx = ($crc -bxor [uint32]$b) -band 0xFF
        $crc = $table[$idx] -bxor ($crc -shr 8)
    }
    return (-bnot $crc) -band 0xFFFFFFFF
}

function Get-DosTimeDate([DateTime]$dt) {
    $sec = [int][Math]::Floor($dt.Second / 2)
    $dosTime = ($dt.Hour -shl 11) -bor ($dt.Minute -shl 5) -bor $sec
    $year = $dt.Year
    if ($year -lt 1980) { $year = 1980 }
    $dosDate = (($year - 1980) -shl 9) -bor ($dt.Month -shl 5) -bor $dt.Day
    return @([uint16]$dosTime, [uint16]$dosDate)
}

param(
    [string]$SrcMod = ".\\res_mods\\mods\\mod_wot_telegram_notifier.py",
    [string]$Out = ".\\build\\wot_telegram_notifier_store.wotmod"
)

$metaText = @'
<?xml version="1.0" encoding="utf-8"?>
<root>
  <id>wot.telegram.notifier</id>
  <name>WoT Telegram Notifier</name>
  <description>Telegram notifications for login/logout/battle start/battle end.</description>
  <version>1.0.2</version>
</root>
'@

$files = @()
$files += [PSCustomObject]@{
    Name = "scripts/client/gui/mods/mod_wot_telegram_notifier.py"
    Data = [System.IO.File]::ReadAllBytes($SrcMod)
}
$files += [PSCustomObject]@{
    Name = "meta.xml"
    Data = [System.Text.Encoding]::UTF8.GetBytes($metaText)
}

if (Test-Path $Out) { Remove-Item $Out -Force }

$table = New-Crc32Table
$now = Get-Date
$td = Get-DosTimeDate $now
$dosTime = $td[0]
$dosDate = $td[1]

$fs = [System.IO.File]::Open($Out, [System.IO.FileMode]::CreateNew)
$bw = New-Object System.IO.BinaryWriter($fs)

$central = New-Object System.Collections.Generic.List[object]

foreach ($f in $files) {
    $nameBytes = [System.Text.Encoding]::ASCII.GetBytes($f.Name)
    $data = [byte[]]$f.Data
    $crc = Get-Crc32 $data $table
    $size = [uint32]$data.Length
    $offset = [uint32]$fs.Position

    # local file header
    $bw.Write([uint32]0x04034B50)
    $bw.Write([uint16]20)          # version needed
    $bw.Write([uint16]0)           # general purpose bit flag
    $bw.Write([uint16]0)           # compression method: store
    $bw.Write([uint16]$dosTime)
    $bw.Write([uint16]$dosDate)
    $bw.Write([uint32]$crc)
    $bw.Write([uint32]$size)
    $bw.Write([uint32]$size)
    $bw.Write([uint16]$nameBytes.Length)
    $bw.Write([uint16]0)           # extra length
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
    # central directory header
    $bw.Write([uint32]0x02014B50)
    $bw.Write([uint16]20)          # version made by
    $bw.Write([uint16]20)          # version needed
    $bw.Write([uint16]0)           # flags
    $bw.Write([uint16]0)           # method
    $bw.Write([uint16]$dosTime)
    $bw.Write([uint16]$dosDate)
    $bw.Write([uint32]$c.Crc)
    $bw.Write([uint32]$c.Size)
    $bw.Write([uint32]$c.Size)
    $bw.Write([uint16]$c.NameBytes.Length)
    $bw.Write([uint16]0)           # extra len
    $bw.Write([uint16]0)           # comment len
    $bw.Write([uint16]0)           # disk number start
    $bw.Write([uint16]0)           # internal attrs
    $bw.Write([uint32]0)           # external attrs
    $bw.Write([uint32]$c.Offset)
    $bw.Write($c.NameBytes)
}

$centralEnd = [uint32]$fs.Position
$centralSize = [uint32]($centralEnd - $centralStart)
$count = [uint16]$central.Count

# end of central directory
$bw.Write([uint32]0x06054B50)
$bw.Write([uint16]0)               # disk number
$bw.Write([uint16]0)               # central dir start disk
$bw.Write([uint16]$count)          # entries on this disk
$bw.Write([uint16]$count)          # total entries
$bw.Write([uint32]$centralSize)    # size of central directory
$bw.Write([uint32]$centralStart)   # offset of central directory
$bw.Write([uint16]0)               # comment length

$bw.Flush()
$bw.Dispose()
$fs.Dispose()

Write-Output ("created:" + $Out)
