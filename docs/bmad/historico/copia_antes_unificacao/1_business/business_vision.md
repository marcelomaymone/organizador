# Visão do Produto e Negócio - Organizador Pro

## 1. Declaração do Problema
Sistemas de arquivos com acervos massivos (até 4 TB de dados) são altamente suscetíveis à desorganização semântica crônica, dispersão de informações e duplicação descontrolada de arquivos. Tentativas tradicionais de organização automatizada por scripts simples (utilitários de sistema diretos) frequentemente falham devido a:
* **Erros de Classificação Semântica:** Decisões semânticas baseadas em heurísticas simples ou inteligência artificial direta sem aprovação geram perda ou dispersão irrecuperável de arquivos críticos em diretórios incorretos.
* **Esgotamento de Recursos do Sistema Operacional:** Operações síncronas de movimentação física em grandes volumes causam congelamento da interface gráfica (Windows 11), vazamentos de memória e falhas de concorrência.
* **Falta de Auditabilidade:** O usuário final não possui controle prévio do que será movido nem visibilidade do motivo (*Chain of Thought*) da classificação, resultando em desconfiança no sistema.

## 2. Visão do Produto
O **Organizador Pro** é um pipeline assíncrono de Extração, Transformação e Carga (ETL) projetado especificamente para governança e classificação automatizada de arquivos locais. A aplicação desacopla a tomada de decisão lógica da manipulação física de arquivos no sistema de arquivos, garantindo total controle humano, transparência e segurança absoluta dos dados.

## 3. Proposição de Valor
* **Desacoplamento Crítico (Plano Lógico vs. Plano Físico):** Os arquivos nunca são movidos de forma síncrona ou autônoma imediata. A inteligência matemática classifica os metadados do acervo em um banco SQLite, gerando uma sugestão. A movimentação física dos arquivos (carga) só é disparada após a aprovação humana.
* **Rastreabilidade Cognitiva (Justificativa CoT):** Cada decisão de classificação é acompanhada por uma justificativa em linguagem natural gerada por IA (*Chain of Thought*), permitindo que o auditor entenda os critérios utilizados pela máquina.
* **Deduplicação Inteligente por Hash SHA-256:** Para otimizar o tempo de processamento e mitigar custos computacionais ou financeiros de chamadas de LLM, o cálculo do hash SHA-256 é feito logo no início da varredura. Se um arquivo for idêntico a outro já processado (mesmo hash), a etapa de vetorização e inferência da IA é pulada, vinculando o duplicado logicamente à mesma classificação definida para o arquivo original.
* **Governança de Arquivos Não-Suportados:** Para arquivos cujo formato não permita a extração textual profunda (como binários, executáveis, imagens, vídeos, áudios e arquivos compactados), o pipeline realiza o inventário de seus metadados (tamanho, nome, extensão) e hash SHA-256. Esses arquivos são encaminhados para subpastas de destino padrão (ex: `Archives/Outros` ou similares) com a justificativa automática: *"Formato de arquivo não textual. Classificado em categoria geral para auditoria manual."* O usuário auditor pode revisar e reposicionar esses arquivos normalmente pela interface web.

## 4. Governança da UI e Painel de Auditoria
A interface do usuário é a única ferramenta de controle e auditoria estatística do sistema. Ela segue regras restritas para garantir a estabilidade do sistema e mitigar riscos operacionais:
* **Interface PHP/Laravel:** Construída estritamente para leitura e controle de status. Ela se conecta ao banco de dados SQLite (`database.sqlite`) para apresentar os resultados consolidados do processamento.
* **Paginação Estrita:** Devido ao volume maciço do acervo (até 4 TB e centenas de milhares de arquivos), a interface exibe as listagens de arquivos de forma rigorosamente paginada no banco de dados, evitando o carregamento total na memória RAM do PHP e consequentes erros de estouro de memória (OOM).
* **Restrição de Operações Físicas:** A interface Laravel **não executa nenhuma ação física no disco**. Ela não move, copia ou deleta arquivos. Os botões da interface servem exclusivamente para atualizar a flag lógica de auditoria (`status_revisao`) para os valores **Aprovado** ou **Rejeitado**.
* **Privilégio Mínimo (Least Privilege):** O servidor web PHP (Laravel) deve rodar obrigatoriamente com permissões de usuário restrito no Windows 11, garantindo que vulnerabilidades de segurança web não deem acesso administrativo ao sistema operacional.

## 5. Segurança da Informação e Blindagem de IA
Para assegurar a integridade do sistema operacional Windows 11 e dos dados do usuário, o motor de inteligência e o pipeline ETL contam com salvaguardas rigorosas:
* **Proteção contra Prompt Injection:** Para evitar que arquivos maliciosos contendo comandos em texto (ex: PDFs com instruções para a IA tomar ações indevidas) manipulem o comportamento do LLM, toda string de texto extraída dos documentos será sanitizada (remoção de tags HTML, caracteres de controle) e truncada rigidamente no limite máximo de 2000 tokens antes do envio ao prompt da IA.
* **Prevenção de Path Traversal:** O motor Python (utilizando validação do Pydantic) deve sanitizar e validar estritamente todos os caminhos de diretório originais e de destino. Qualquer tentativa de caminho malicioso (como `../../Windows/System32` ou caracteres especiais de escape de diretório) deve disparar um erro imediato no Pydantic, cancelando a operação do arquivo e registrando o alerta de segurança no banco de dados.

## 6. Estados e Ciclo de Vida do ETL
Para garantir a rastreabilidade e a consistência, cada arquivo no pipeline deve transitar obrigatoriamente pelas seguintes fases lógicas de status:
1. `pendente_extracao`: Arquivo recém-inventariado e deduplicado por hash, aguardando leitura e extração de texto.
2. `pendente_inferencia`: Texto extraído com sucesso, aguardando vetorização matemática e inferência com justificativa CoT.
3. `aguardando_auditoria`: Classificação semântica sugerida no banco, aguardando decisão do auditor na UI do Laravel.
4. `aprovado_para_movimentacao`: Destino logicamente validado e aprovado pelo usuário, elegível para a execução física.
5. `concluido`: Arquivo movido fisicamente para a pasta final sem erros e com logs registrados.
6. `erro`: Falha em qualquer uma das etapas (de extração, inferência ou movimentação física), contendo a descrição da falha na coluna correspondente para auditoria manual.

## 7. Métricas de Sucesso (KPIs)
* **Zero Perda de Dados:** Ausência total de arquivos corrompidos ou perdidos devido à atomicidade da operação e isolamento de etapas.
* **Rastreabilidade de 100%:** Todo arquivo processado deve conter um registro de metadados, hash SHA-256 e justificativa lógica (CoT) no banco de dados.
* **Operação Responsiva:** O Windows 11 hospedeiro não deve apresentar travamentos ou gargalos na interface gráfica durante a varredura e inferência em background.
* **Tempo de Auditoria:** Redução de até 90% no tempo gasto pelo usuário para reestruturar manualmente diretórios de até 4 TB, necessitando apenas aprovar ou rejeitar lotes consolidados.

## 8. Stakeholders e Personas
* **Usuário Administrador (Auditor):** Profissional com grande volume de dados locais (pesquisadores, engenheiros, criadores de conteúdo) que precisa manter uma estrutura rigorosa (ex: metodologia P.A.R.A.) sem gastar horas em classificação manual.
* **Desenvolvedor/Arquiteto do Sistema:** Agente responsável por estender e adaptar o classificador a novos formatos ou regras de negócio locais sem violar a estabilidade e atomicidade do pipeline.
