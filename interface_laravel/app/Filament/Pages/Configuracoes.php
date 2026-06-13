<?php

namespace App\Filament\Pages;

use Filament\Pages\Page;
use Filament\Forms\Form;
use Filament\Forms\Components\TextInput;
use Filament\Forms\Components\Section;
use Filament\Forms\Components\Select;
use Filament\Notifications\Notification;
use Filament\Forms\Concerns\InteractsWithForms;
use Filament\Forms\Contracts\HasForms;

/**
 * Organizador Pro - Página de Configurações do Painel
 * 
 * DECISÃO ARQUITETURAL:
 * Esta página permite gerenciar visualmente os diretórios de processamento (origem e destino)
 * e chaves de API sem exigir que o usuário final edite arquivos de configuração (.env) manualmente.
 * As alterações são gravadas diretamente nos arquivos .env da aplicação e do motor Python
 * para garantir que ambos trabalhem com o mesmo contexto e banco de dados SQLite.
 * Também oferece um gatilho para iniciar a Varredura (Fase 1) em background via PHP.
 */
class Configuracoes extends Page implements HasForms
{
    use InteractsWithForms;

    protected static ?string $navigationIcon = 'heroicon-o-cog-6-tooth';

    protected static string $view = 'filament.pages.configuracoes';

    protected static ?string $navigationLabel = 'Configurações';
    protected static ?string $title = 'Configurações do Sistema';
    protected static ?string $slug = 'configuracoes';

    // Variáveis para o Folder Picker (Navegador de Diretórios Local)
    public bool $seletorAberto = false;
    public string $seletorCampo = ''; // 'scan_path' ou 'destination_path'
    public string $seletorCaminhoAtual = '';
    public array $seletorDiretorios = [];
    public string $novaPastaNome = '';

    // Propriedades do formulário que representam as chaves no .env
    public ?string $scan_path = '';
    public ?string $destination_path = '';
    public ?string $gemini_api_key = '';
    public ?string $embedding_provider = 'local';
    public ?string $llm_provider = 'gemini';

    public function mount(): void
    {
        // Lê os valores atuais das variáveis de ambiente para preencher o formulário.
        // Preferencialmente lê direto do arquivo .env para evitar chaves desatualizadas em cache.
        $envData = $this->lerEnv();

        $this->scan_path = $envData['SCAN_PATH'] ?? env('SCAN_PATH', '');
        $this->destination_path = $envData['DESTINATION_PATH'] ?? env('DESTINATION_PATH', '');
        $this->gemini_api_key = $envData['GEMINI_API_KEY'] ?? env('GEMINI_API_KEY', '');
        $this->embedding_provider = $envData['EMBEDDING_PROVIDER'] ?? env('EMBEDDING_PROVIDER', 'local');
        $this->llm_provider = $envData['LLM_PROVIDER'] ?? env('LLM_PROVIDER', 'gemini');
    }

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Section::make('Diretórios de Processamento')
                    ->description('Defina as pastas utilizadas pelo motor ETL do Organizador Pro.')
                    ->schema([
                        TextInput::make('scan_path')
                            ->label('Diretório de Origem (Varredura)')
                            ->placeholder('Ex: C:/meus_arquivos')
                            ->helperText('Pasta onde estão os arquivos originais que você deseja catalogar e organizar.')
                            ->required()
                            ->suffixAction(
                                \Filament\Forms\Components\Actions\Action::make('abrirSeletorOrigem')
                                    ->icon('heroicon-m-folder-open')
                                    ->color('primary')
                                    ->label('Escolher Pasta')
                                    ->action(fn ($livewire) => $livewire->abrirSeletor('scan_path'))
                            ),

                        TextInput::make('destination_path')
                            ->label('Diretório de Destino (Organizado)')
                            ->placeholder('Ex: C:/arquivos_organizados')
                            ->helperText('Pasta para onde os arquivos classificados e aprovados serão movidos.')
                            ->required()
                            ->suffixAction(
                                \Filament\Forms\Components\Actions\Action::make('abrirSeletorDestino')
                                    ->icon('heroicon-m-folder-open')
                                    ->color('primary')
                                    ->label('Escolher Pasta')
                                    ->action(fn ($livewire) => $livewire->abrirSeletor('destination_path'))
                            ),
                    ])->columns(1),

                Section::make('Integração com Inteligência Artificial')
                    ->description('Configuração do motor de classificação e provedores de IA.')
                    ->schema([
                        Select::make('embedding_provider')
                            ->label('Provedor de Embeddings')
                            ->options([
                                'local' => 'Local (Sem custos)',
                                'gemini' => 'Google Gemini API',
                            ])
                            ->required(),

                        Select::make('llm_provider')
                            ->label('Provedor de LLM (Classificação)')
                            ->options([
                                'gemini' => 'Google Gemini (Recomendado)',
                                'mock' => 'Mock (Apenas testes, não consome API)',
                            ])
                            ->required(),

                        TextInput::make('gemini_api_key')
                            ->label('Chave da API do Google Gemini')
                            ->password()
                            ->placeholder('Insira sua chave de API do Gemini...')
                            ->helperText('Necessário para inferências de IA se Gemini estiver selecionado.')
                            ->nullable(),
                    ])->columns(1),
            ]);
    }

    /**
     * Salva as configurações de volta nos arquivos .env (Laravel e Motor)
     */
    public function save(): void
    {
        $data = $this->form->getState();
        $scan = trim($data['scan_path']);
        $dest = trim($data['destination_path']);

        $caminhosEnv = [
            // .env do Laravel
            base_path('.env'),
            // .env da raiz do pacote (um nível acima de interface_laravel)
            dirname(base_path()) . DIRECTORY_SEPARATOR . '.env',
            // .env de compatibilidade do motor compilado
            dirname(base_path()) . DIRECTORY_SEPARATOR . 'dist' . DIRECTORY_SEPARATOR . 'motor_organizador' . DIRECTORY_SEPARATOR . '.env'
        ];

        foreach ($caminhosEnv as $envPath) {
            if (file_exists($envPath)) {
                $this->atualizarEnv($envPath, [
                    'SCAN_PATH' => $scan,
                    'DESTINATION_PATH' => $dest,
                    'GEMINI_API_KEY' => $data['gemini_api_key'] ?? '',
                    'EMBEDDING_PROVIDER' => $data['embedding_provider'],
                    'LLM_PROVIDER' => $data['llm_provider'],
                ]);
            }
        }

        if (strcasecmp(str_replace('\\', '/', $scan), str_replace('\\', '/', $dest)) === 0) {
            Notification::make()
                ->title('Aviso: Pastas Idênticas')
                ->body("A pasta de destino é igual à de origem. O Organizador Pro salvará os arquivos estruturados na subpasta '/Organizado' dentro dela para evitar loops infinitos de processamento.")
                ->warning()
                ->persistent()
                ->send();
        } else {
            Notification::make()
                ->title('Configurações Salvas')
                ->body('As pastas de origem/destino e chaves de IA foram atualizadas em todos os motores.')
                ->success()
                ->send();
        }
    }

    /**
     * Abre o modal de seleção de pasta para o campo especificado
     */
    public function abrirSeletor(string $campo): void
    {
        $this->seletorCampo = $campo;
        
        // Inicia no valor atual do campo se for um diretório existente, senão no HOME do usuário
        $caminhoInicial = $this->{$campo} ?? '';
        if (empty($caminhoInicial) || !is_dir($caminhoInicial)) {
            $caminhoInicial = getenv('USERPROFILE') ?: base_path();
        }
        
        $this->atualizarDiretorioNavegacao($caminhoInicial);
        $this->seletorAberto = true;
    }

    /**
     * Atualiza a navegação para o diretório indicado e carrega suas subpastas
     */
    public function atualizarDiretorioNavegacao(string $caminho): void
    {
        $caminho = str_replace('/', DIRECTORY_SEPARATOR, $caminho);
        $caminhoReal = realpath($caminho);
        
        // Se o realpath falhar (ex: partição inacessível ou vazia), usa o caminho original
        $this->seletorCaminhoAtual = $caminhoReal ?: $caminho;
        $this->seletorDiretorios = [];

        if (is_dir($this->seletorCaminhoAtual)) {
            try {
                $files = scandir($this->seletorCaminhoAtual);
                if ($files !== false) {
                    foreach ($files as $file) {
                        if ($file === '.' || $file === '..') {
                            continue;
                        }
                        
                        $completo = $this->seletorCaminhoAtual . DIRECTORY_SEPARATOR . $file;
                        if (is_dir($completo)) {
                            // Ignora pastas ocultas ou do sistema para manter a lista limpa
                            if (strpos($file, '$') !== 0 && $file !== 'System Volume Information') {
                                $this->seletorDiretorios[] = $file;
                            }
                        }
                    }
                }
                sort($this->seletorDiretorios);
            } catch (\Exception $e) {
                // Silencia erros de acesso a pastas protegidas
            }
        }
    }

    /**
     * Entra em uma subpasta na navegação atual
     */
    public function entrarNaPasta(string $nomePasta): void
    {
        // Garante que não use contrabarra duplicada no final de letras de unidade (ex: C:\)
        $separador = (substr($this->seletorCaminhoAtual, -1) === DIRECTORY_SEPARATOR) ? '' : DIRECTORY_SEPARATOR;
        $novoCaminho = $this->seletorCaminhoAtual . $separador . $nomePasta;
        $this->atualizarDiretorioNavegacao($novoCaminho);
    }

    /**
     * Sobe um nível na árvore de diretórios (diretório pai)
     */
    public function subirDiretorio(): void
    {
        $pai = dirname($this->seletorCaminhoAtual);
        
        // Evita loop se já estiver na raiz do drive no Windows
        if ($pai !== $this->seletorCaminhoAtual) {
            $this->atualizarDiretorioNavegacao($pai);
        }
    }

    /**
     * Cria uma nova pasta física no diretório de navegação atual
     */
    public function criarNovaPasta(): void
    {
        $nome = trim($this->novaPastaNome);
        if (empty($nome)) {
            return;
        }

        $separador = (substr($this->seletorCaminhoAtual, -1) === DIRECTORY_SEPARATOR) ? '' : DIRECTORY_SEPARATOR;
        $caminhoNovaPasta = $this->seletorCaminhoAtual . $separador . $nome;
        
        if (!file_exists($caminhoNovaPasta)) {
            try {
                mkdir($caminhoNovaPasta, 0777, true);
                $this->novaPastaNome = '';
                $this->atualizarDiretorioNavegacao($this->seletorCaminhoAtual);
                
                Notification::make()
                    ->title('Pasta Criada')
                    ->body("A pasta '{$nome}' foi criada com sucesso.")
                    ->success()
                    ->send();
            } catch (\Exception $e) {
                Notification::make()
                    ->title('Erro ao Criar Pasta')
                    ->body($e->getMessage())
                    ->danger()
                    ->send();
            }
        } else {
            Notification::make()
                ->title('Pasta já existe')
                ->body("A pasta '{$nome}' já existe no diretório atual.")
                ->warning()
                ->send();
        }
    }

    /**
     * Confirma a seleção do diretório atual e preenche o formulário do Filament
     */
    public function confirmarSelecao(): void
    {
        $caminhoFinal = str_replace('\\', '/', $this->seletorCaminhoAtual);
        
        if ($this->seletorCampo === 'scan_path') {
            $this->scan_path = $caminhoFinal;
        } elseif ($this->seletorCampo === 'destination_path') {
            $this->destination_path = $caminhoFinal;
        }

        // Atualiza os dados no formulário do Filament
        $this->form->fill([
            'scan_path' => $this->scan_path,
            'destination_path' => $this->destination_path,
            'gemini_api_key' => $this->gemini_api_key,
            'embedding_provider' => $this->embedding_provider,
            'llm_provider' => $this->llm_provider,
        ]);

        $this->seletorAberto = false;
        
        Notification::make()
            ->title('Diretório Selecionado')
            ->body("Pasta definida: {$caminhoFinal}")
            ->success()
            ->send();
    }

    /**
     * Dispara a varredura física (Fase 1) em background utilizando os caminhos configurados.
     */
    public function iniciarVarredura(): void
    {
        $this->save(); // Garante que as pastas salvas são as que serão processadas

        $raizDir = dirname(base_path());
        
        // Executa o motor portátil passando o comando de escaneamento (--scan) com o diretório configurado
        $motorExe = $raizDir . DIRECTORY_SEPARATOR . 'dist' . DIRECTORY_SEPARATOR . 'motor_organizador' . DIRECTORY_SEPARATOR . 'motor_organizador.exe';
        
        if (!file_exists($motorExe)) {
            // Fallback para ambiente de desenvolvimento (executa o main.py usando o venv)
            $venvPython = $raizDir . DIRECTORY_SEPARATOR . 'motor_python' . DIRECTORY_SEPARATOR . '.venv' . DIRECTORY_SEPARATOR . 'Scripts' . DIRECTORY_SEPARATOR . 'python.exe';
            $mainScript = $raizDir . DIRECTORY_SEPARATOR . 'motor_python' . DIRECTORY_SEPARATOR . 'main.py';
            
            if (file_exists($venvPython)) {
                $cmd = '"' . $venvPython . '" "' . $mainScript . '" --scan "' . $this->scan_path . '"';
            } else {
                $cmd = 'python "' . $mainScript . '" --scan "' . $this->scan_path . '"';
            }
        } else {
            $cmd = '"' . $motorExe . '" --scan "' . $this->scan_path . '"';
        }

        // Executa o processo de forma assíncrona/background no Windows para não travar a UI do Laravel
        if (substr(php_uname(), 0, 7) == "Windows") {
            pclose(popen("start /B cmd /c " . $cmd, "r"));
        } else {
            exec($cmd . " > /dev/null &");
        }

        Notification::make()
            ->title('Varredura Iniciada')
            ->body('O motor do Organizador Pro começou a escanear a pasta de origem em background.')
            ->info()
            ->send();
    }

    /**
     * Auxiliar para ler chaves diretamente do arquivo .env
     */
    private function lerEnv(): array
    {
        $envPath = base_path('.env');
        if (!file_exists($envPath)) {
            return [];
        }

        $data = [];
        $lines = file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        foreach ($lines as $line) {
            if (strpos(trim($line), '#') === 0) continue;
            if (strpos($line, '=') !== false) {
                list($key, $value) = explode('=', $line, 2);
                $data[trim($key)] = trim($value, " \t\n\r\0\x0B\"'");
            }
        }
        return $data;
    }

    /**
     * Auxiliar para escrever/atualizar chaves no arquivo .env preservando comentários e formatação
     */
    private function atualizarEnv(string $path, array $valores): void
    {
        $content = file_get_contents($path);

        foreach ($valores as $key => $value) {
            // Normaliza as barras para forward-slash para evitar problemas de escape no parser dotenv do Laravel
            // No caso das variáveis do motor, o Python também processa normalmente o forward-slash.
            $value = str_replace('\\', '/', $value);
            
            // Coloca aspas em todos os valores para tratar caminhos ou chaves que contenham espaços.
            $value = '"' . $value . '"';

            if (preg_match("/^{$key}=.*/m", $content)) {
                $content = preg_replace("/^{$key}=.*/m", "{$key}={$value}", $content);
            } else {
                $content .= "\n{$key}={$value}";
            }
        }

        file_put_contents($path, $content);
    }
}
