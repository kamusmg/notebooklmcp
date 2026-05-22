# NotebookLM CLI — Guia para Antigravity (agy)

## O que é este projeto

CLI para consultar o Google NotebookLM direto do terminal, usando o pacote `notebooklm-mcp`.
Comandos principais: `note "pergunta"` e `lm "pergunta"`.

## Como instalar (quando o usuário pedir)

Execute os passos abaixo em ordem:

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

Avise o usuário: *"Uma janela do Chrome vai abrir — faça login na sua conta Google e entre em notebooklm.google.com. Depois feche a janela e me avise."*

Aguarde a confirmação antes de continuar.

### 3. Cadastrar o primeiro notebook

Peça ao usuário a URL do notebook no formato:
`https://notebooklm.google.com/notebook/...`

Depois rode:
```bash
note add <url> "Nome do Projeto"
```

### 4. Testar

```bash
note "Como funciona este projeto?"
```

Se a resposta vier, instalação completa.

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

## Se o login expirar

```bash
npx notebooklm-mcp setup_auth
```

## O que NÃO fazer

- Nunca commitar `auth.json` — contém cookies de sessão do Google
- Nunca hardcodar caminhos com username nos scripts
