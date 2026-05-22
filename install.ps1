# Instalador do NotebookLM CLI para Windows (PowerShell)

$InstallDir = "$env:USERPROFILE\.notebooklm-cli"
$BinDir = "$env:USERPROFILE\.local\bin"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "📓 Instalador do NotebookLM CLI" -ForegroundColor Cyan
Write-Host "────────────────────────────────"

# Verificar Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js $nodeVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js não encontrado. É necessário para rodar o script." -ForegroundColor Red
    Write-Host "   Baixe em: https://nodejs.org"
    exit 1
}

# Criar pastas
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

# Copiar script principal
Copy-Item "$ScriptDir\ask_notebook.js" "$InstallDir\ask_notebook.js" -Force
Write-Host "✅ Script instalado em $InstallDir" -ForegroundColor Green

# Criar note.cmd
@"
@echo off
node "$InstallDir\ask_notebook.js" %*
"@ | Out-File -FilePath "$BinDir\note.cmd" -Encoding ascii

# Criar lm.cmd (alias)
@"
@echo off
node "$InstallDir\ask_notebook.js" %*
"@ | Out-File -FilePath "$BinDir\lm.cmd" -Encoding ascii

Write-Host "✅ Comandos 'note' e 'lm' instalados em $BinDir" -ForegroundColor Green

# Adicionar ao PATH do usuário se necessário
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$BinDir*") {
    Write-Host "⚠️  Adicionando $BinDir ao PATH..." -ForegroundColor Yellow
    [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$BinDir", "User")
    Write-Host "✅ PATH atualizado. Reinicie o terminal para aplicar." -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Instalação completa!" -ForegroundColor Green
Write-Host ""
Write-Host "Próximo passo — fazer login com Google:" -ForegroundColor White
Write-Host "  npx notebooklm-mcp setup_auth" -ForegroundColor Cyan
Write-Host ""
Write-Host "Depois cadastre seu primeiro notebook:" -ForegroundColor White
Write-Host "  note add <url-do-notebook> `"Nome do Projeto`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "E use:" -ForegroundColor White
Write-Host '  note "Como funciona o sistema de pagamentos?"' -ForegroundColor Cyan
Write-Host ""
Write-Host "Veja o TUTORIAL.md para guia completo passo a passo." -ForegroundColor White
Write-Host ""
