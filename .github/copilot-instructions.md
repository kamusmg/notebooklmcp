# NotebookLM CLI — Instruções para GitHub Copilot

## O que é este projeto

CLI para consultar o Google NotebookLM direto do terminal, usando o pacote `notebooklm-mcp`.
Comandos principais: `note "pergunta"` e `lm "pergunta"`.

## Como instalar (quando o usuário pedir)

### 1. Rodar o instalador

**Windows:**
```powershell
.\install.ps1
```

**macOS / Linux:**
```bash
chmod +x install.sh && ./install.sh
```

### 2. Login com Google (requer interação humana)

```bash
npx notebooklm-mcp setup_auth
```

Instrua o usuário a logar no Google na janela do Chrome que vai abrir e acessar notebooklm.google.com. Aguarde confirmação antes de continuar.

### 3. Cadastrar o primeiro notebook

```bash
note add <url-do-notebook> "Nome do Projeto"
```

### 4. Testar

```bash
note "Como funciona este projeto?"
```

---

## Comandos disponíveis

| Comando | Descrição |
|---------|-----------|
| `note "pergunta"` | Consulta o notebook ativo |
| `note add <url> [nome]` | Cadastra um notebook |
| `note list` | Lista notebooks cadastrados |
| `note use <id>` | Troca o notebook ativo |
| `note remove <id>` | Remove um notebook |
| `note info` | Status e estatísticas |

## Renovar login expirado

```bash
npx notebooklm-mcp setup_auth
```

## Regras do código

- Nunca hardcodar caminhos com username — usar sempre `os.homedir()`
- `auth.json` nunca deve ser commitado (está no `.gitignore`)
- O script principal é `ask_notebook.js` — toda lógica está nele
