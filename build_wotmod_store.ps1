param(
  [string]$SrcMod = ".\\res_mods\\mods\\mod_wot_telegram_notifier.py",
  [string]$Out = ".\\build\\wot_telegram_notifier_store.wotmod"
)

if (Test-Path $Out) { Remove-Item $Out -Force }

$meta = @"
<?xml version="1.0" encoding="utf-8"?>
<root>
  <id>wot.telegram.notifier</id>
  <name>WoT Telegram Notifier</name>
  <description>Telegram notifications for login/logout/battle start/battle end.</description>
  <version>1.0.1</version>
</root>
"@

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$fs = [System.IO.File]::Open($Out, [System.IO.FileMode]::CreateNew)
$zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create, $false)

try {
  $entry1 = $zip.CreateEntry("scripts/client/gui/mods/mod_wot_telegram_notifier.py", [System.IO.Compression.CompressionLevel]::NoCompression)
  $s1 = $entry1.Open()
  $w1 = New-Object System.IO.StreamWriter($s1, [System.Text.Encoding]::UTF8)
  try { $w1.Write([System.IO.File]::ReadAllText($SrcMod)) } finally { $w1.Dispose(); $s1.Dispose() }

  $entry2 = $zip.CreateEntry("meta.xml", [System.IO.Compression.CompressionLevel]::NoCompression)
  $s2 = $entry2.Open()
  $w2 = New-Object System.IO.StreamWriter($s2, [System.Text.Encoding]::UTF8)
  try { $w2.Write($meta) } finally { $w2.Dispose(); $s2.Dispose() }
}
finally {
  $zip.Dispose()
  $fs.Dispose()
}

Write-Output ("created:" + $Out)
