# NotebookLM MCP Desktop — Instruções para Claude Code

## O que é este projeto

Servidor MCP em Python para consultar o Google NotebookLM via RPC interno (`batchexecute`).
Expõe 9 tools MCP via stdio para uso direto de agentes de IA.

**NÃO confundir com** `C:\Users\samue\.notebooklm-mcp\` (projeto Node.js separado com comandos `note`/`lm`).

## Arquivos críticos

- `src/server.py` — 9 tools MCP expostos via FastMCP
- `src/notebook_api.py` — NotebookLMClient (RPC batchexecute)
- `src/google_auth.py` — Autenticação + fingerprint anti-bot (SAGRADO)
- `src/browser_auth.py` — Extração de cookies via Chrome CDP

## Como rodar

```powershell
cd "D:\projetos D\notebooklmcpdesktop-claude"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m src.server
```

## Autenticação (requer interação humana)

```python
# Via MCP tool:
# authenticate()

# Ou diretamente:
python -m src.browser_auth
```

Avise o usuário: "Uma janela do Chrome vai abrir — não feche, aguarde extrair os cookies."
Após extrair, cookies ficam no `.env` local.

## Regras INVIOLÁVEIS

1. **Ler SACRED.md antes de tocar em google_auth.py, notebook_api.py ou server.py**
2. **Ler COORDINATION.md antes de qualquer sessão de trabalho**
3. **Claude trabalha SOMENTE no worktree `notebooklmcpdesktop-claude/`** (branch `claude/upgrade-v3`)
4. **NUNCA editar** `D:\projetos D\notebooklmcpdesktop\` (território do Antigravity em `main`)
5. **NUNCA commitar** `.env`, `auth.json`, `.notebook_id`
6. **NUNCA push direto em `main`** — sempre via PR com aprovação do usuário
7. **Atualizar `.handoff.md` ao terminar** qualquer sessão

## Fingerprint anti-bot (resumo)

Os headers, User-Agent e padrão de re-auth em `src/google_auth.py` e `src/server.py` são o que
permite contornar a detecção de bot do Google. Ver `SACRED.md` para lista completa.
**Não modificar sem teste A/B com fixture real.**

## Rodar testes

```powershell
pytest tests/ -v                         # Unit tests (Fase 3+)
python test_research_run.py              # Integração (requer cookies reais)
```

## GitHub

Repo: `github.com/kamusmg/notebooklmcp` (público)
PR target: `main`
Branch de trabalho: `claude/upgrade-v3`
