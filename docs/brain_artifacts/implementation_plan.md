# Plano de Implementação - Aperfeiçoamento Estético e Funcional do Organizador Pro

Este documento descreve as etapas técnicas e de design para implementar melhorias no painel web, segurança na organização física, logo animado, execução silenciosa dos serviços e encerramento automatizado.

---

## User Review Required

> [!IMPORTANT]
> A implementação do **Seletor de Diretórios Local** usará um componente customizado que navega pelo sistema de arquivos do servidor. Como o navegador de internet por motivos de segurança padrão impede que o input `<input type="file">` retorne o caminho absoluto das pastas físicas do sistema operacional, nossa solução em Livewire/PHP criará um navegador nativo embutido no modal, permitindo que o usuário selecione qualquer pasta no disco local de forma 100% amigável.

> [!WARNING]
> Quando a **pasta de origem for idêntica à de destino**, a aplicação redefinirá automaticamente o destino de gravação dos arquivos organizados para uma subpasta chamada `Organizado/` dentro do próprio diretório para evitar a colisão de nomes e loops de catalogação infinita. O Scanner de inventário do motor Python será atualizado para ignorar esta pasta.

---

## Proposed Changes

### 1. Interface e Estética Visual (Filament Theme Override)

#### [NEW] [custom_theme.css](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/public/css/custom_theme.css)
Criação de folha de estilo injetada no Filament para customizar a interface com as seguintes definições visuais:
- **Tema Marinho e Celeste:** Gradientes sutis utilizando tons de azul escuro profundo para a barra lateral, combinados com ciano/celeste para os itens ativos e destaque secundário.
- **Tons Solares de Destaque:** Uso de cores laranja quente e dourado para botões de ação críticos, alertas e badges de status.
- **Transparências e Vidro:** Efeito de desfoque (`backdrop-filter: blur(8px)`) no cabeçalho e na sidebar quando em modo flutuante.
- **Marca Minimalista Animada:** Injeção de marca animada via SVG/CSS no menu lateral do painel.

#### [NEW] [brand-logo.blade.php](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/resources/views/filament/components/brand-logo.blade.php)
Desenho de uma marca/logo minimalista moderna em formato SVG nativo com animações discretas de pulsação e transição de cores (do ciano ao solar).

#### [MODIFY] [AdminPanelProvider.php](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/app/Providers/Filament/AdminPanelProvider.php)
- Registro da folha de estilo `custom_theme.css`.
- Configuração do logo dinâmico utilizando a view `brand-logo`.

---

### 2. Controle de Diretório Local (Folder Picker)

#### [NEW] [FolderPicker.php](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/app/Livewire/FolderPicker.php)
Componente Livewire auxiliar que exibe um modal de seleção de pastas. Ele permite:
- Listar diretórios da máquina local do usuário a partir de unidades de disco (C:, D:, etc.) ou da pasta HOME do usuário.
- Navegar recursivamente para cima e para baixo nas pastas.
- Criar pastas novas diretamente pelo modal.
- Retornar o caminho absoluto completo da pasta selecionada para o campo de texto correspondente no Filament.

#### [NEW] [folder-picker.blade.php](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/resources/views/livewire/folder-picker.blade.php)
Visual do seletor de pastas em Tailwind CSS nativo do Filament, exibindo a árvore de pastas de forma amigável com ícones de diretórios.

#### [MODIFY] [Configuracoes.php](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/app/Filament/Pages/Configuracoes.php)
Integração do componente `FolderPicker` nos campos de input de origem e de destino para que o usuário possa digitar ou selecionar usando o navegador de pastas local.

---

### 3. Prevenção de Loops (Origem Igual ao Destino)

#### [MODIFY] [inventario.py](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/motor_python/inventario.py)
Ajuste da classe `Scanner` para ignorar pastas de destino configuradas que estejam contidas no caminho de origem.
- Adiciona detecção automática da pasta de destino no scanner.
- Pula a leitura de diretórios com nome `Organizado` ou que correspondam ao `destination_path` para evitar loops infinitos.

#### [MODIFY] [movement_worker.py](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/motor_python/movement_worker.py)
Ajuste no roteador físico de movimentação. Se a pasta de destino configurada for igual à de origem, move os arquivos de forma isolada para a subpasta `Organizado` dentro da própria origem.

---

### 4. Inicialização Silenciosa e Abertura Automática

#### [MODIFY] [start.bat](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/start.bat)
Atualização do script orquestrador:
- Executa a configuração inicial de ambiente.
- Inicia o servidor PHP e o loop do motor Python em background **oculto** de verdade via PowerShell (`Start-Process -WindowStyle Hidden`).
- Abre automaticamente a interface do painel no navegador padrão utilizando o comando `start http://127.0.0.1:8000`.

---

### 5. Botão de Encerramento Completo da Aplicação

#### [NEW] [DesligarAction.php](file:///C:/Users/Marcelo%20Maymone/Documents/antigravity_projetos/organizador_pro/interface_laravel/app/Filament/Actions/DesligarAction.php)
Ação integrada ao cabeçalho ou barra de navegação que:
- Dispara uma notificação avisando o encerramento.
- Retorna um script JavaScript ao navegador que executa `window.close()` para fechar a aba ativa.
- Dispara um script assíncrono no servidor que faz a limpeza dos caches do Laravel (`config:clear`, `cache:clear`).
- Executa comandos `taskkill` no Windows para matar todos os processos de background ativos do `php.exe` e `motor_organizador.exe` associados à aplicação de forma definitiva.

---

## Verification Plan

### Automated Tests
- Execução de testes de rotas do Laravel para verificar se os assets e as páginas customizadas respondem com HTTP 200.
- Execução de testes de unidade do motor Python (`run_tests.bat`).

### Manual Verification
1. Executar o `start.bat` modificado no Desktop e verificar se:
   - Os terminais rodam ocultos sem janelas pretas piscando.
   - O browser abre o painel automaticamente.
2. Navegar para a aba "Configurações":
   - Clicar nos seletores de diretório e verificar a navegação local.
   - Definir a pasta de origem e destino idênticas.
   - Disparar o escaneamento e checar se os arquivos organizados são movidos para o subdiretório `Organizado` sem gerar loops de re-escaneamento.
3. Testar a funcionalidade de "Encerrar Aplicação" no painel Filament e garantir que os processos PHP e do motor em background foram fechados.
