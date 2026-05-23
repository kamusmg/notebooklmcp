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
   - Ação: Cria um NotebookLM para o projeto atual e vincula o repositório Git como fonte principal.
2. `deep_query`
   - Parâmetros: `notebook_id` (str), `question` (str)
   - Ação: Faz uma pergunta direta no chat do NotebookLM e retorna a resposta.
3. `authenticate`
   - Parâmetros: `method` (str, padrão: "browser")
   - Ação: Abre o Chrome para login manual e extrai automaticamente os cookies salvando no `.env`.
4. `start_research`
   - Parâmetros: `notebook_id` (str), `query` (str), `mode` (str)
   - Ação: Inicia uma pesquisa web (Fast ou Deep) e retorna o `task_id`.
5. `poll_research`
   - Parâmetros: `notebook_id` (str), `task_id` (str)
   - Ação: Monitora o status da pesquisa web ativa (retorna progresso, fontes e relatório).
6. `import_research_sources`
   - Parâmetros: `notebook_id` (str), `task_id` (str), `sources` (list)
   - Ação: Importa fontes descobertas pela pesquisa como fontes permanentes do NotebookLM.
7. `get_notebook_sources`
   - Parâmetros: `notebook_id` (str)
   - Ação: Retorna a lista de IDs de fontes ativos vinculados ao notebook.
8. `generate_studio_artifact`
   - Parâmetros: `notebook_id` (str), `artifact_type` (str), `custom_prompt` (str, opcional)
   - Ação: Gera um entregável no Estúdio do NotebookLM (como Guia de Estudo, Resumo ou Quiz) com base em todas as fontes.
9. `poll_studio_artifact`
   - Parâmetros: `notebook_id` (str), `artifact_id` (str)
   - Ação: Monitora o status de geração e retorna o conteúdo gerado (markdown, etc.).

---

## [DIRETRIZES DE COMPORTAMENTO DO AGENTE - NOTEBOOKLMCP V2]

### 1. Gatilho do Comando `/notelm`
Sempre que o usuário digitar `/notelm` no chat, invoque **imediatamente** a ferramenta MCP `provision_lifecycle` passando o nome da pasta do projeto atual e a URL do repositório Git local.

### 2. Ciclo de Vida de Boot do Projeto
Ao inicializar ou abrir este diretório de trabalho:
- **Se o arquivo `.notebook_id` existir na raiz:**
  Leia o ID contido nele e use-o silenciosamente nas futuras consultas. Não pergunte nada ao usuário.
- **Se o arquivo `.notebook_id` não existir na raiz:**
  Inicie a conversa obrigatoriamente com a seguinte mensagem padrão:
  > *"Samuel, notei que este projeto ainda não tem um NotebookLM vinculado. Deseja criar um ambiente fechado de Deep Research para ele agora? (Você também pode ignorar e ativar mais tarde digitando `/notelm`)."*

### 3. Resposta do Usuário ao Boot
- Se ele responder positivamente: Execute a ferramenta `provision_lifecycle` imediatamente.
- Se ele responder negativamente: Permaneça em modo local.

### 4. Proatividade e Comunicação de Pesquisa (IMPORTANTE)
- **Aviso de Progresso no Chat**: Sempre que iniciar uma pesquisa web profunda (`start_research`) ou geração de artefatos do Estúdio, você deve explicar e manter o usuário atualizado no chat em tempo real a cada iteração de polling (ex: *"Samuel, estou iniciando uma pesquisa profunda sobre [tema] no NotebookLM para enriquecer o contexto do seu projeto..."*, *"Ainda pesquisando... encontrei 6 fontes web relevantes..."*, *"Pesquisa concluída! Relatório final gerado. Agora vou importar as fontes..."*).
- **Proatividade de Deep Research**: Se o usuário te fizer perguntas sobre o código ou sobre bibliotecas externas que necessitam de buscas web atualizadas, e você perceber que o NotebookLM atual não possui fontes suficientes sobre esse assunto, ofereça-se proativamente para rodar uma pesquisa profunda (Deep Research) e salvá-la no notebook para uso futuro.
- **Uso do Estúdio**: Sempre que o usuário solicitar resumos detalhados, questionários, mapas mentais ou guias de estudo do repositório, utilize a ferramenta `generate_studio_artifact` + `poll_studio_artifact` para gerar e trazer a versão estruturada do Estúdio do NotebookLM, apresentando o resultado final de forma muito polida no chat.
- **Metáforas Amigáveis**: NUNCA exponha termos técnicos como "RPC", "batchexecute" ou "payload" nas mensagens do chat. Use termos humanos e amigáveis como "Pesquisa profunda na web", "Processando fontes", "Gerando Guia de Estudo no Estúdio", etc.
