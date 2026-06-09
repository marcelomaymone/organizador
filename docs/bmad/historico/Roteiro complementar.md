Aqui está o roteiro de execução pormenorizado para a construção do Organizador Pro ETL, estruturado passo a passo para você e seu agente na Antigravity-IDE 2.0.  
**Contexto rápido**  
Construir um classificador para 4 TB de arquivos não permite amadorismo ou "vibe coding" (codificação baseada em tentativas às cegas com IA). Este roteiro aplica o método BMAD para dividir o desenvolvimento em fases atômicas. O foco é garantir que o agente de IA construa primeiro as fundações de segurança e os motores de processamento em lote, deixando a interface visual e a manipulação física dos arquivos para o final do ciclo.

## **Passo a Passo Prático de Desenvolvimento**

### **Fase 1: Setup do Workspace e Barreiras de Qualidade (Sprint 1\)**

O objetivo aqui é preparar a Antigravity-IDE 2.0 e estabelecer as regras do jogo para o agente não produzir código inseguro.

* Abra o terminal integrado da Antigravity-IDE 2.0.  
* Inicialize o repositório Git com git init.  
* Crie a estrutura de diretórios isolando responsabilidades: motor\_python/, interface\_laravel/, banco\_dados/ e testes/.  
* Instale as extensões obrigatórias via IDE: Ruff (linting Python), Bandit (análise estática de segurança/SAST), PHP Intelephense e a extensão nativa para SQLite.  
* Acione o agente na *Manager View* e ordene a criação do arquivo .gitignore bloqueando envios de .env, diretórios virtuais (.venv) e o próprio database.sqlite.

### **Fase 2: Construção do Motor Python e Processamento Assíncrono (Sprint 2\)**

Aqui começamos o "trabalho pesado". O agente deve construir o pipeline ETL sem interface gráfica, focado apenas em não estourar a memória (OOM).

* Instrua o agente a criar o script de varredura usando os.scandir() combinado com *Generators* (yield) no Python. Nunca permita o uso de os.listdir() para listar milhares de arquivos na memória de uma vez.  
* Determine a criação de um modelo de dados estrito utilizando a biblioteca Pydantic para validar todos os caminhos de arquivos lidos antes de enviá-los ao banco.  
* Mande o agente implementar a biblioteca **FAISS** (Facebook AI Similarity Search) para a vetorização. O texto extraído do arquivo será convertido em vetor e comparado com a taxonomia corporativa na memória RAM.  
* Configure a chamada ao LLM (ex: via API do Gemini ou modelo local) apenas para gerar o *Chain of Thought* (a justificativa em texto) da decisão matemática do FAISS.

### **Fase 3: Persistência Segura e Interface de Auditoria (Sprint 3\)**

O front-end em PHP/Laravel entrará apenas para consumir os dados já processados pelo Python, atuando como o painel do auditor.

* Gere os scripts DDL em SQL (auditados pelo SQLFluff) para criar as tabelas no SQLite. A tabela principal deve ter as colunas: caminho\_origem, hash\_sha256, categoria\_sugerida, justificativa\_ia e status\_revisao.  
* Peça ao agente para estruturar o projeto Laravel dentro da pasta interface\_laravel/.  
* Crie os *Controllers* em PHP que leiam o banco de dados e enviem as listas paginadas (usando paginação estrita do Laravel) para uma *View* Blade.  
* Adicione botões na interface apenas para alterar o status\_revisao (Aprovado/Rejeitado). O Laravel não moverá arquivos neste momento.

### **Fase 4: O Executor de Movimentação (Sprint 4\)**

Este é o módulo mais perigoso e deve rodar de forma isolada, apenas após a aprovação humana no painel.

* Crie um *worker* secundário no Python que faça *polling* (consultas periódicas) no SQLite buscando registros com status Aprovado.  
* Implemente a lógica de movimentação física usando shutil.move() ou os.rename() envolta em blocos de tratamento de exceção (try/except).  
* Determine que, caso a movimentação falhe (por falta de permissão ou arquivo em uso), o sistema não deve travar, mas sim atualizar o registro no banco para ERRO\_MOVIMENTACAO.

### **Fase 5: Agentes de Teste e Limpeza Teardown (Sprint 5\)**

A qualidade contínua entra para validar o que o agente de desenvolvimento criou.

* Mude a *role* do seu agente na IDE para o perfil QA (usando o módulo Test Architect \- TEA do BMAD, se instalado).  
* Peça a criação de testes automatizados com pytest. O agente deve fazer o *mock* das funções do FAISS e do LLM para que os testes não consumam créditos reais de API nem exijam GPUs.  
* Implemente a regra de ouro do Teardown: instrua o agente a usar o módulo tempfile em todos os testes. No método de encerramento (tearDown), o script deve forçar a exclusão recursiva de todos os arquivos temporários gerados.

### **Fase 6: Empacotamento Portátil (Opcional)**

Se o software for entregue a um usuário que não seja desenvolvedor.

* Crie um arquivo .spec para o PyInstaller, configurando o empacotamento do Python e suas dependências (FAISS) em um único executável.  
* Crie um script em lote (start.bat ou PowerShell) que suba o servidor embutido do PHP (php artisan serve) e o motor Python simultaneamente em *background*.

## **Boas Práticas Profissionais**

* **Princípio da Responsabilidade Única (SOLID):** O Python lê arquivos e faz cálculos. O PHP exibe a tela. O banco de dados une os dois. Não permita que o agente crie um script monolítico que tente fazer tudo de uma vez.  
* **Gestão de Dependências:** Fixe as versões das bibliotecas (ex: faiss-cpu==1.7.4, pydantic==2.5.2) no arquivo requirements.txt para evitar que futuras atualizações quebrem o instalador gerado.  
* **Deduplicação Inteligente:** O cálculo de Hash SHA-256 no Sprint 2 deve acontecer *antes* da vetorização. Se dois arquivos têm o mesmo hash, você pula a etapa do LLM (poupando custo e tempo) e apenas vincula o arquivo duplicado à mesma classificação do original.

## **Segurança da Informação**

A blindagem deste projeto foca em proteger os dados do usuário e o sistema operacional:

* **Proteção contra Prompt Injection:** Um arquivo malicioso (ex: um PDF chamado instrucoes.pdf contendo comandos de ataque em texto) pode induzir o LLM a apagar dados se o texto não for higienizado. Toda string extraída de arquivos deve ser sanitizada (removendo tags HTML e caracteres de controle) e ter limite estrito de tamanho (ex: truncar após 2000 tokens) antes de ser enviada ao *prompt* da IA.  
* **Modelagem de Ameaças (Path Traversal):** Valide todas as strings de caminhos de arquivos. Se um arquivo tentar resolver para ../../Windows/System32, o script Pydantic deve barrar e registrar o alerta sem prosseguir.  
* **Least Privilege (Privilégio Mínimo):** O servidor web PHP nunca deve ter permissões de administrador no Windows, garantindo que uma vulnerabilidade na interface não comprometa a máquina inteira.

## **Repositórios ou Referências**

* **Bibliotecas e Frameworks:** facebookresearch/faiss no GitHub para a documentação do algoritmo de busca vetorial; laravel/framework para as melhores práticas de roteamento e paginação web.  
* **Qualidade e Segurança:** PyCQA/bandit para regras estáticas Python, aplicáveis durante os *commits*.  
* **Ecossistema BMAD:** bmad-code-org/bmad-method para acessar as instruções de *prompting* arquitetural na separação entre os agentes *Dev* e *QA*.

## **Checklist: Validação do Fim da Fase 1**

Antes de avançar para a lógica pesada, confira seu workspace:

* \[ \] A estrutura de diretórios foi criada sem arquivos desnecessários?  
* \[ \] O Bandit e o Ruff estão configurados no .vscode/settings.json ou nativo da Antigravity-IDE?  
* \[ \] O .gitignore está ativo e protegendo seus segredos (arquivos .env) de irem para o controle de versão?  
* \[ \] As regras do "Chain of Thought" (CoT) estão claras no documento de referência do agente?