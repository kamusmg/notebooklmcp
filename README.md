# 📓 NotebookLM CLI

Converse com seus notebooks do **Google NotebookLM** direto pelo terminal — e deixe sua IA favorita (Claude Code, Antigravity CLI ou qualquer outra) consultar seus documentos automaticamente.

```bash
note "Como funciona o sistema de ordens do projeto?"
```

```
──────────────────────────────────────────────────────
O sistema de ordens utiliza uma fila FIFO com prioridade
por tipo de ativo. Ordens de mercado são executadas...
──────────────────────────────────────────────────────
```

---

## Como funciona

Este projeto é um **cliente CLI** para o pacote [`notebooklm-mcp`](https://www.npmjs.com/package/notebooklm-mcp). Ele abre o NotebookLM via Playwright (navegador em segundo plano), envia sua pergunta e retorna a resposta no terminal.

Seus notebooks ficam registrados localmente — basta instalar uma vez, logar com Google, e usar para sempre.

---

## Instalação

### Pré-requisitos

- [Node.js 18+](https://nodejs.org) instalado
- Conta no [Google NotebookLM](https://notebooklm.google.com) com pelo menos um notebook

### Windows

Abra o PowerShell como administrador e rode:

```powershell
git clone https://github.com/kamusmg/notebooklmcp.git
cd notebooklmcp
.\install.ps1
```

### macOS / Linux

```bash
git clone https://github.com/kamusmg/notebooklmcp.git
cd notebooklmcp
chmod +x install.sh
./install.sh
```

### Passo 2 — Fazer login com Google

Após instalar, rode o comando abaixo. Uma janela do Chrome vai abrir:

```bash
npx notebooklm-mcp setup_auth
```

1. Faça login na sua conta Google
2. Acesse [notebooklm.google.com](https://notebooklm.google.com)
3. Feche a janela — pronto, sessão salva!

### Passo 3 — Registrar seu primeiro notebook

Copie a URL do seu notebook no navegador e rode:

```bash
note add https://notebooklm.google.com/notebook/SEU-ID-AQUI "Nome do Projeto"
```

### Passo 4 — Usar!

```bash
note "Qual é a arquitetura do projeto?"
```

---

## Comandos

| Comando | O que faz |
|---------|-----------|
| `note "pergunta"` | Faz uma pergunta ao notebook ativo |
| `note add <url> [nome]` | Registra um novo notebook |
| `note list` | Lista todos os notebooks cadastrados |
| `note use <id>` | Troca o notebook ativo |
| `note remove <id>` | Remove um notebook da lista local |
| `note info` | Mostra status e estatísticas |

> O atalho `lm` funciona igual ao `note` — use o que preferir.

---

## Integração com IA

Este projeto inclui arquivos de instruções para os principais assistentes de IA. Quando você clona o repo e abre com seu assistente, ele já sabe o que é o projeto e como instalar — sem precisar explicar nada.

| Assistente | Arquivo lido automaticamente |
|------------|------------------------------|
| Claude Code | `CLAUDE.md` |
| Antigravity (agy) | `guia_antigravity.md` |
| GitHub Copilot | `.github/copilot-instructions.md` |
| Cursor | `.cursorrules` |
| Outros agentes | `AGENTS.md` |

### Instalar via IA (recomendado)

Clone o repo, abra com seu assistente e diga apenas:

> *"Instala isso aqui."*

O assistente lê as instruções, roda o instalador, e te guia pelo login do Google.

### Claude Code (MCP)

Para integrar o NotebookLM diretamente nas ferramentas do Claude, adicione ao seu `.claude/settings.json`:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "npx",
      "args": ["-y", "notebooklm-mcp@latest"]
    }
  }
}
```

Depois você pode pedir ao Claude diretamente no chat:
> *"Consulte o notebook sobre o sistema de pagamentos e explique como funciona o retry."*

### Antigravity CLI (agy)

O agente pode rodar `note "pergunta"` automaticamente sempre que precisar de contexto do seu projeto. Consulte o [`guia_antigravity.md`](guia_antigravity.md) para detalhes.

---

## Renovar login (quando expirar)

Se as respostas pararem de funcionar, o login pode ter expirado:

```bash
npx notebooklm-mcp setup_auth
```

---

## Segurança

- O arquivo `auth.json` (cookies do Google) fica salvo **localmente** no seu computador
- Nunca é enviado para este repositório (está no `.gitignore`)
- Seus notebooks e dados **nunca saem da sua máquina**

---

## Tutorial passo a passo

Veja o [TUTORIAL.md](TUTORIAL.md) para um guia completo do zero para quem nunca usou terminal.

---

## Licença

MIT
