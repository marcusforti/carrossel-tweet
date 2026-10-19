#!/usr/bin/env bash
# Instala a skill carrossel-tweet no Claude Code e no Codex (Mac e Linux).
# Uso: curl -fsSL https://raw.githubusercontent.com/marcusforti/carrossel-tweet/main/install.sh | bash
set -e
REPO="https://github.com/marcusforti/carrossel-tweet.git"
TMP="$(mktemp -d)/carrossel-tweet"

if command -v git >/dev/null 2>&1; then
  git clone --depth 1 "$REPO" "$TMP" >/dev/null 2>&1
else
  curl -fsSL "https://github.com/marcusforti/carrossel-tweet/archive/refs/heads/main.tar.gz" | tar -xz -C "$(dirname "$TMP")"
  mv "$(dirname "$TMP")/carrossel-tweet-main" "$TMP"
fi

for DEST in "$HOME/.claude/skills/carrossel-tweet" "$HOME/.codex/skills/carrossel-tweet"; do
  mkdir -p "$(dirname "$DEST")"
  rm -rf "$DEST"
  cp -R "$TMP" "$DEST"
  rm -rf "$DEST/.git"
  echo "Instalado em $DEST"
done
rm -rf "$TMP"

if command -v python3 >/dev/null 2>&1; then
  python3 -m pip install --quiet --upgrade pillow || python3 -m pip install --quiet --user --upgrade pillow
  echo "Pillow instalado."
else
  echo "Atenção: Python 3 não encontrado. Instale e rode: python3 -m pip install pillow"
fi
echo
echo "Pronto! Abra o Claude Code (ou o Codex) e peça: crie um carrossel tweet sobre <seu tema>."
