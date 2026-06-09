# Especificação Técnica de Desenvolvimento - Organizador Pro

Esta documentação fornece as diretrizes matemáticas, lógicas e operacionais para a implementação do código do Organizador Pro.

---

## 1. Máquina de Status ETL (Topologia Lógica)

A tabela central no SQLite (`arquivos_processamento`) possui uma coluna `status` que atua como barramento de controle do pipeline Produtor-Consumidor. O fluxo de transição obrigatório é:

```
                  ┌──(Scan/Extract)──► [quarentena] (Física e Lógica)
                  │
[pendente_extracao] ──(Scan/Extract)──► [pendente_inferencia] ──(ML & CoT)──► [aguardando_auditoria] ──(Auditoria Laravel)──► [aprovado_para_movimentacao] ──(Move)──► [concluido]
```

### Regras de Transição de Estado
1. **Varredura (Scan):** Insere registros no estado `pendente_extracao`.
2. **Enriquecimento (Extract):**
   * Em caso de sucesso na extração de texto: altera o status para `pendente_inferencia`.
   * Em caso de falha física, arquivo corrompido, bloqueado por permissão ou criptografado: altera o status para `quarentena`, grava o erro amigável em `motivo_falha` e move o arquivo fisicamente para a pasta `_QUARENTENA_` no destino.
   * Em caso de exceção de código: altera o status para `erro` e armazena a stack trace em `mensagem_erro`.
3. **ML & Inferência (Transform):**
   * Em caso de cálculo de embeddings e geração de justificativa CoT com sucesso: altera o status para `aguardando_auditoria`.
   * Em caso de falha matemática ou indisponibilidade da API do LLM: altera para `erro`.
4. **Governança (Auditoria Laravel):**
   * O usuário aprova um ou mais registros através da UI Laravel. O Laravel altera a coluna `caminho_destino_aprovado` e define o status para `aprovado_para_movimentacao` (propagando automaticamente para duplicados).
5. **Carga (Move):**
   * O script de movimentação física executa a cópia e remoção segura (atomicidade), preservando metadados de mídias e aplicando a renomeação padrão. Se bem-sucedido, altera o status para `concluido`.
   * Se a movimentação física falhar: altera para `erro`.

---

## 2. Lógicas e Algoritmos do Motor Python (Workers)

### 2.1. Mapeamento de Hardware ID no Windows 11
Para associar de forma unívoca o acervo mapeado a um disco físico, o `ScanWorker` deve capturar o número de série lógico da partição de origem do volume Windows.
* **Algoritmo de Captura (Python):**
```python
import ctypes
import os

def obter_serial_volume(caminho_diretorio: str) -> str:
    """Retorna o número de série da partição de origem no Windows 11."""
    drive_letra = os.path.splitdrive(os.path.abspath(caminho_diretorio))[0] + "\\"
    volume_serial_number = ctypes.c_ulong()
    
    # Executa chamada nativa à Kernel32 para evitar dependências de terceiros
    sucesso = ctypes.windll.kernel32.GetVolumeInformationW(
        ctypes.c_wchar_p(drive_letra),
        None, 0,
        ctypes.byref(volume_serial_number),
        None, None, None, 0
    )
    if sucesso:
        return f"{drive_letra.replace(':', '')}_{volume_serial_number.value:X}"
    else:
        # Fallback para partição via UUID
        import subprocess
        try:
            cmd = f'wmic logicaldisk where DeviceID="{drive_letra.strip(chr(92))}" get VolumeSerialNumber'
            output = subprocess.check_output(cmd, shell=True).decode().split()
            if len(output) >= 2:
                return f"{drive_letra.replace(':', '')}_{output[1]}"
        except Exception:
            pass
        return "HARDWARE_DESCONHECIDO"
```

### 2.2. Verificação Preventiva de Segurança de Caminhos
Antes de iniciar qualquer varredura ou escrita física, o script deve validar as strings de diretórios contra a lista negra de pastas do SO.
* **Lógica de Segurança:**
```python
import os

CAMINHOS_PROIBIDOS = [
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\ProgramData",
]

def validar_caminho_seguro(caminho: str):
    caminho_abs = os.path.abspath(caminho).lower()
    
    # Bloqueio de raiz do sistema
    if caminho_abs in ["c:\\", "c:"]:
        raise PermissionError("Acesso à raiz C:\\ é estritamente proibido.")
        
    # Bloqueio de subpastas do sistema
    for pasta in CAMINHOS_PROIBIDOS:
        if caminho_abs.startswith(pasta.lower()):
            raise PermissionError(f"Acesso à pasta protegida do SO {pasta} é proibido.")
            
    # Bloqueio de AppData
    if "appdata" in caminho_abs.split(os.path.sep):
        raise PermissionError("Acesso à pasta AppData é proibido.")
```

### 2.3. Algoritmo de Higienização de Strings e Renomeação Padrão
Todo arquivo elegível será renomeado na movimentação para: `[YYYYMMDD]_[antigo_nome_snake_case].[ext]`.
* **Lógica de Sanitização e Prefixo:**
```python
import re
import unicodedata
from datetime import datetime

def sanitizar_nome_arquivo(nome_base: str) -> str:
    # Remove acentos
    nfkd = unicodedata.normalize('NFKD', nome_base)
    nome_sem_acentos = "".join([c for c in nfkd if not unicodedata.combining(c)])
    # Substitui espaços e caracteres especiais por underscore, mantendo letras e números
    nome_limpo = re.sub(r'[^a-zA-Z0-9_\-]', '_', nome_sem_acentos)
    # Converte para snake_case limpo
    nome_snake = re.sub(r'_+', '_', nome_limpo).strip('_').lower()
    return nome_snake

def gerar_nome_final(nome_arquivo_original: str, data_criacao: datetime) -> str:
    # Separa nome e extensão
    nome_base, ext = os.path.splitext(nome_arquivo_original)
    ext = ext.lower()
    
    # Verifica se já possui prefixo YYYYMMDD no início (ex: "20231015_")
    possui_data = re.match(r'^\d{8}_', nome_base)
    
    nome_sanitizado = sanitizar_nome_arquivo(nome_base)
    
    if possui_data:
        return f"{nome_sanitizado}{ext}"
    else:
        prefixo_data = data_criacao.strftime("%Y%m%d")
        return f"{prefixo_data}_{nome_sanitizado}{ext}"
```

### 2.4. Resolução de Homônimos no Destino
Se houver colisão física no diretório final de destino, o worker incrementará um sufixo numérico de versão de `_v01` a `_v99`.
* **Pseudocódigo de Resolução:**
```python
def resolver_caminho_homonimo(caminho_destino_proposto: str) -> str:
    if not os.path.exists(caminho_destino_proposto):
        return caminho_destino_proposto
        
    pasta, arquivo = os.path.split(caminho_destino_proposto)
    nome_base, ext = os.path.splitext(arquivo)
    
    # Tenta encontrar uma versão vaga de v01 a v99
    for versao in range(1, 100):
        novo_nome = f"{nome_base}_v{versao:02d}{ext}"
        caminho_teste = os.path.join(pasta, novo_nome)
        if not os.path.exists(caminho_teste):
            return caminho_teste
            
    # Fallback caso todas as 99 versões estejam ocupadas (adiciona timestamp)
    timestamp = datetime.now().strftime("%H%M%S")
    return os.path.join(pasta, f"{nome_base}_v99_{timestamp}{ext}")
```

### 2.5. Injeção Física de Metadados CoT em Arquivos Abertos
Escrever o texto de justificativa CoT diretamente nos metadados estendidos para evitar a perda da rastreabilidade semântica.
* **Lógica de Injeção em PDFs (usando PyMuPDF/fitz):**
```python
import fitz

def injetar_cot_pdf(caminho_pdf: str, justificativa_cot: str):
    try:
        doc = fitz.open(caminho_pdf)
        metadata = doc.metadata
        # Injeta a justificativa na propriedade "subject" ou metadado customizado
        metadata["subject"] = justificativa_cot
        metadata["keywords"] = "Organizador Pro ETL; Classificação Automática"
        doc.set_metadata(metadata)
        # Salva as alterações in-place de forma incremental
        doc.save(doc.name, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()
    except Exception as e:
        # Falha de injeção não deve corromper o arquivo; registrar apenas log
        print(f"Erro ao injetar metadados no PDF: {e}")
```
* **Lógica de Injeção em DOCXs (usando python-docx):**
```python
from docx import Document

def injetar_cot_docx(caminho_docx: str, justificativa_cot: str):
    try:
        doc = Document(caminho_docx)
        propriedades = doc.core_properties
        # Injeta a justificativa na propriedade de comentário/assunto do Word
        propriedades.comments = justificativa_cot
        propriedades.subject = "Classificação Organizador Pro"
        doc.save(caminho_docx)
    except Exception as e:
        print(f"Erro ao injetar metadados no DOCX: {e}")
```

---

## 3. Motor de Inferência (Matemática e Algoritmos)

A categorização inteligente do Organizador Pro compara o vetor do documento $\mathbf{A}$ contra o vetor da categoria candidato $\mathbf{B}$ via similaridade de cosseno:

$$\text{similaridade} = \cos(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$$

* **Modelo Utilizado:** `paraphrase-multilingual-MiniLM-L12-v2` (Sentence Transformers) rodando em CPU/GPU.
* **Roteamento em Cascata:**
  1. **Passo 1 (Macro):** Calcula similaridade contra os vetores que descrevem as funções primárias da metodologia P.A.R.A. (Projects, Areas, Resources, Archives). Se classificado, por exemplo, como `Resources`, o escopo é isolado.
  2. **Passo 2 (Micro):** Calcula a similaridade do vetor do arquivo *apenas* contra as subpastas cadastradas hierarquicamente subordinadas a `Resources` (ex: `apostilas`, `manuais`).

---

## 4. Integração do Prompt CoT e Blindagem

### Higienização contra Prompt Injection (Ataque Indireto)
1. **Remoção de Delimitadores Críticos:** Substituir todas as ocorrências de aspas triplas (`"""`), crases triplas (`` ` ` ` ``) e divisores de seção (`---`, `===`) por hífens.
2. **Escapamento:** Filtrar tags HTML/XML e caracteres não-ASCII de controle.
3. **Truncamento:** Cortar estritamente o texto nos primeiros 2000 tokens.

### Template de Prompt
```
Você é o assistente de governança do Organizador Pro.
Com base nas diretrizes do Plano de Classificação de Documentos (PCD), justifique em exatamente 50 palavras por que o documento com o seguinte trecho textual:
---
[INÍCIO DO DOCUMENTO HIGIENIZADO]
{TEXTO_EXTRAIDO_LIMITADO}
[FIM DO DOCUMENTO HIGIENIZADO]
---
pertence à categoria recomendada: "{CATEGORIA_SUGERIDA}".
Escreva a justificativa em Português do Brasil, de forma clara, técnica e focada estritamente no conteúdo semântico.
```

---

## 5. Configuração do Arquivo `.env` Unificado

O arquivo `.env` reside na raiz do projeto (`/app_organizadora/.env`) e parametriza o motor Python e o Laravel:

```env
# Configurações do Banco de Dados SQLite
DB_CONNECTION=sqlite
DB_DATABASE=banco_dados/database.sqlite
DB_TIMEOUT=30.0

# Caminhos de Varredura e Destino Físico
SCAN_PATH="C:/Users/Exemplo/Origem"
DESTINATION_PATH="C:/Users/Exemplo/Destino"

# Motor de ML & LLM
LLM_PROVIDER=gemini            # Opções: gemini, local
GEMINI_API_KEY="AIzaSy..."     # Necessário se LLM_PROVIDER=gemini
LOCAL_MODEL_PATH="motor_python/models/model.gguf" # Necessário se LLM_PROVIDER=local

# Orquestração da Interface Laravel
PORT=8000
APP_ENV=local
APP_KEY=base64:XyZ...
APP_DEBUG=true
APP_URL=http://localhost:8000
```

---

## 6. Diretrizes de Desenvolvimento da UI / Laravel BFF

* **Laravel como BFF:** O backend Laravel atuará exclusivamente como um *Backend For Frontend* (BFF), consumindo os dados consolidados no banco de dados SQLite comum e interagindo indiretamente com as etapas do pipeline ETL gerenciadas pelo motor Python.
* **Timeout do SQLite no Laravel:** Para mitigar erros de `database is locked` decorrentes de gravação paralela dos workers Python, a conexão SQLite do Laravel (`config/database.php`) deve ser configurada estritamente com a opção de timeout do PDO:
  ```php
  'sqlite' => [
      'driver' => 'sqlite',
      'database' => env('DB_DATABASE', database_path('database.sqlite')),
      'prefix' => '',
      'foreign_key_constraints' => env('DB_FOREIGN_KEYS', true),
      'options' => [
          PDO::ATTR_TIMEOUT => 30, // Timeout de 30 segundos
      ],
  ],
  ```
* **Componentização de Dados (FilamentPHP / Livewire):**
  * **Widget de Progresso em Tempo Real:** Criar um widget no Dashboard principal (`Filament/Widgets`) com polling dinâmico a cada 5 segundos utilizando o recurso nativo de Livewire (`wire:poll.5s`). O widget deve consultar a tabela `arquivos_processamento` e realizar a contagem agregada de registros por status para exibir uma barra de progresso do pipeline de processamento.
  * **Agrupamento e Controle de Duplicados (Drawer/Modal):** As tabelas do FilamentPHP devem filtrar a listagem principal para exibir apenas registros com `eh_duplicado = 0`. Um badge ou coluna interativa exibirá a contagem de duplicatas. Ao ser clicado, abrirá um Filament Drawer ou Modal que listará as duplicatas (mesmo `hash_sha256`), fornecendo botões para:
    * *Propagar Destino:* Salvar o mesmo caminho aprovado do original.
    * *Exclusão Física:* Marcar as duplicatas para deleção na movimentação final pelo worker Python.
  * **Aba de Gestão de Quarentena:** Página customizada no painel administrativo listando registros sob o status `quarentena`. Deve exibir o caminho de origem do arquivo e o `motivo_falha` gravado no banco de dados. A listagem fornecerá ações para forçar o reprocessamento (mudando o status para `pendente_extracao`) ou descarte físico do arquivo.
* **Treemap de Heatmap Premium (ApexCharts):** A visualização de densidade de arquivos e tamanho total por categorias P.A.R.A. / PCD deve utilizar o componente ApexCharts integrado de forma segura ao Filament:
  * O gráfico do tipo Treemap deve representar o tamanho somado dos arquivos em bytes por categoria.
  * Para respeitar as políticas de Content Security Policy (CSP), os dados para renderização do gráfico devem ser passados como objeto JSON estruturado para o frontend, proibindo a execução de strings inline via `eval` ou geração dinâmica de scripts no DOM.
* **Segurança e XSS:**
  * Sempre utilize a sintaxe de escape automático do Blade (`{{ $resultado }}`) para renderizar logs, caminhos e justificativas do ETL. O uso de `{!! $resultado !!}` é estritamente proibido, a menos que os dados tenham passado por um sanitizador de HTML rigoroso no backend.
  * Configurar cabeçalhos HTTP de CSP estritos no Laravel para prevenir injeção de scripts no DOM manipulado.
  * Tratar todas as saídas geradas por IA como dados não confiáveis no frontend.

