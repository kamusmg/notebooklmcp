# 📖 Tutorial Completo — Do Zero ao Funcionando

> **Para quem nunca mexeu com terminal.** Vamos instalar tudo passo a passo, sem pressa.

---

## O que você vai conseguir no final

Digitar isso no terminal:

```
note "Como funciona o sistema de pagamentos?"
```

E receber uma resposta do seu Google NotebookLM direto no terminal, sem abrir o navegador.

---

## PARTE 1 — Instalar o Node.js

O Node.js é o programa que vai rodar o nosso script. Sem ele, nada funciona.

### Windows

1. Acesse: **https://nodejs.org**
2. Clique no botão verde grande que diz **"LTS"** (versão recomendada)
3. Baixe o arquivo `.msi` e execute ele
4. Clique em "Next" em tudo e "Finish" no final
5. **Reinicie o terminal** depois de instalar

**Como confirmar que funcionou:**
Abra o PowerShell (tecla Windows → digite "powershell" → Enter) e digite:

```
node --version
```

Deve aparecer algo como `v20.11.0`. Se aparecer, está instalado! ✅

### macOS

Abra o Terminal (Spotlight → "Terminal") e cole:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.zshrc
nvm install --lts
```

### Linux (Ubuntu/Debian)

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## PARTE 2 — Baixar este projeto

### Windows (PowerShell)

Cole no PowerShell e pressione Enter:

```powershell
git clone https://github.com/kamusmg/notebooklmcp.git
cd notebooklmcp
```

> **Não tem o git?** Baixe em https://git-scm.com/download/win — instale com tudo padrão.

### macOS / Linux

```bash
git clone https://github.com/kamusmg/notebooklmcp.git
cd notebooklmcp
```

---

## PARTE 3 — Instalar o `note` no seu computador

### Windows

No PowerShell, dentro da pasta do projeto, rode:

```powershell
.\install.ps1
```

> Se aparecer um erro de segurança, rode primeiro:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> E tente de novo.

### macOS / Linux

```bash
chmod +x install.sh
./install.sh
```

Quando terminar, você vai ver: **🎉 Instalação completa!**

**Reinicie o terminal** depois de instalar.

---

## PARTE 4 — Fazer login com o Google

Este é o passo que vai abrir o Chrome para você logar. Rode:

```bash
npx notebooklm-mcp setup_auth
```

Vai aparecer uma janela do Chrome. Faça isso:

1. **Logue na sua conta Google** (a mesma que você usa no NotebookLM)
2. **Acesse** https://notebooklm.google.com — só abrir a página já basta
3. **Feche a janela do Chrome**
4. Volte pro terminal — vai aparecer uma mensagem de sucesso

> Isso só precisa ser feito uma vez. O login fica salvo. Se expirar no futuro, é só rodar este comando de novo.

---

## PARTE 5 — Pegar a URL do seu notebook

1. Abra **https://notebooklm.google.com** no navegador
2. Clique no notebook que você quer usar
3. Olhe a barra de endereços — vai estar algo assim:
   ```
   https://notebooklm.google.com/notebook/abc123-def456-...
   ```
4. **Copie essa URL completa**

---

## PARTE 6 — Registrar o notebook

No terminal, cole (substituindo pela URL que você copiou):

```bash
note add https://notebooklm.google.com/notebook/SUA-URL-AQUI "Nome do Projeto"
```

Exemplo real:
```bash
note add https://notebooklm.google.com/notebook/abc123 "Meu Projeto"
```

Se aparecer `✅ Notebook registrado!`, funcionou!

---

## PARTE 7 — Fazer sua primeira pergunta

Agora é só usar:

```bash
note "Como funciona o sistema de login do projeto?"
```

Vai aparecer uma resposta baseada nos documentos do seu notebook. 🎉

---

## Outros comandos úteis

### Ver todos os notebooks cadastrados

```bash
note list
```

### Trocar para outro notebook

```bash
note use nome-do-notebook
```

### Ver qual notebook está ativo

```bash
note info
```

### Remover um notebook da lista

```bash
note remove nome-do-notebook
```

---

## Problemas comuns

### "node não reconhecido" / "node is not recognized"

O Node.js não foi instalado corretamente ou o terminal precisa ser reiniciado.
→ Feche e abra o terminal de novo. Se não funcionar, reinstale o Node.js.

### "note não reconhecido" / "note is not recognized"

O instalador adicionou o `note` ao PATH mas o terminal ainda não sabe.
→ Feche e abra o terminal de novo.

### A resposta do notebook vem vazia ou com erro

O login do Google expirou.
→ Rode: `npx notebooklm-mcp setup_auth`

### "Set-ExecutionPolicy" pediu confirmação

Digite `S` e pressione Enter para confirmar.

---

## Dica: Usar com IA (Claude Code, Antigravity etc.)

Depois de instalado, você pode pedir para qualquer IA rodar o `note` por você:

> "Consulte o notebook e me diga como funciona o sistema de pagamentos"

A IA vai rodar `note "como funciona o sistema de pagamentos"` e trazer a resposta automaticamente.

Para o Claude Code funcionar como MCP (mais integrado), veja o README para a configuração.

---

Pronto! Se chegou até aqui, você tem o NotebookLM funcionando no terminal. 🎉
