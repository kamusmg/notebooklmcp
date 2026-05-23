# NotebookLM CLI V2 — Instruções para Agentes de IA

## O que é este projeto

Servidor MCP em Python para consultar o Google NotebookLM direto de ambientes de agentes compatíveis (como a IDE do Google Antigravity), sem usar automação de tela (Playwright/Chromium). Ele opera por meio de chamadas assíncronas/síncronas de alto desempenho diretamente nos endpoints HTTP/RPC internos do Google.

---

## Estrutura do Servidor MCP

- **`src/google_auth.py`**: Gerenciador de sessão e injeção de cookies Pro (`SID`, `HSID`, etc.) para bypass de login.
- **`src/notebook_api.py`**: Mapeamento dos endpoints RPC e batchexecute do NotebookLM.
- **`src/server.py`**: Core do Servidor MCP utilizando `FastMCP`, que expõe as ferramentas abaixo.

---

## Ferramentas MCP Expostas

1. `provision_lifecycle`
   - Parâmetros: `project_name` (str), `github_repo_url` (str)
   - Ação: Cria um NotebookLM para o projeto atual e vincula o repositório Git como fonte principal. Persiste o ID do notebook gerado no arquivo `.notebook_id` na raiz do projeto.
2. `deep_query`
   - Parâmetros: `notebook_id` (str), `question` (str)
   - Ação: Encaminha uma pergunta diretamente ao chat interno do NotebookLM e retorna a resposta grounded.
3. `authenticate`
   - Parâmetros: `method` (str, padrão: "browser")
   - Ação: Abre o navegador Chrome com depuração remota habilitada para que o usuário faça login na conta Google Pro e, após o login, extrai automaticamente os cookies salvando-os no arquivo `.env`.

---

## [DIRETRIZES DE COMPORTAMENTO DO AGENTE - NOTEBOOKLMCP V2]

### 1. Gatilho do Comando `/notelm`
Sempre que o usuário digitar `/notelm` no chat, invoque **imediatamente** a ferramenta MCP `provision_lifecycle` passando o nome da pasta do projeto atual e a URL do repositório Git local.

### 2. Ciclo de Vida de Boot do Projeto
Ao inicializar ou abrir este diretório de trabalho:
- **Se o arquivo `.notebook_id` existir na raiz:**
  Leia o ID contido nele e use-o silenciosamente nas futuras ferramentas de `deep_query`. Não pergunte nada ao usuário.
- **Se o arquivo `.notebook_id` não existir na raiz:**
  Inicie a conversa obrigatoriamente com a seguinte mensagem padrão:
  > *"Samuel, notei que este projeto ainda não tem um NotebookLM vinculado. Deseja criar um ambiente fechado de Deep Research para ele agora? (Você também pode ignorar e ativar mais tarde digitando `/notelm`)."*

### 3. Resposta do Usuário ao Boot
- Se ele responder positivamente: Execute a ferramenta `provision_lifecycle` imediatamente.
- Se ele responder negativamente: Permaneça em modo local.
