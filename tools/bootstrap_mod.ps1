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

$envPath = Join-Path $GameRoot "mods\.env"
$envExamplePath = Join-Path $GameRoot ".env.example"
if (-not (Test-Path $envPath)) {
    if (Test-Path $envExamplePath) {
        Copy-Item -LiteralPath $envExamplePath -Destination $envPath -Force
    } else {
        $template = "# Required
WOT_TG_BOT_TOKEN=
WOT_TG_CHAT_ID=

# Optional
WOT_TG_TIMEOUT_SECONDS=3.0
WOT_TG_QUEUE_SIZE=128
"
        Set-Content -LiteralPath $envPath -Value $template -Encoding UTF8 -NoNewline
    }
    Write-Host "Created $envPath. Fill required values before launching the game."
} else {
    Write-Host ".env already exists: $envPath"
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

$artifact = Join-Path $GameRoot ("mods\\{0}\\wot_telegram_notifier_current.wotmod" -f $activeVersion)
if (Test-Path $artifact) {
    Write-Host "Artifact ready: $artifact"
} else {
    Write-Host "Warning: no artifact for active version $activeVersion yet."
}

Write-Host "Bootstrap completed."