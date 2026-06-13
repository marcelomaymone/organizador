<#
.SYNOPSIS
    Organizador Pro - Script de Empacotamento para Deploy Portavel
    Gera o pacote completo de distribuicao na pasta deploy\producao\
    contendo: motor Python, PHP portavel, Laravel BFF e banco SQLite.

.NOTES
    Execute a partir da raiz do projeto:
        powershell -ExecutionPolicy Bypass -File deploy\empacotar.ps1
#>

$ErrorActionPreference = "Stop"

# ---- Configuracoes ----------------------------------------
$RAIZ = Split-Path -Parent $PSScriptRoot
$DESTINO = Join-Path $RAIZ "deploy\producao"
$PHP_HERD = "C:\Users\$env:USERNAME\.config\herd\bin\php84"

# ---- Funcoes Auxiliares -----------------------------------
function Write-Step([string]$numero, [string]$descricao) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  Etapa $numero - $descricao" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-OK([string]$msg)   { Write-Host "[OK]  $msg" -ForegroundColor Green }
function Write-Info([string]$msg) { Write-Host "[..] $msg" -ForegroundColor Yellow }
function Write-Erro([string]$msg) { Write-Host "[ERR] $msg" -ForegroundColor Red }

function Get-TamanhoMB([string]$caminho) {
    if (Test-Path $caminho) {
        $soma = (Get-ChildItem $caminho -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        return [math]::Round($soma / 1MB, 1)
    }
    return 0
}

# ---- Cabecalho --------------------------------------------
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Magenta
Write-Host "      ORGANIZADOR PRO - EMPACOTAMENTO PORTATIL DE PRODUCAO         " -ForegroundColor Magenta
Write-Host "====================================================================" -ForegroundColor Magenta
Write-Host "  Raiz do projeto : $RAIZ"
Write-Host "  Destino de saida: $DESTINO"
$dataHora = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "  Data/hora       : $dataHora"
Write-Host ""

# ---- Validacoes Pre-Empacotamento -------------------------
Write-Host "Verificando pre-requisitos..." -ForegroundColor White

$motorExe = Join-Path $RAIZ "dist\motor_organizador\motor_organizador.exe"
if (-not (Test-Path $motorExe)) {
    Write-Erro "Motor compilado nao encontrado em: $motorExe"
    Write-Erro "Execute: cd motor_python && .venv\Scripts\activate && pyinstaller ..\motor_organizador.spec"
    exit 1
}
$motorSizeMB = [math]::Round((Get-Item $motorExe).Length / 1MB, 1)
Write-OK "Motor Python compilado: $motorSizeMB MB"

$laravelDir = Join-Path $RAIZ "interface_laravel"
$laravelVendor = Join-Path $laravelDir "vendor"
if (-not (Test-Path $laravelVendor)) {
    Write-Erro "Pasta vendor/ nao encontrada em interface_laravel\"
    Write-Erro "Execute: cd interface_laravel && composer install"
    exit 1
}
Write-OK "Interface Laravel com vendor/ encontrada"

$phpPortatil = Join-Path $RAIZ "php\php.exe"
$phpHerdExe = Join-Path $PHP_HERD "php.exe"
if (-not (Test-Path $phpPortatil) -and -not (Test-Path $phpHerdExe)) {
    Write-Erro "PHP portavel nao encontrado em php\ nem em: $PHP_HERD"
    exit 1
}
Write-OK "PHP 8.4 portavel disponivel"

$sqliteOrigem = Join-Path $RAIZ "banco_dados\database.sqlite"
if (-not (Test-Path $sqliteOrigem)) {
    Write-Erro "Banco de dados nao encontrado em: $sqliteOrigem"
    exit 1
}
$sqliteKB = [math]::Round((Get-Item $sqliteOrigem).Length / 1KB, 0)
Write-OK "Banco SQLite encontrado: $sqliteKB KB"

# ---- Etapa 1: Preparar estrutura de destino ---------------
Write-Step "1" "Preparando estrutura de diretorios"

$dirs = @(
    "$DESTINO\dist\motor_organizador",
    "$DESTINO\interface_laravel",
    "$DESTINO\php",
    "$DESTINO\banco_dados",
    "$DESTINO\docs"
)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-OK "Estrutura criada em: $DESTINO"

# ---- Etapa 2: Copiar Motor Python compilado ---------------
Write-Step "2" "Copiando Motor Python compilado (PyInstaller)"

$motorSrc = Join-Path $RAIZ "dist\motor_organizador\*"
$motorDst = "$DESTINO\dist\motor_organizador"
Write-Info "Copiando motor e dependencias _internal/ ..."
Copy-Item -Path $motorSrc -Destination $motorDst -Recurse -Force
$motorTotalMB = Get-TamanhoMB $motorDst
Write-OK "Motor copiado: $motorTotalMB MB"

# ---- Etapa 3: Copiar PHP portavel -------------------------
Write-Step "3" "Copiando PHP 8.4 portavel"

if (Test-Path $phpPortatil) {
    $phpOrigem = Join-Path $RAIZ "php"
} else {
    $phpOrigem = $PHP_HERD
}
Write-Info "Origem PHP: $phpOrigem"
Copy-Item -Path "$phpOrigem\*" -Destination "$DESTINO\php" -Recurse -Force
$phpTotalMB = Get-TamanhoMB "$DESTINO\php"
Write-OK "PHP copiado: $phpTotalMB MB"

# ---- Etapa 4: Copiar Interface Laravel --------------------
Write-Step "4" "Copiando Interface Laravel (sem arquivos de desenvolvimento)"

$laravelDst = "$DESTINO\interface_laravel"
Write-Info "Executando robocopy (excluindo .git, node_modules, tests)..."
robocopy $laravelDir $laravelDst /E /XD ".git" "node_modules" "tests" /XF "*.log" ".phpunit.result.cache" "require_filament.txt" "show_filament.txt" /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -gt 7) {
    Write-Erro "Robocopy falhou com codigo: $LASTEXITCODE"
    exit 1
}

$envProd = Join-Path $RAIZ "interface_laravel\.env.producao"
$envDst = "$laravelDst\.env"
if (Test-Path $envDst) { Remove-Item $envDst -Force }
Copy-Item -Path $envProd -Destination $envDst -Force
Write-Info "ATENCAO: Configure DB_DATABASE, DESTINATION_PATH e GEMINI_API_KEY no arquivo .env antes de executar!"

$laravelTotalMB = Get-TamanhoMB $laravelDst
Write-OK "Laravel copiado: $laravelTotalMB MB"

# ---- Etapa 5: Banco de Dados SQLite -----------------------
Write-Step "5" "Copiando banco de dados SQLite"

Copy-Item -Path $sqliteOrigem -Destination "$DESTINO\banco_dados\database.sqlite" -Force
$dbKB = [math]::Round((Get-Item "$DESTINO\banco_dados\database.sqlite").Length / 1KB, 0)
Write-OK "SQLite copiado: $dbKB KB"

# ---- Etapa 6: Script de Orquestracao ----------------------
Write-Step "6" "Copiando orquestrador start.bat"

Copy-Item -Path (Join-Path $RAIZ "start.bat") -Destination "$DESTINO\start.bat" -Force
Write-OK "start.bat portavel v2.0 copiado"

# ---- Etapa 7: Documentacao --------------------------------
Write-Step "7" "Gerando documentacao de primeira execucao"

$dataVersao = Get-Date -Format "yyyy-MM-dd"
$linhasGuia = @(
    "# Organizador Pro - Guia de Primeira Execucao",
    "",
    "ESTRUTURA DO PACOTE:",
    "  dist/motor_organizador/  - Motor de processamento ETL (autonomo)",
    "  interface_laravel/       - Painel web (Laravel + FilamentPHP)",
    "  php/                     - PHP 8.4 portavel (sem instalacao necessaria)",
    "  banco_dados/             - Banco de dados SQLite",
    "  start.bat                - Ponto de entrada da aplicacao",
    "",
    "CONFIGURACAO OBRIGATORIA (primeira execucao):",
    "Edite o arquivo interface_laravel/.env e configure:",
    "",
    "  1. DB_DATABASE",
    "     Caminho absoluto para o banco SQLite neste volume.",
    "     Exemplo: DB_DATABASE=D:/organizador_pro/banco_dados/database.sqlite",
    "",
    "  2. DESTINATION_PATH",
    "     Caminho absoluto para a pasta destino dos arquivos organizados.",
    "     Exemplo: DESTINATION_PATH=D:/acervo_organizado",
    "",
    "  3. GEMINI_API_KEY",
    "     Chave da API Google Gemini para classificacao semantica via IA.",
    "     Obtenha gratuitamente em: https://aistudio.google.com/app/apikey",
    "",
    "COMO EXECUTAR:",
    "  Abra um Prompt de Comando (CMD) e execute: start.bat run",
    "  O painel web estara disponivel em: http://localhost:8000",
    "",
    "PROCESSAR ARQUIVOS:",
    "  start.bat scan [pasta_acervo]  - Indexa todos os arquivos",
    "  start.bat extract              - Extrai texto dos documentos",
    "  start.bat inference            - Classifica semanticamente com IA",
    "  start.bat move                 - Move fisicamente os arquivos aprovados",
    "",
    "SUPORTE:",
    "  Documentacao tecnica: docs/bmad/",
    "  Versao do pacote: $dataVersao",
    "  PHP incluido: 8.4.22 (NTS x64)"
)
$guiaConteudo = $linhasGuia -join "`r`n"
$guiaConteudo | Out-File -FilePath "$DESTINO\docs\PRIMEIROS_PASSOS.md" -Encoding UTF8 -Force
Write-OK "Guia de primeiros passos gerado"

# ---- Etapa 8: Validacao Final -----------------------------
Write-Step "8" "Validacao da estrutura do pacote"

$artefatos = @(
    @{ P = "$DESTINO\dist\motor_organizador\motor_organizador.exe"; N = "Motor Python (exe)" },
    @{ P = "$DESTINO\dist\motor_organizador\_internal";             N = "Motor Python (_internal)" },
    @{ P = "$DESTINO\php\php.exe";                                  N = "PHP 8.4 portavel" },
    @{ P = "$DESTINO\interface_laravel\vendor";                     N = "Laravel vendor/" },
    @{ P = "$DESTINO\interface_laravel\artisan";                    N = "Laravel artisan" },
    @{ P = "$DESTINO\interface_laravel\.env";                       N = "Laravel .env (producao)" },
    @{ P = "$DESTINO\banco_dados\database.sqlite";                  N = "Banco SQLite" },
    @{ P = "$DESTINO\start.bat";                                    N = "Orquestrador start.bat" },
    @{ P = "$DESTINO\docs\PRIMEIROS_PASSOS.md";                     N = "Guia de primeiros passos" }
)

$nOK = 0
$nErro = 0
foreach ($a in $artefatos) {
    if (Test-Path $a.P) { Write-OK $a.N; $nOK++ }
    else                { Write-Erro "AUSENTE: $($a.N) em $($a.P)"; $nErro++ }
}

# ---- Relatorio Final --------------------------------------
$totalMB = Get-TamanhoMB $DESTINO
$distMB  = Get-TamanhoMB "$DESTINO\dist"
$phpMB   = Get-TamanhoMB "$DESTINO\php"
$lwMB    = Get-TamanhoMB "$DESTINO\interface_laravel"
$dbFinalKB = [math]::Round((Get-Item "$DESTINO\banco_dados\database.sqlite").Length / 1KB, 0)

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Magenta
Write-Host "                   RELATORIO DE EMPACOTAMENTO                       " -ForegroundColor Magenta
Write-Host "====================================================================" -ForegroundColor Magenta
Write-Host "  Motor Python (dist/)  : $distMB MB"
Write-Host "  PHP 8.4 portavel      : $phpMB MB"
Write-Host "  Interface Laravel     : $lwMB MB"
Write-Host "  Banco SQLite          : $dbFinalKB KB"
Write-Host "  ------------------------------------------------------------------"
Write-Host "  TOTAL DO PACOTE       : $totalMB MB"
Write-Host ""
Write-Host "  Artefatos validados: $nOK / $($artefatos.Count)"
Write-Host "  Destino final      : $DESTINO"
Write-Host "====================================================================" -ForegroundColor Magenta

if ($nErro -gt 0) {
    Write-Host ""
    Write-Erro "EMPACOTAMENTO INCOMPLETO: $nErro artefatos ausentes!"
    exit 1
} else {
    Write-Host ""
    Write-Host "[SUCESSO] Pacote de producao gerado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Proximos passos:" -ForegroundColor White
    Write-Host "  1. Configure: $DESTINO\interface_laravel\.env" -ForegroundColor White
    Write-Host "  2. Copie a pasta de producao para o volume de 4 TB" -ForegroundColor White
    Write-Host "  3. No destino, execute start.bat run" -ForegroundColor White
    Write-Host ""
}
