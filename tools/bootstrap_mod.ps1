param(
    [string]$RepoUrl = "https://github.com/mitinsany/WotBroColab.git",
    [string]$TargetBranch = "mod",
    [string]$GameRoot = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pathsXml = Join-Path $GameRoot "paths.xml"
if (-not (Test-Path $pathsXml)) {
    throw "paths.xml not found in $GameRoot. Run this script from WoT game folder."
}

if (-not (Test-Path (Join-Path $GameRoot ".git"))) {
    git init | Out-Null
}

$existingRemote = ""
try {
    $existingRemote = (git remote get-url origin 2>$null)
} catch {
    $existingRemote = ""
}

if (-not $existingRemote) {
    git remote add origin $RepoUrl
} elseif ($existingRemote -ne $RepoUrl) {
    git remote set-url origin $RepoUrl
}

git fetch origin

$hasLocalBranch = $false
try {
    git rev-parse --verify $TargetBranch 1>$null 2>$null
    $hasLocalBranch = $true
} catch {
    $hasLocalBranch = $false
}

if ($hasLocalBranch) {
    git checkout $TargetBranch
} else {
    git checkout -b $TargetBranch "origin/$TargetBranch"
}

git pull --ff-only origin $TargetBranch

$configPath = Join-Path $GameRoot "mods\wot_bro_colab.ini"
$configExamplePath = Join-Path $GameRoot "wot_bro_colab.ini.example"
if (-not (Test-Path $configPath)) {
    if (Test-Path $configExamplePath) {
        Copy-Item -LiteralPath $configExamplePath -Destination $configPath -Force
    } else {
        $template = "# Required
WOT_TG_BOT_TOKEN=
WOT_TG_CHAT_ID=

# Optional
WOT_TG_TIMEOUT_SECONDS=3.0
WOT_TG_QUEUE_SIZE=128
"
        Set-Content -LiteralPath $configPath -Value $template -Encoding UTF8 -NoNewline
    }
    Write-Host "Created $configPath. Fill required values before launching the game."
} else {
    Write-Host "Config already exists: $configPath"
}

[xml]$xml = Get-Content -Raw -LiteralPath $pathsXml
$activeVersion = $null
$nodes = $xml.SelectNodes("//Path")
foreach ($n in $nodes) {
    $text = $n.InnerText
    if ($text -match "res_mods[/\\]([0-9.]+)") {
        $activeVersion = $Matches[1]
        break
    }
}

if (-not $activeVersion) {
    throw "Cannot detect active res_mods version from $pathsXml"
}

$artifactGui = Join-Path $GameRoot ("res_mods\\{0}\\scripts\\client\\gui\\mods\\mod_wot_telegram_notifier.pyc" -f $activeVersion)
if (Test-Path $artifactGui) {
    Write-Host "Runtime ready: $artifactGui"
} else {
    Write-Host ("Warning: missing runtime file for active version {0}: {1}" -f $activeVersion, $artifactGui)
    Write-Host "Run 'git pull' and check branch 'mod'."
}

Write-Host "Bootstrap completed."
