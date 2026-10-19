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
  python3 -m pip install --quiet --upgrade pillow 2>/dev/null \
    || python3 -m pip install --quiet --user --upgrade pillow 2>/dev/null \
    || python3 -m pip install --quiet --user --break-system-packages --upgrade pillow
  echo "Pillow instalado."
else
  echo "Atenção: Python 3 não encontrado. No Mac, rode python3 uma vez no Terminal e aceite instalar as ferramentas da Apple; depois rode este instalador de novo."
fi

# Atalho "Carrossel" na Mesa: abre o app (página com os assuntos e o botão Gerar)
MESA="${CARROSSEL_DESKTOP:-$HOME/Desktop}"
if [ -d "$MESA" ]; then
  ATALHO="$MESA/Carrossel.command"
  cat > "$ATALHO" <<'EOF'
#!/bin/bash
# Abre o app Carrossel no navegador. Deixe esta janela aberta enquanto usa; feche para desligar.
cd "$HOME/.codex/skills/carrossel-tweet" && exec python3 app/server.py
EOF
  chmod +x "$ATALHO"
  echo "Atalho criado: $ATALHO"
fi

if ! command -v codex >/dev/null 2>&1 && [ ! -d /Applications/Codex.app ]; then
  echo "Aviso: não achei o Codex. Instale o app do Codex (https://developers.openai.com/codex/app) e entre com a sua conta do ChatGPT."
fi
echo
echo "Pronto! Dê dois cliques em \"Carrossel\" na Mesa, ou peça no Claude Code/Codex: crie um carrossel tweet sobre <seu tema>."
