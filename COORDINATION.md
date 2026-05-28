# COORDINATION — Claude Code ↔ Antigravity IDE

Este projeto é editado por DOIS agentes de IA diferentes. Para evitar
sobrescrita de trabalho:

## Quem trabalha onde

- **Antigravity IDE**: usa `D:\projetos D\notebooklmcpdesktop\` (branch `main`)
- **Claude Code**: usa `D:\projetos D\notebooklmcpdesktop-claude\` (worktree, branch `claude/upgrade-v3`)

## Antes de qualquer mudança

1. Rodar `git status` — não trabalhar se houver arquivos não-commitados de outra sessão
2. Rodar `git fetch origin && git log HEAD..origin/main --oneline` — ver se a outra branch avançou
3. Se outro agente commitou: pull/rebase antes de mexer

## Antes de terminar sessão

1. `git add -A && git commit -m "..."` — não deixar working tree sujo
2. `git push origin <sua-branch>` — sync com remote
3. Atualizar `.handoff.md` com resumo do que fez

## Merge para main

- Apenas via `gh pr create` + revisão manual do usuário Samuel
- Nunca `git push origin main` direto
- Antes do PR: rodar `pytest tests/` + `python test_research_run.py`

## Arquivos sagrados (anti-bot fingerprint)

Ver `SACRED.md`. Não modificar sem teste A/B com response Google real.
Se em dúvida: PERGUNTAR ao usuário antes de tocar nesses arquivos.
