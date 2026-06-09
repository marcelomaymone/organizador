# Visão do Produto e Negócio - Organizador Pro

## 1. Declaração do Problema
Sistemas de arquivos com acervos massivos (até 4 TB de dados) são altamente suscetíveis à desorganização semântica crônica, dispersão de informações e duplicação descontrolada de arquivos. Tentativas tradicionais de organização automatizada por scripts simples (utilitários de sistema diretos) frequentemente falham devido a:
* **Erros de Classificação Semântica:** Decisões semânticas baseadas em heurísticas simples ou inteligência artificial direta sem aprovação humana geram perda ou dispersão irrecuperável de arquivos críticos em diretórios incorretos.
* **Esgotamento de Recursos do Sistema Operacional:** Operações síncronas de movimentação física em grandes volumes causam congelamento da interface gráfica (Windows 11), vazamentos de memória e falhas de concorrência.
* **Falta de Auditabilidade:** O usuário final não possui controle prévio do que será movido nem visibilidade do motivo (*Chain of Thought*) da classificação, resultando em desconfiança no sistema.

---

## 2. Visão do Produto
O **Organizador Pro** é um pipeline assíncrono de Extração, Transformação e Carga (ETL) projetado especificamente para governança e classificação automatizada de arquivos locais. A aplicação desacopla a tomada de decisão lógica da manipulação física de arquivos no sistema de arquivos, garantindo total controle humano, transparência e segurança absoluta dos dados.

---

## 3. Proposição de Valor e Regras de Negócio

### 3.1. Desacoplamento Crítico (Plano Lógico vs. Plano Físico)
Os arquivos nunca são movidos de forma síncrona ou autônoma imediata. A inteligência matemática classifica os metadados do acervo em um banco SQLite, gerando uma sugestão. A movimentação física dos arquivos (carga) só é disparada após a aprovação humana.

### 3.2. Modos de Operação do Pipeline
* **Origem = Destino (Organização In-Place):** O pipeline reorganiza os arquivos diretamente na própria árvore de diretórios existente. Durante a fase de limpeza final (teardown físico), todas as pastas vazias remanescentes serão excluídas recursivamente.
* **Origem ≠ Destino:** O sistema opera sob o modelo de cópia via fluxo direto (streaming/buffer), preservando a estrutura de arquivos no destino e **sem criar cache temporário** massivo no disco do host, protegendo a máquina contra o esgotamento súbito de espaço em disco.

### 3.3. Deduplicação Inteligente por Hash SHA-256
Para otimizar o tempo de processamento e mitigar custos computacionais ou financeiros de chamadas de LLM, o cálculo do hash SHA-256 é feito logo no início da varredura:
* Se um arquivo for idêntico a outro já processado (mesmo hash), a etapa de vetorização e inferência da IA é pulada, vinculando o duplicado logicamente à mesma classificação definida para o arquivo original de referência.
* Apenas uma cópia física do arquivo original será retida no destino. As cópias adicionais (duplicatas exatas) serão **apagadas fisicamente** durante a fase de limpeza final, caso o usuário acione a ação correspondente na interface.

### 3.4. Governança de Arquivos Não-Suportados e Quarentena
* **Quarentena Física:** Arquivos corrompidos, criptografados de forma ilegível ou que causem exceções críticas de I/O durante o processamento serão movidos fisicamente para uma pasta dedicada `_QUARENTENA_` na raiz do *destino*, preservando suas subpastas de origem para garantir rastreabilidade histórica. No SQLite, estes arquivos serão marcados com o status `quarentena` acompanhados do motivo da falha.
* **Formatos Não-Suportados Semânticos:** Para arquivos cujos formatos não permitam extração textual profunda (como binários, executáveis, áudio, etc.), o pipeline extrairá metadados básicos (tamanho, nome, extensão) e calculará o hash SHA-256. Eles serão direcionados para categorias padrão (ex: `Archives/Outros`) com a justificativa automática: *"Formato de arquivo não textual. Classificado em categoria geral para auditoria manual."*
* **Dúvida Semântica (Baixa Confiança):** Arquivos que passaram pela extração de texto, mas cuja classificação neural gerou índice de similaridade inferior ao limiar mínimo de corte, serão direcionados para a categoria lógica `"nao_classificado"`, permitindo revisão e reclassificação manual na interface.

### 3.5. Tratamento Especial de Mídias (Imagens e Vídeos)
Arquivos de imagem e vídeo possuem um fluxo de governança apartado. Eles serão direcionados para uma árvore estruturada com pastas específicas (`imagens` e `vídeos`). A movimentação ou cópia física deve **preservar integralmente os metadados nativos** de criação do arquivo (como data de captura e modificação original) utilizando chamadas às APIs internas do Windows.

### 3.6. Bloqueio Absoluto de Pastas Críticas de Sistema
Para blindar o sistema operacional Windows 11 de modificações acidentais devastadoras, o Organizador Pro abortará a operação imediatamente caso a Origem ou o Destino apontem para as seguintes áreas:
* `C:\Windows`
* `C:\Program Files` e `C:\Program Files (x86)`
* `C:\ProgramData`
* `C:\Users\[Nome]\AppData` e subpastas
* Raiz do sistema `C:\`

### 3.7. Mapeamento Físico de Hardware
Dada a possibilidade de processar HDDs e pendrives externos, o banco de dados associará o **Identificador Físico Único** do dispositivo correspondente ao arquivo. O usuário poderá atribuir um apelido (*label* ou *nickname*) no banco para rastrear a origem histórica do documento de forma amigável.

### 3.8. Rastreabilidade com Chain of Thought (CoT) e Propriedades Físicas
A decisão matemática de similaridade será acompanhada por uma justificativa em linguagem natural gerada por IA (*Chain of Thought*).
* **Injeção de Metadados:** A justificativa do CoT será injetada fisicamente nas propriedades estendidas do arquivo *apenas* em formatos abertos e suportados (ex: Office, PDF). Arquivos proprietários (como bancos de dados, arquivos PSD) não sofrerão injeção física para evitar riscos de corrupção.
* **Toggle de Persistência:** A interface do usuário fornecerá um interruptor (*toggle*) para que o usuário decida se o texto completo de CoT deve ser armazenado permanentemente no SQLite ou limpo após a conclusão do ciclo de movimentação.

---

## 4. Governança da UI e Painel de Auditoria
A interface do usuário atua exclusivamente como terminal de visualização de estados (*State Machine Viewer*), operando em modo isolado para evitar gargalos:
* **Laravel como BFF (Backend For Frontend):** Conecta-se ao banco de dados SQLite (`database.sqlite`) para leitura, paginação e controle de flags, sem realizar manipulações físicas diretas de arquivos no disco.
* **Controle de Autorização de Movimentação:** O usuário audita os lotes sugeridos com base nas estatísticas prévias e aprova a movimentação de duas formas:
  1. **Aprovação Unitária:** Arquivo por arquivo.
  2. **Aprovação em Lote:** Por categoria sugerida.
* **Propagação de Decisões de Duplicados:** Ao aprovar ou alterar o destino de um arquivo original de referência, o sistema propaga automaticamente a mesma ação para todos os seus duplicados identificados pelo hash, otimizando a governança.
* **Visualização Avançada:** O painel exibirá um gráfico de área (*Treemap* / Mapa de Calor) indicando a concentração física de volume de dados por categorias PCD.

---

## 5. Segurança da Informação e Blindagem de IA
* **Proteção contra Prompt Injection:** Para evitar que arquivos contendo instruções maliciosas manipulem o comportamento do LLM, toda string de texto extraída será higienizada (removendo tags HTML, delimitadores de bloco) e truncada rigidamente nos primeiros 2000 tokens antes do envio ao prompt.
* **Prevenção de Path Traversal:** Validação rigorosa dos caminhos via Pydantic. Padrões maliciosos (como `../../`) serão barrados e gerarão alertas de segurança no banco de dados.
* **Privilégio Mínimo (Least Privilege):** O servidor web Laravel rodará sob credenciais restritas do Windows 11, impedindo elevação de privilégios.

---

## 6. Estados e Ciclo de Vida do ETL
Cada arquivo no pipeline transita de forma estritamente controlada pelos seguintes status lógicos:
1. `pendente_extracao`: Recém-inventariado e deduplicado por hash, aguardando extração textual.
2. `pendente_inferencia`: Texto extraído com sucesso, aguardando vetorização e inferência.
3. `aguardando_auditoria`: Classificação lógica sugerida no banco, aguardando ação humana no painel.
4. `aprovado_para_movimentacao`: Destino logicamente validado e aprovado, pronto para execução física.
5. `quarentena`: Arquivo corrompido, inacessível ou criptografado, isolado na pasta física correspondente com log de motivo da falha.
6. `concluido`: Movimentado e validado fisicamente via hash SHA-256 no destino.
7. `erro`: Falha na execução física de qualquer uma das etapas anteriores.

---

## 7. Métricas de Sucesso (KPIs)
* **Zero Perda de Dados:** Ausência total de arquivos corrompidos ou deletados indevidamente.
* **Rastreabilidade de 100%:** Cada arquivo classificado possui registro de metadados, hash SHA-256 e justificativa lógica (CoT) no banco.
* **Operação em Background Silenciosa:** O processamento em background não deve causar congelamento da interface gráfica do Windows 11.
