# Diagnóstico Forense e Plano de Ações Corretivas - Organizador Pro

Esta auditoria forense analisa de forma meticulosa o ecossistema do **Organizador Pro** sob o método **BMAD** (Business, Management, Architecture, Development) com o objetivo de identificar inconformidades, gaps de regras de negócio, fragilidades arquiteturais e falhas de desenvolvimento, propondo ações corretivas estruturadas.

---

## User Review Required

> [!IMPORTANT]
> A auditoria forense identificou três falhas graves de conformidade com as regras de negócio declaradas no projeto:
> 
> 1. **Deduplicação Inexistente no Motor Python:** Embora a documentação defina que arquivos duplicados pelo hash xxhash devem pular a extração e a inferência de IA, o `inventario.py` marca todos com `eh_duplicado = 0`. Múltiplos arquivos idênticos passam individualmente pela vetorização e LLM, gerando custos financeiros e latência desnecessários.
> 2. **Rastreabilidade de Dispositivo Quebrada:** A coluna `dispositivo_id` fica sempre `NULL` no banco SQLite. O motor Python não implementa a lógica de detecção de hardware ID do disco NTFS de origem e não vincula os arquivos ao seu drive correspondente.
> 3. **Propagação de Decisões Incompleta no Laravel:** Quando o usuário aprova ou reclassifica um arquivo original de referência na interface, os duplicados não recebem a mesma decisão de destino nem são marcados como aprovados/descartados. Eles permanecem órfãos na fila do banco e nunca são processados pelo worker de movimentação física, deixando cópias extras acumulando lixo na pasta de origem.

---

## Proposed Changes

Para sanar os desvios, propõe-se uma refatoração pontual focada em manter a compatibilidade dos testes e colocar o sistema em total conformidade com a especificação original, sem alterar as APIs públicas das classes.

### 1. Camada de Negócios e Desenvolvimento (Python Engine)

#### [MODIFY] [inventario.py](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/motor_python/inventario.py)
* **Mapeamento de Hardware ID:** Implementar o método `obter_serial_volume` nativo no Windows 11 usando chamadas do kernel32 (com fallback para UUID em outros ambientes/erros). O `InventoryWorker` detectará o hardware ID da partição do diretório monitorado no construtor.
* **Registro de Dispositivo no SQLite:** Na inicialização, verificar se o dispositivo com o hardware ID detectado já existe na tabela `dispositivos`. Se não existir, criá-lo com um UUID único (`uuid.uuid4()`) e nome baseado na letra do drive e serial. Obter a chave primária `id` desse registro e associá-la à coluna `dispositivo_id` em todos os registros do lote inserido.
* **Deduplicação Lógica Atômica:**
  * Manter um cache local em memória (um `set` de hashes) de arquivos já inventariados na execução atual.
  * Antes de inserir um arquivo no banco, verificar se o hash já foi visto na execução atual ou se já existe no banco de dados com `eh_duplicado = 0`.
  * Se já existir, definir `eh_duplicado = 1`, `status = 'aguardando_auditoria'` e `justificativa_classificacao = 'Arquivo duplicado. Decisão de destino propagada do original correspondente.'`, pulando as fases subsequentes de extração e inferência.

### 2. Camada de Interface e Modelo de Dados (Laravel BFF)

#### [MODIFY] [ArquivoProcessamento.php](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/app/Models/ArquivoProcessamento.php)
* **Propagação Automática via Eventos do Eloquent:**
  * Implementar o método de ciclo de vida `booted()` no modelo Eloquent.
  * Adicionar um escopo `updated` que intercepta alterações em registros originais (`eh_duplicado = false`).
  * Toda vez que as colunas `status`, `caminho_aprovado`, `caminho_proposto`, `categoria_proposta` ou `justificativa_classificacao` mudarem, propagar automaticamente os mesmos valores em massa para todos os registros duplicados (mesmo `hash_xxhash` e `eh_duplicado = true`).
  * Esta abordagem centralizada resolve todas as rotas (aprovação unitária no Filament, reclassificação de caminhos e aprovação em lote), sem precisar mexer nos controllers ou resources individuais da interface.

### 3. Ajustes de Qualidade Estática (Linter)

#### [MODIFY] [movement_worker.py](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/motor_python/movement_worker.py)
* Remover trailing whitespace na linha 125 apontado pelo Ruff.

#### [MODIFY] [query_db.py](file:///c:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/motor_python/tests/query_db.py)
* Reorganizar imports ordenando-os corretamente de acordo com a recomendação do Ruff.

---

## Verification Plan

### Automated Tests
- **Ruff Linter:** Rodar `python -m ruff check .` para garantir a resolução completa de todos os warnings (exit code: 0).
- **Pytest:** Rodar a suíte inteira com `python -m pytest` garantindo que os 30 testes passem (incluindo testes de concorrência e integridade física).
- **Laravel Feature Tests:** Rodar `php artisan test` dentro da pasta `interface_laravel` para garantir o funcionamento correto das rotas ajax de auditoria e escopos de modelo.

### Manual Verification
1. **Teste de Inventário Real com Duplicatas:**
   * Executar o inventário em um diretório com arquivos redundantes (mesmo conteúdo, caminhos diferentes).
   * Confirmar via consulta SQLite se os arquivos originais estão marcados com `eh_duplicado = 0` (status `pendente_extracao`) e os duplicados com `eh_duplicado = 1` (status `aguardando_auditoria` diretamente).
   * Verificar se a coluna `dispositivo_id` está devidamente preenchida relacionando-se com a tabela `dispositivos`.
2. **Teste de Propagação:**
   * Na interface do Laravel/Filament, aprovar o arquivo original.
   * Verificar via SQLite se os duplicados correspondentes tiveram seus caminhos e status atualizados instantaneamente para `aprovado_para_movimentacao`.
