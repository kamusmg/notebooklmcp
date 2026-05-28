# NotebookLM MCP Desktop (v3.0)

Servidor MCP em Python para consultar o **Google NotebookLM** diretamente de agentes de IA.
Funciona no **Claude Code** e no **Google Antigravity IDE** via protocolo MCP (stdio).

Opera por chamadas diretas aos endpoints RPC internos do Google — sem Playwright, sem automação de tela.

---

## O que faz

- **Deep Research** — inicia pesquisa web profunda no NotebookLM e importa as fontes encontradas
- **Query direta** — faz perguntas grounded nas suas fontes (equivale a abrir o chat do NotebookLM)
- **Studio artifacts** — gera Study Guide, Briefing Doc, Quiz, Slide Deck, Data Table no Estúdio
- **Provision** — cria um notebook novo e vincula um repositório GitHub como fonte

## Instalação rápida

```powershell
cd "D:\projetos D\notebooklmcpdesktop"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Autenticação

Os cookies do Google ficam armazenados em texto simples no arquivo `.env` local.
**Eles nunca são enviados para fora da sua máquina.** Você pode deletar o `.env` a qualquer momento.

Para autenticar:
```powershell
# Importar cookies do projeto Node.js (se você já tinha autenticado lá)
python scripts/import_cookies_from_node.py

# OU autenticar via Chrome (abre janela do browser)
python -m src.browser_auth
```

### Configurar no Claude Code

Adicione em `~/.claude/settings.json`:
```json
"mcpServers": {
  "notebooklm-python": {
    "command": "python",
    "args": ["-m", "src.server"],
    "cwd": "D:\\projetos D\\notebooklmcpdesktop"
  }
}
```

### Configurar no Antigravity

Adicione em `~/.gemini/antigravity-ide/mcp_config.json`:
```json
"notebooklm-python": {
  "command": "python",
  "args": ["-m", "src.server"],
  "cwd": "D:\\projetos D\\notebooklmcpdesktop",
  "type": "stdio"
}
```

## Tools MCP disponíveis

| Tool | Parâmetros | O que faz |
|------|-----------|-----------|
| `health_check` | — | Verifica autenticação e conectividade |
| `deep_query` | `notebook_id`, `question` | Pergunta direta ao chat do NotebookLM |
| `provision_lifecycle` | `project_name`, `github_repo_url` | Cria notebook e vincula repo |
| `authenticate` | `method="browser"` | Abre Chrome para login |
| `start_research` | `notebook_id`, `query`, `mode` | Inicia pesquisa web (fast/deep) |
| `poll_research` | `notebook_id`, `task_id` | Status da pesquisa + fontes encontradas |
| `import_research_sources` | `notebook_id`, `task_id`, `sources` | Importa fontes para o notebook |
| `get_notebook_sources` | `notebook_id` | Lista IDs de fontes ativas |
| `generate_studio_artifact` | `notebook_id`, `artifact_type` | Gera artefato do Estúdio |
| `poll_studio_artifact` | `notebook_id`, `artifact_id` | Status + conteúdo do artefato |
| `usage_stats` | — | Estatísticas de uso local |

### Tipos de artefato do Estúdio

`study_guide` | `briefing_doc` | `blog_post` | `quiz` | `slide_deck` | `data_table` | `custom`

## Rodar testes

```powershell
pip install -r requirements-dev.txt
pytest tests/ -v
```

## Estrutura

```
src/
  server.py          # 11 tools MCP (FastMCP)
  notebook_api.py    # NotebookLMClient — RPC batchexecute
  google_auth.py     # Autenticação + fingerprint anti-bot (SAGRADO)
  browser_auth.py    # Extração de cookies via Chrome CDP
  exceptions.py      # Exceções tipadas
  rpc_ids.py         # Constantes de RPC ID
  status_codes.py    # Enums de status
  config.py          # Settings centralizados
  validators.py      # Validação de inputs
  retry.py           # Retry com exponential backoff
  telemetry.py       # Telemetria local
scripts/
  import_cookies_from_node.py  # Migração de cookies do projeto Node.js
tests/
  test_auth.py        # 11 testes de autenticação
  test_notebook_api.py # 16 testes de parsing
  test_status_codes.py # 13 testes de status codes
```

## Coordenação Claude Code + Antigravity

Este projeto é usado por dois agentes de IA. Ver `COORDINATION.md` e `SACRED.md` antes de fazer qualquer mudança.

## Segurança

- Cookies armazenados em texto simples no `.env` local (protegidos apenas pelo filesystem do OS)
- Nenhuma informação enviada para fora da sua máquina
- `.env` está no `.gitignore` — nunca é commitado

## Licença

MIT
