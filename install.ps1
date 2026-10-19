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

function Find-Python {
    # Ignora o "python" falso do Windows (atalho da Microsoft Store em WindowsApps, que não roda nada)
    foreach ($nome in @("python", "py")) {
        foreach ($c in @(Get-Command $nome -All -ErrorAction SilentlyContinue)) {
            if ($c.Source -like "*\WindowsApps\*") { continue }
            try { & $c.Source --version *> $null; if ($LASTEXITCODE -eq 0) { return $c } } catch {}
        }
    }
    foreach ($p in (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)) {
        return (Get-Command $p.FullName)
    }
    return $null
}

$py = Find-Python
if (-not $py -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "Python nao encontrado. Instalando o Python 3.12 (so para este usuario, sem senha de administrador)..."
    winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements | Out-Null
    $py = Find-Python
}
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
# O app Carrossel usa o comando "codex" (Codex CLI) por tras. O app do Codex nem sempre traz esse comando,
# entao, se faltar, instala o CLI pelo instalador oficial da OpenAI (nao precisa de Node).
function Find-Codex {
    $cands = @(Get-Command codex -All -ErrorAction SilentlyContinue | ForEach-Object { $_.Source })
    $cands += "$env:LOCALAPPDATA\Programs\OpenAI\Codex\bin\codex.exe"
    foreach ($c in $cands) {
        if ($c -and (Test-Path $c)) {
            try { $v = & $c --version 2>$null; if ($LASTEXITCODE -eq 0) { return @{ Path = $c; Version = "$v" } } } catch {}
        }
    }
    return $null
}
$codex = Find-Codex
if (-not $codex -and -not $env:CARROSSEL_SEM_CODEX) {
    Write-Host "Instalando o Codex CLI (instalador oficial da OpenAI)..."
    $env:CODEX_NON_INTERACTIVE = "1"
    try { & ([scriptblock]::Create((Invoke-RestMethod https://chatgpt.com/codex/install.ps1))) } catch { Write-Host "Nao deu para instalar o Codex CLI: $_" }
    $codex = Find-Codex
}
if ($codex) {
    Write-Host "Codex pronto: $($codex.Version)"
    $st = & $codex.Path login status 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0 -or $st -match "Not logged") {
        Write-Host "Falta entrar com a sua conta do ChatGPT: abra o Carrossel e clique em 'Entrar com o ChatGPT' (ou rode: codex login)."
    }
} else {
    Write-Host "Aviso: o Codex ainda nao esta instalado. Abra o Carrossel e clique em 'Instalar o Codex'."
}
Write-Host "`nPronto! Dois cliques em 'Carrossel' na Area de Trabalho, ou peca no Claude Code/Codex: crie um carrossel tweet sobre <seu tema>."
