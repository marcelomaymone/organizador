# Lista de Tarefas - Auditoria Forense e Ações Corretivas

- `[x]` Correções de Qualidade Estática (Linter)
  - `[x]` Remover trailing whitespace de [movement_worker.py](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/motor_python/movement_worker.py) (L125)
  - `[x]` Organizar imports de [query_db.py](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/motor_python/tests/query_db.py)
- `[x]` Refatoração do Motor Python ([inventario.py](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/motor_python/inventario.py))
  - `[x]` Implementar captura de Hardware ID do drive NTFS de origem
  - `[x]` Integrar registro do drive na tabela `dispositivos` e associar `dispositivo_id`
  - `[x]` Implementar deduplicação lógica na varredura (marcar `eh_duplicado = 1` e status `aguardando_auditoria` para redundantes)
- `[x]` Refatoração do Laravel BFF ([ArquivoProcessamento.php](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/app/Models/ArquivoProcessamento.php))
  - `[x]` Implementar propagação automática de decisões de aprovação/reclassificação e descarte do arquivo original para seus duplicados no SQLite via evento Eloquent `updated`
- `[x]` Validação Geral do Sistema
  - `[x]` Executar linter Ruff e confirmar correção de alertas
  - `[x]` Rodar testes unitários com pytest no Python
  - `[x]` Rodar testes de integração e feature no Laravel
