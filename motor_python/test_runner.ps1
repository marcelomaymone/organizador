$ErrorActionPreference = "Continue"
Write-Output "Iniciando Test Runner no PowerShell nativo..."

# Configura PATH do Miniconda
$conda_path = "C:\Users\Marcelo Maymone\Miniconda3"
if (Test-Path $conda_path) {
    Write-Output "Diretorio do Miniconda existe. Injetando no PATH."
    $env:PATH = "$conda_path;$conda_path\Scripts;$conda_path\Library\bin;" + $env:PATH
} else {
    Write-Output "ALERTA: Diretorio do Miniconda nao foi encontrado no caminho padrao: $conda_path"
}

# Verifica se o executavel do python na venv existe
$venv_python = "c:\Users\Marcelo Maymone\Documents\antigravity_projetos\organizador_pro\motor_python\.venv\Scripts\python.exe"
if (Test-Path $venv_python) {
    Write-Output "Python da venv encontrado em $venv_python"
} else {
    Write-Output "ERRO: Python da venv nao encontrado!"
    Exit 1
}

# Executa Bandit e pytest capturando a saida e gravando nos arquivos de log
Write-Output "Rodando Bandit..."
try {
    & $venv_python -m bandit -r inventario.py main.py > bandit_run.log 2>&1
    Write-Output "Bandit concluido com exit code: $LASTEXITCODE"
} catch {
    Write-Output "Excecao ao rodar Bandit: $_"
}

Write-Output "Rodando Pytest..."
try {
    & $venv_python -m pytest > pytest_run.log 2>&1
    Write-Output "Pytest concluido com exit code: $LASTEXITCODE"
} catch {
    Write-Output "Excecao ao rodar Pytest: $_"
}

Write-Output "Test Runner concluido."
