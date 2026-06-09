import subprocess
import sys
import os

# Usamos o script Python nativo para orquestrar os testes e linter de forma limpa,
# isolando o ambiente de interpretacao do host contra peculiaridades de parsing do PowerShell (SOLID).

def run_cmd(args, name):
    print(f"[+] Rodando {name}...")
    venv_python = os.path.join(".venv", "Scripts", "python.exe")
    cmd_args = [venv_python] + args
    
    # Captura stdout e stderr para logging centralizado
    result = subprocess.run(cmd_args, capture_output=True, text=True)
    return result

def main():
    log_content = []
    log_content.append("====================================================")
    log_content.append("    RESULTADOS DETALHADOS DOS TESTES E LINTER")
    log_content.append("====================================================")
    log_content.append("")
    
    # 1. Bandit (Segurança estática)
    res_bandit = run_cmd(["-m", "bandit", "-r", "inventario.py", "main.py"], "Bandit (Seguranca)")
    log_content.append("=== BANDIT RESULT ===")
    log_content.append(res_bandit.stdout)
    log_content.append(res_bandit.stderr)
    log_content.append(f"Exit Code: {res_bandit.returncode}")
    log_content.append("-" * 50)
    print(f"-> Bandit concluido com status: {res_bandit.returncode}")
    
    # 2. Ruff (Qualidade de código)
    res_ruff = run_cmd(["-m", "ruff", "check", "."], "Ruff (Linter)")
    log_content.append("=== RUFF RESULT ===")
    log_content.append(res_ruff.stdout)
    log_content.append(res_ruff.stderr)
    log_content.append(f"Exit Code: {res_ruff.returncode}")
    log_content.append("-" * 50)
    print(f"-> Ruff concluido com status: {res_ruff.returncode}")
    
    # 3. Pytest (Testes de unidade do inventário)
    res_pytest = run_cmd(["-m", "pytest"], "Pytest (Testes)")
    log_content.append("=== PYTEST RESULT ===")
    log_content.append(res_pytest.stdout)
    log_content.append(res_pytest.stderr)
    log_content.append(f"Exit Code: {res_pytest.returncode}")
    log_content.append("-" * 50)
    print(f"-> Pytest concluido com status: {res_pytest.returncode}")
    
    # Salva o arquivo de log no workspace do projeto
    with open("linter_tests_results.log", "w", encoding="utf-8") as f:
        f.write("\n".join(log_content))
        
    print("[+] Resultados salvos em linter_tests_results.log")

if __name__ == "__main__":
    main()
