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

# Atalho "Carrossel" na Mesa: abre o app (pagina com os assuntos e o botao Gerar)
$mesa = if ($env:CARROSSEL_DESKTOP) { $env:CARROSSEL_DESKTOP } else { [Environment]::GetFolderPath("Desktop") }
if ($py -and (Test-Path $mesa)) {
    $server = "$HOME\.codex\skills\carrossel-tweet\app\server.py"
    $pyw = Join-Path (Split-Path $py.Source) "pythonw.exe"
    if (-not (Test-Path $pyw)) { $pyw = Join-Path (Split-Path $py.Source) "pyw.exe" }
    if (-not (Test-Path $pyw)) { $pyw = $py.Source }
    $lnk = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $mesa "Carrossel.lnk"))
    $lnk.TargetPath = $pyw
    $lnk.Arguments = "`"$server`""
    $lnk.WorkingDirectory = Split-Path (Split-Path $server)
    $lnk.Description = "Gerar carrosseis estilo tweet"
    $lnk.Save()
    Write-Host "Atalho criado: $(Join-Path $mesa 'Carrossel.lnk')"
}
if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    Write-Host "Aviso: nao achei o Codex. Instale o app do Codex (https://developers.openai.com/codex/app) e entre com a sua conta do ChatGPT."
}
Write-Host "`nPronto! Dois cliques em 'Carrossel' na Mesa, ou peca no Claude Code/Codex: crie um carrossel tweet sobre <seu tema>."
