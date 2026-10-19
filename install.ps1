# Instala a skill carrossel-tweet no Claude Code e no Codex (Windows).
# Uso: irm https://raw.githubusercontent.com/marcusforti/carrossel-tweet/main/install.ps1 | iex
$ErrorActionPreference = "Stop"
$repo = "https://github.com/marcusforti/carrossel-tweet.git"
$tmp = Join-Path $env:TEMP "carrossel-tweet-install"

if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
if (Get-Command git -ErrorAction SilentlyContinue) {
    git clone --depth 1 $repo $tmp | Out-Null
} else {
    $zip = "$tmp.zip"
    Invoke-WebRequest "https://github.com/marcusforti/carrossel-tweet/archive/refs/heads/main.zip" -OutFile $zip
    Expand-Archive $zip -DestinationPath "$tmp-x" -Force
    Move-Item (Get-ChildItem "$tmp-x" | Select-Object -First 1).FullName $tmp
    Remove-Item $zip, "$tmp-x" -Recurse -Force
}

foreach ($dest in @("$HOME\.claude\skills\carrossel-tweet", "$HOME\.codex\skills\carrossel-tweet")) {
    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    Copy-Item $tmp $dest -Recurse
    Remove-Item (Join-Path $dest ".git") -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Instalado em $dest"
}
Remove-Item $tmp -Recurse -Force

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if ($py) {
    & $py.Source -m pip install --quiet --upgrade pillow
    Write-Host "Pillow instalado."
} else {
    Write-Host "Atencao: Python nao encontrado. Instale em https://www.python.org/downloads/ e rode: python -m pip install pillow"
}
Write-Host "`nPronto! Abra o Claude Code (ou o Codex) e peça: crie um carrossel tweet sobre <seu tema>."
