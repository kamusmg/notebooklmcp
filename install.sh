#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/.notebooklm-cli"
BIN_DIR="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "📓 Instalador do NotebookLM CLI"
echo "────────────────────────────────"

# Verificar Node.js
if ! command -v node &>/dev/null; then
  echo "❌ Node.js não encontrado. É necessário para rodar o script."
  echo "   Instale em: https://nodejs.org"
  exit 1
fi

echo "✅ Node.js $(node --version) encontrado"

# Criar pastas
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Copiar script principal
cp "$SCRIPT_DIR/ask_notebook.js" "$INSTALL_DIR/ask_notebook.js"
echo "✅ Script instalado em $INSTALL_DIR"

# Criar wrapper 'note'
cat > "$BIN_DIR/note" <<EOF
#!/usr/bin/env bash
node "$INSTALL_DIR/ask_notebook.js" "\$@"
EOF
chmod +x "$BIN_DIR/note"

# Criar alias 'lm'
cat > "$BIN_DIR/lm" <<EOF
#!/usr/bin/env bash
node "$INSTALL_DIR/ask_notebook.js" "\$@"
EOF
chmod +x "$BIN_DIR/lm"

echo "✅ Comandos 'note' e 'lm' instalados em $BIN_DIR"

# Verificar PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo ""
  echo "⚠️  $BIN_DIR não está no seu PATH."
  echo "   Adicione esta linha no seu ~/.bashrc ou ~/.zshrc:"
  echo ""
  echo '   export PATH="$HOME/.local/bin:$PATH"'
  echo ""
  echo "   Depois rode: source ~/.bashrc"
fi

echo ""
echo "🎉 Instalação completa!"
echo ""
echo "Próximo passo — fazer login com Google:"
echo "  npx notebooklm-mcp setup_auth"
echo ""
echo "Depois cadastre seu primeiro notebook:"
echo "  note add <url-do-notebook> \"Nome do Projeto\""
echo ""
echo "E use:"
echo "  note \"Como funciona o sistema de pagamentos?\""
echo ""
echo "Veja o TUTORIAL.md para guia completo passo a passo."
echo ""
