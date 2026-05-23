# 📓 NotebookLM MCP Server (V2.1)

Conecte o poder do **Google NotebookLM** diretamente ao seu assistente de Inteligência Artificial no **Antigravity**! 🚀

Este projeto permite que a sua IA acesse seus documentos, faça pesquisas profundas na internet (Deep Research) e gere materiais de estudo (como questionários, resumos e slides) no **Estúdio do NotebookLM** sem que você precise abrir o site ou fazer configurações difíceis.

---

## 🌟 O que ele faz por você?

- **Pesquisa Profunda (Deep Research) 🔍**: A IA faz buscas completas na internet sobre qualquer assunto e adiciona os resultados automaticamente como fontes no seu caderno virtual.
- **Estúdio Inteligente 🎨**: Crie Guias de Estudo, Resumos de Reuniões, Questionários (Quizzes), Flashcards de memorização ou Mapas Mentais direto pelo chat da IA.
- **Consultas Inteligentes 💬**: Faça perguntas sobre o seu código ou projeto. A IA consulta o NotebookLM silenciosamente em segundo plano para responder com a maior precisão possível.

---

## 🚀 Como Configurar (Para Iniciantes)

Configurar é super simples e leva menos de 2 minutos! Siga os passos abaixo:

### Passo 1 — Ativar no Chat
Abra o chat da sua IDE Antigravity no seu projeto atual e digite o comando abaixo:
```bash
/notelm
```
A IA detectará que o projeto não possui um caderno virtual vinculado e perguntará se você deseja criar um. Basta responder que **Sim**!

### Passo 2 — Conectar sua conta do Google 🔐
Para que a IA possa ler e salvar as pesquisas, ela precisa acessar a sua conta do Google de forma segura.
1. No chat, peça para a IA: *"Fazer login no Google"* ou digite a ferramenta de autenticação.
2. Uma janela do navegador Google Chrome será aberta automaticamente.
3. Faça o login normal na sua conta do Google (a mesma que você usa no NotebookLM).
4. Assim que a página carregar, **feche a janela do navegador**.
5. Pronto! A IA salvou o acesso de forma segura e local na sua máquina.

---

## 💡 Como Usar no Dia a Dia (Exemplos Práticos)

Você não precisa rodar códigos no terminal! Basta conversar com o seu assistente de IA em português claro:

### 1. Fazer Pesquisa Profunda na Web
Se você precisa que a IA entenda uma nova tecnologia, biblioteca ou assunto complexo:
> 👤 **Você**: *"Faça uma Deep Research sobre a nova API do React 19 e salve no notebook."*
> 🤖 **IA**: *"Estou iniciando a pesquisa profunda no NotebookLM... Encontrei 6 fontes relevantes na web... Importando as fontes no seu notebook... Pronto!"*

### 2. Criar Materiais de Estudo (Estúdio)
Peça para a IA gerar qualquer item do painel "Estúdio" do NotebookLM:
- **Guia de Estudo**: *"Crie um guia de estudo baseado no nosso código atual."*
- **Quiz / Questionário**: *"Gere um quiz com perguntas difíceis sobre a nossa arquitetura."*
- **Resumo Executivo**: *"Crie um briefing doc resumindo os pontos principais do projeto."*

### 3. Fazer Perguntas Gerais
Toda vez que você perguntar algo como *"Como funciona a nossa conexão com o banco de dados?"*, a IA usará o NotebookLM automaticamente para consultar os arquivos locais do seu repositório. Você não precisa pedir!

---

## 🔒 Segurança em Primeiro Lugar

- **Dados 100% Locais**: Os cookies de acesso da sua conta Google ficam salvos de forma criptografada apenas na sua máquina (no arquivo `.env`). Eles **nunca** são compartilhados ou enviados para a internet.
- **Caderno Privado**: Os notebooks criados pertencem apenas à sua conta Google e só podem ser visualizados por você.

---

Feito com ❤️ para facilitar seus estudos e desenvolvimento. Qualquer dúvida, é só pedir ajuda para o assistente de IA no chat!
