# SACRED — Fingerprint Anti-Bot do Google (NÃO MODIFICAR)

Estes itens fazem parte do bypass de detecção de bot que **funciona hoje**.
Modificar qualquer um deles = risco real de ban do Google.

## Regra de ouro

Antes de qualquer mudança nestes itens:
1. Capturar fixture de response Google funcional (ANTES da mudança)
2. Fazer a mudança
3. Capturar nova fixture (DEPOIS da mudança)
4. Comparar: se diferente → **REVERTER IMEDIATAMENTE**
5. Se igual → ok para prosseguir

Em caso de dúvida: **PERGUNTAR ao usuário Samuel antes de tocar**.

---

## Tabela de Itens Sagrados

| Arquivo:linha | Item | Por que é sagrado |
|---|---|---|
| `src/google_auth.py:64` | User-Agent Chrome 131.0.0.0 | Match com Chrome real do usuário |
| `src/google_auth.py:67-74` | Headers `X-Same-Domain: 1`, `X-Goog-AuthUser: 0`, `Origin`, `Referer` | Bypass de Google RPC same-origin check |
| `src/google_auth.py:107` | Regex `"SNlM0e":"([^"]+)"` | Nome do token CSRF — Google pode renomear |
| `src/google_auth.py:113` | Regex `"cfb2h":"([^"]+)"` | Nome do build label — Google pode renomear |
| `src/server.py:27-47` | Pattern de re-auth por chamada | Pode ser intencional para parecer humano — testar antes de cachear |
| `src/notebook_api.py:33` | URL `_/LabsTailwindUi/data/batchexecute` | Endpoint interno reverse-engineered |
| `src/notebook_api.py:131` | URL `GenerateFreeFormStreamed` | Endpoint de query streaming |

## RPC IDs (todos sagrados)

| Constante | Valor | Operação |
|---|---|---|
| `CREATE_NOTEBOOK` | `CCqFvf` | Criar notebook |
| `ADD_SOURCE` | `izAoDd` | Adicionar fonte |
| `START_FAST_RESEARCH` | `Ljjv0c` | Pesquisa rápida |
| `START_DEEP_RESEARCH` | `QA9ei` | Deep Research |
| `POLL_RESEARCH` | `e3bVqc` | Polling status pesquisa |
| `IMPORT_RESEARCH_SOURCES` | `LBwxtb` | Importar fontes |
| `GET_NOTEBOOK` | `rLM1Ne` | Buscar notebook |
| `CREATE_ARTIFACT` | `R7cb6c` | Criar artefato Studio |
| `LIST_ARTIFACTS` | `gArtLc` | Listar artefatos |

## O que é seguro fazer (sem A/B test)

- Adicionar `safe_get()` wrapper em torno de magic indexes (não muda valores, só adiciona proteção)
- Adicionar logging de warnings (não muda requests)
- Adicionar exceções tipadas (não muda requests)
- Adicionar testes unitários (não toca em produção)
- Refatorar código que NÃO toca em requests HTTP (pydantic models, enums, config)

## O que REQUER A/B test

- Qualquer mudança em User-Agent, headers, cookies
- Qualquer mudança nos padrões de re-auth (frequência, ordem)
- Qualquer mudança nos RPC IDs ou URLs de endpoint
- Qualquer cache de CSRF/build_label (muda frequência de requests para homepage)
